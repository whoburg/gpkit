"Implements KeyDict and KeySet classes"

from collections import defaultdict
from collections.abc import Hashable

import numpy as np

from .small_classes import FixedScalar, Numbers, Quantity
from .small_scripts import is_sweepvar, isnan, veclinkedfn

DIMLESS_QUANTITY = Quantity(1, "dimensionless")
INT_DTYPE = np.dtype(int)


def clean_value(key, value):
    """Gets the value of variable-less monomials, so that
    `x.sub({x: gpkit.units.m})` and `x.sub({x: gpkit.ureg.m})` are equivalent.

    Also converts any quantities to the key's units, because quantities
    can't/shouldn't be stored as elements of numpy arrays.
    """
    if isinstance(value, FixedScalar):
        value = value.value
    if isinstance(value, Quantity):
        value = value.to(key.units or "dimensionless").magnitude
    return value


class KeyMap:
    """Helper class to provide KeyMapping to interfaces.

    Mapping keys
    ------------
    A KeyMap keeps an internal list of VarKeys as
    canonical keys, and their values can be accessed with any object whose
    `key` attribute matches one of those VarKeys, or with strings matching
    any of the multiple possible string interpretations of each key:

    For example, after creating the KeyDict kd and setting kd[x] = v (where x
    is a Variable or VarKey), v can be accessed with by the following keys:
     - x
     - x.key
     - x.name (a string)
     - "x_modelname" (x's name including modelname)

    Note that if a item is set using a key that does not have a `.key`
    attribute, that key can be set and accessed normally.
    """

    collapse_arrays = False
    keymap = []
    log_gets = False
    vks = varkeys = None

    def __init__(self, *args, **kwargs):
        "Passes through to super().__init__ via the `update()` method"
        self.keymap = defaultdict(set)
        self._unmapped_keys = set()
        self.owned = set()
        self.update(*args, **kwargs)  # pylint: disable=no-member

    def parse_and_index(self, key):
        "Returns key if key had one, and veckey/idx for indexed veckeys."
        try:
            key = key.key
            if self.collapse_arrays and key.idx:
                return key.veckey, key.idx
            return key, None
        except AttributeError:
            if self.vks is None and self.varkeys is None:
                return key, self.update_keymap()
        # looks like we're in a substitutions dictionary
        if self.varkeys is None:
            self.varkeys = KeySet(self.vks)
        if key not in self.varkeys:
            raise KeyError(key)
        newkey, *otherkeys = self.varkeys[key]
        if otherkeys:
            if all(k.veckey == newkey.veckey for k in otherkeys):
                return newkey.veckey, None
            raise ValueError(
                f"{key} refers to multiple keys in this "
                "substitutions KeyDict. Use "
                f"`.variables_byname({key})` to see all of them."
            )
        if self.collapse_arrays and newkey.idx:
            return newkey.veckey, newkey.idx
        return newkey, None

    def __contains__(self, key):
        "In a winding way, figures out if a key is in the KeyDict"
        # pylint: disable=no-member
        try:
            key, idx = self.parse_and_index(key)
        except KeyError:
            return False
        except ValueError:  # multiple keys correspond
            return True
        if not isinstance(key, Hashable):
            return False
        if super().__contains__(key):
            if idx:
                try:
                    val = super().__getitem__(key)[idx]
                    return True if is_sweepvar(val) else not isnan(val).any()
                except TypeError as err:
                    val = super().__getitem__(key)
                    raise TypeError(
                        f"{key} has an idx, but its value in this"
                        " KeyDict is the scalar {val}."
                    ) from err
                except IndexError as err:
                    val = super().__getitem__(key)
                    raise IndexError(
                        f"key {key} with idx {idx} is out of " " bounds for value {val}"
                    ) from err
        return key in self.keymap

    def update_keymap(self):
        "Updates the keymap with the keys in _unmapped_keys"
        copied = set()  # have to copy bc update leaves duplicate sets
        for key in self._unmapped_keys:
            for mapkey in key.keys:
                if mapkey not in copied and mapkey in self.keymap:
                    self.keymap[mapkey] = set(self.keymap[mapkey])
                    copied.add(mapkey)
                self.keymap[mapkey].add(key)
        self._unmapped_keys = set()


class KeyDict(KeyMap, dict):
    """KeyDicts do two things over a dict: map keys and collapse arrays.

    >>>> kd = gpkit.keydict.KeyDict()

    For mapping keys, see KeyMapper.__doc__

    Collapsing arrays
    -----------------
    If ``.collapse_arrays`` is True then VarKeys which have a `shape`
    parameter (indicating they are part of an array) are stored as numpy
    arrays, and automatically de-indexed when a matching VarKey with a
    particular `idx` parameter is used as a key.

    See also: gpkit/tests/t_keydict.py.
    """

    collapse_arrays = True

    def get(self, key, *alternative):
        return alternative[0] if alternative and key not in self else self[key]

    def _copyonwrite(self, key):
        "Copys arrays before they are written to"
        if not hasattr(self, "owned"):  # backwards pickle compatibility
            self.owned = set()
        if key not in self.owned:
            super().__setitem__(key, super().__getitem__(key).copy())
            self.owned.add(key)

    def update(self, *args, **kwargs):
        "Iterates through the dictionary created by args and kwargs"
        if not self and len(args) == 1 and isinstance(args[0], KeyDict):
            super().update(args[0])
            self.keymap.update(args[0].keymap)
            self._unmapped_keys.update(
                args[0]._unmapped_keys  # pylint:disable=protected-access
            )
        else:
            for k, v in dict(*args, **kwargs).items():
                self[k] = v

    def __call__(self, key):  # if uniting is ever a speed hit, cache it
        got = self[key]
        if isinstance(got, dict):
            for k, v in got.items():
                got[k] = v * (k.units or DIMLESS_QUANTITY)
            return got
        if not hasattr(key, "units"):
            (key,) = self.keymap[self.parse_and_index(key)[0]]
        return Quantity(got, key.units or "dimensionless")

    def __getitem__(self, key):
        "Overloads __getitem__ and [] access to work with all keys"
        key, idx = self.parse_and_index(key)
        keys = self.keymap[key]
        if not keys:
            del self.keymap[key]  # remove blank entry added by defaultdict
            raise KeyError(key)
        got = {}
        for k in keys:
            if not idx and k.shape:
                self._copyonwrite(k)
            val = dict.__getitem__(self, k)
            if idx:
                if len(idx) < len(val.shape):
                    idx = (...,) + idx  # idx from the right, in case of sweep
                val = val[idx]
            if len(keys) == 1:
                return val
            got[k] = val
        return got

    def __setitem__(self, key, value):
        "Overloads __setitem__ and []= to work with all keys"
        # pylint: disable=too-many-boolean-expressions,too-many-branches
        # pylint: disable=too-many-statements
        try:
            key, idx = self.parse_and_index(key)
        except KeyError as e:  # may be indexed VectorVariable
            # NOTE: this try/except takes ~4% of the time in this loop
            if not hasattr(key, "shape"):
                raise e
            if not hasattr(value, "shape"):
                value = np.full(key.shape, value)
            elif key.shape != value.shape:
                raise KeyError("Key and value have different shapes") from e
            for subkey, subval in zip(key.flat, value.flat):
                self[subkey] = subval
            return
        value = clean_value(key, value)
        if key not in self.keymap:
            if not hasattr(self, "_unmapped_keys"):
                self.__init__()  # py3's pickle sets items before init... :(
            self.keymap[key].add(key)
            self._unmapped_keys.add(key)
            if idx:
                dty = {} if isinstance(value, Numbers) else {"dtype": "object"}
                if getattr(value, "shape", None) and value.dtype != INT_DTYPE:
                    dty["dtype"] = value.dtype
                dict.__setitem__(self, key, np.full(key.shape, np.nan, **dty))
                self.owned.add(key)
        if idx:
            if is_sweepvar(value):
                old = super().__getitem__(key)
                super().__setitem__(key, np.array(old, "object"))
                self.owned.add(key)
            self._copyonwrite(key)
            if hasattr(value, "__call__"):  # a linked function
                old = super().__getitem__(key)
                super().__setitem__(key, np.array(old, dtype="object"))
            super().__getitem__(key)[idx] = value
            return  # successfully set a single index!
        if key.shape:  # now if we're setting an array...
            if hasattr(value, "__call__"):  # a linked vector-function
                key.vecfn = value
                value = np.empty(key.shape, dtype="object")
                it = np.nditer(value, flags=["multi_index", "refs_ok"])
                while not it.finished:
                    i = it.multi_index
                    it.iternext()
                    value[i] = veclinkedfn(key.vecfn, i)
            if getattr(value, "shape", None):  # is the value an array?
                if value.dtype == INT_DTYPE:
                    value = np.array(value, "f")  # convert to float
                if dict.__contains__(self, key):
                    old = super().__getitem__(key)
                    if old.dtype != value.dtype:
                        # e.g. replacing a number with a linked function
                        newly_typed_array = np.array(old, dtype=value.dtype)
                        super().__setitem__(key, newly_typed_array)
                        self.owned.add(key)
                    self._copyonwrite(key)
                    goodvals = ~isnan(value)
                    super().__getitem__(key)[goodvals] = value[goodvals]
                    return  # successfully set only some indexes!
            elif not is_sweepvar(value):  # or needs to be made one?
                if not hasattr(value, "__len__"):
                    value = np.full(key.shape, value, "f")
                elif not isinstance(value[0], np.ndarray):
                    clean_values = [clean_value(key, v) for v in value]
                    dtype = None
                    if any(is_sweepvar(cv) for cv in clean_values):
                        dtype = "object"
                    value = np.array(clean_values, dtype=dtype)
        super().__setitem__(key, value)
        self.owned.add(key)

    def __delitem__(self, key):
        "Overloads del [] to work with all keys"
        if not hasattr(key, "key"):  # not a keyed object
            self.update_keymap()
            keys = self.keymap[key]
            if not keys:
                raise KeyError(key)
            for k in keys:
                del self[k]
        else:
            key = key.key
            veckey, idx = self.parse_and_index(key)
            if idx is None:
                super().__delitem__(key)
            else:
                super().__getitem__(veckey)[idx] = np.nan
                if isnan(super().__getitem__(veckey)).all():
                    super().__delitem__(veckey)
            copiedonwrite = set()  # to save time, .update() does not copy
            mapkeys = set([key])
            if key.keys:
                mapkeys.update(key.keys)
            for mapkey in mapkeys:
                if mapkey in self.keymap:
                    if len(self.keymap[mapkey]) == 1:
                        del self.keymap[mapkey]
                        continue
                    if mapkey not in copiedonwrite:
                        self.keymap[mapkey] = set(self.keymap[mapkey])
                        copiedonwrite.add(mapkey)
                    self.keymap[mapkey].remove(key)


class KeySet(KeyMap, set):
    "KeyMaps that don't collapse arrays or store values."

    collapse_arrays = False

    def update(self, keys):
        "Iterates through the dictionary created by args and kwargs"
        for key in keys:
            self.keymap[key].add(key)
        self._unmapped_keys.update(keys)
        super().update(keys)

    def __getitem__(self, key):
        "Gets the keys corresponding to a particular key."
        key, _ = self.parse_and_index(key)
        return self.keymap[key]
