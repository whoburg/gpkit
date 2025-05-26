.PHONY: install-dev clean check-clean test test-unittest test-pytest lint format

# Development environment setup
install-dev:
	pip install -r requirements-dev.txt
	pip install -e .

# Code quality
lint:
	pylint gpkit

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
	if [[ -n "$(git status --porcelain)" ]]; then
		echo "Tests caused uncommitted changes:"
		git status --porcelain
		exit 1
	else
		echo "No uncommitted changes detected."
	fi

# Help
help:
	@echo "Available commands:"
	@echo "  install-dev        Install development dependencies"
	@echo "  lint              Run pylint"
	@echo "  format            Format code with black"
	@echo "  test              Run both unittest and pytest"
	@echo "  test-unittest     Run tests using the original test runner"
	@echo "  test-pytest       Run tests with pytest"
	@echo "  clean             Clean build artifacts"
	@echo "  check-clean       Check no uncommitted changes"
	@echo "  help              Show this help message"
