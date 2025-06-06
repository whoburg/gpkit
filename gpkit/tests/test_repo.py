"Implements tests for all external repositories."

import os
import subprocess
import sys
from collections import defaultdict
from time import sleep

import pytest  # pylint: disable=import-error

pytestmark = pytest.mark.skip(
    reason="These tests require special setup and should be run separately"
)


def test_repo(repo=".", xmloutput=False):
    """Test repository.

    If no repo name given, runs in current directory.
    Otherwise, assumes is in directory above the repo
    with a shared gplibrary repository.
    """
    os.chdir(repo)
    settings = get_settings()
    print("")
    print("SETTINGS")
    print(settings)
    print("")

    if repo == "." and not os.path.isdir("gpkitmodels"):
        git_clone("gplibrary")
        pip_install("gplibrary", local=True)

    # install dependencies other than gplibrary
    if settings["pip install"]:
        for package in settings["pip install"].split(","):
            package = package.strip()
            pip_install(package)
    if os.path.isfile("setup.py"):
        pip_install(".")

    skipsolvers = None
    if "skipsolvers" in settings:
        skipsolvers = [s.strip() for s in settings["skipsolvers"].split(",")]

    testpy = (
        "from gpkit.tests.from_paths import run;"
        f"run(xmloutput={xmloutput}, skipsolvers={skipsolvers})"
    )
    subprocess.call(["python", "-c", testpy])
    if repo != ".":
        os.chdir("..")


def test_repos(repos=None, xmloutput=False, ingpkitmodels=False):
    """Get the list of external repos to test, and test.

    Arguments
    ---------
    xmloutput : bool
        True if the tests should produce xml reports

    ingpkitmodels : bool
        False if you're in the gpkitmodels directory that should be considered
        as the default. (overriden by repo-specific branch specifications)
    """
    if not ingpkitmodels:
        git_clone("gplibrary")
        repos_list_filename = "gplibrary" + os.sep + "EXTERNALTESTS"
        pip_install("gplibrary", local=True)
    else:
        print("USING LOCAL DIRECTORY AS GPKITMODELS DIRECTORY")
        repos_list_filename = "EXTERNALTESTS"
        pip_install(".", local=True)
    with open(repos_list_filename, "r", encoding="utf-8") as fil:
        repos = [line.strip() for line in fil]
    for repo in repos:
        git_clone(repo)
        test_repo(repo, xmloutput)


def get_settings():
    "Gets settings from a TESTCONFIG file"
    settings = defaultdict(str)
    if os.path.isfile("TESTCONFIG"):
        with open("TESTCONFIG", "r", encoding="utf-8") as f:
            for line in f:
                if len(line.strip().split(" : ")) > 1:
                    key, value = line.strip().split(" : ")
                    settings[key] = value
    return settings


def git_clone(repo, branch="master"):
    "Tries several times to clone a given repository"
    cmd = ["git", "clone", "--depth", "1"]
    cmd += ["-b", branch]
    cmd += [f"https://github.com/convexengineering/{repo}.git"]
    call_and_retry(cmd)


def pip_install(package, local=False):
    "Tries several times to install a pip package"
    if sys.platform == "win32":
        cmd = ["pip"]
    else:
        cmd = ["python", os.environ["PIP"]]
    cmd += ["install"]
    if local:
        cmd += ["--no-cache-dir", "--no-deps", "-e"]
    cmd += [package]
    call_and_retry(cmd)


def call_and_retry(cmd, max_iterations=5, delay=5):
    "Tries max_iterations times (waiting d each time) to run a command"
    iterations = 0
    return_code = None
    print("calling", cmd)
    while return_code != 0 and iterations < max_iterations:
        iterations += 1
        print("  attempt", iterations)
        return_code = subprocess.call(cmd)
        sleep(delay)
    return return_code
