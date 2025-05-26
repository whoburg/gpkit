.PHONY: install-dev install-lint install-test clean check-clean test test-unittest test-pytest lint format

# Development environment setup
install-dev:
	pip install -e .[lint,test]

install-lint:
	pip install .[lint]

install-test:
	pip install .[test]

# Code quality
lint:
	flake8 --max-line-length=88 --ignore=E203,W503,F821 --per-file-ignores="__init__.py:F401" gpkit

# Code formatting
format:
	isort --profile black gpkit
	black gpkit

# Testing
test: test-unittest test-pytest  # Run both test runners

test-unittest:  # Run tests using the original test runner
	python -c "import gpkit.tests; gpkit.tests.run()"

test-pytest:  # Run tests with pytest
	pytest gpkit/tests -v

# Cleanup
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

check-clean:
	@if [ -n "$$(git status --porcelain)" ]; then \
		echo "Found uncommitted changes:"; \
		git status --porcelain; \
		exit 1; \
	else \
		echo "Working directory is clean."; \
	fi


# Help
help:
	@echo "Available commands:"
	@echo "  install-dev       Editable install for local development"
	@echo "  install-lint      Install with linting tools for CI"
	@echo "  install-test      Install with testing tools for CI"
	@echo "  lint              Run pylint"
	@echo "  format            Format code with isort and black"
	@echo "  test              Run both unittest and pytest"
	@echo "  test-unittest     Run tests using the original test runner"
	@echo "  test-pytest       Run tests with pytest"
	@echo "  clean             Clean build artifacts"
	@echo "  check-clean       Check no uncommitted changes"
	@echo "  help              Show this help message"
