.PHONY: install-dev clean test test-pytest lint sort format

# Development environment setup
install-dev:
	pip install -r requirements-dev.txt
	pip install -e .

# Code quality
lint:
	pylint gpkit

# Import sorting
sort:
	isort --profile black gpkit

# Code formatting
format:
	black gpkit

# Testing
test:  # Run tests using the original test runner
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

# Help
help:
	@echo "Available commands:"
	@echo "  install-dev        Install development dependencies"
	@echo "  lint              Run pylint"
	@echo "  sort              Sort imports with isort"
	@echo "  format            Format code with black"
	@echo "  test              Run tests using the original test runner"
	@echo "  test-pytest       Run tests with pytest"
	@echo "  clean             Clean build artifacts"
	@echo "  help              Show this help message"