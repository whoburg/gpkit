.PHONY: install-dev clean test lint

# Development environment setup
install-dev:
	pip install -r requirements-dev.txt

# Code quality
lint:
	pylint gpkit

# Testing
test:
	python -c "import gpkit.tests; gpkit.tests.run()"

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
	@echo "  test              Run tests"
	@echo "  clean             Clean build artifacts"
	@echo "  help              Show this help message"