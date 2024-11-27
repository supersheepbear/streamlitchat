.PHONY: clean clean-build clean-pyc clean-test coverage dist docs help install lint-check lint-all type-check check-deps update-deps clean-docs test-results test-with-report clean-test-results test-results-dir view-test-results test-summary archive-test-results test-parallel

.DEFAULT_GOAL := help

define BROWSER_PYSCRIPT
import os, webbrowser, sys
from urllib.request import pathname2url
webbrowser.open("file://" + pathname2url(os.path.abspath(sys.argv[1])))
endef
export BROWSER_PYSCRIPT

define PRINT_HELP_PYSCRIPT
import re, sys
for line in sys.stdin:
	match = re.match(r'^([a-zA-Z_-]+):.*?## (.*)$$', line)
	if match:
		target, help = match.groups()
		print("%-20s %s" % (target, help))
endef
export PRINT_HELP_PYSCRIPT

BROWSER := python -c "$$BROWSER_PYSCRIPT"

help:
	@python -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)

clean: clean-build clean-pyc clean-test clean-test-results ## remove all build, test, coverage and Python artifacts
	@echo "All build, test, coverage and Python artifacts removed successfully."

clean-build: ## remove build artifacts
	rm -fr build/ || true
	rm -fr dist/ || true
	rm -fr .eggs/ || true
	find . -name '*.egg-info' -exec rm -fr {} + || true
	find . -name '*.egg' -type f -exec rm -f {} + || true
	@echo "Build artifacts removed successfully."

clean-pyc: ## remove Python file artifacts
	find . -name '*.pyc' -exec rm -f {} + || true
	find . -name '*.pyo' -exec rm -f {} + || true
	find . -name '*~' -exec rm -f {} + || true
	find . -name '__pycache__' -exec rm -fr {} + || true
	@echo "Python file artifacts removed successfully."

clean-test: ## remove test and coverage artifacts
	rm -fr .tox/ || true
	rm -f .coverage || true
	rm -fr htmlcov/ || true
	rm -fr .pytest_cache/ || true
	@echo "Test and coverage artifacts removed successfully."

clean-test-results: ## remove test result artifacts
	rm -rf test-results/*.html || true
	rm -rf test-results/*.xml || true
	rm -rf test-results/*.log || true
	@echo "Test results cleaned successfully."

test-results-dir:
	mkdir -p test-results

test: test-with-report ## run tests with detailed reports
	@echo "Tests completed successfully."

test-with-report: test-results-dir ## run tests and generate detailed HTML and XML reports
	pytest \
		--html=test-results/report.html \
		--self-contained-html \
		--junitxml=test-results/junit.xml \
		--log-file=test-results/pytest.log \
		--log-file-level=DEBUG \
		--verbose \
		--asyncio-mode=auto \
		tests/ || { echo "Tests failed with status $$?"; exit 1; }
	@echo "Test reports generated in test-results directory."

view-test-results: ## open test results in default browser
	$(BROWSER) test-results/report.html
	@echo "Opening test results in browser."

test-summary: ## display test summary from junit.xml
	@if [ -f test-results/junit.xml ]; then \
		echo "Test Summary:"; \
		echo "------------"; \
		python -c "import xml.etree.ElementTree as ET; \
			tree = ET.parse('test-results/junit.xml'); \
			root = tree.getroot(); \
			print(f'Tests: {root.attrib.get(\"tests\", \"0\")}'); \
			print(f'Failures: {root.attrib.get(\"failures\", \"0\")}'); \
			print(f'Errors: {root.attrib.get(\"errors\", \"0\")}'); \
			print(f'Skipped: {root.attrib.get(\"skipped\", \"0\")}'); \
			print(f'Time: {float(root.attrib.get(\"time\", \"0\")):.2f}s')"; \
	else \
		echo "No test results found. Run 'make test-with-report' first."; \
	fi

archive-test-results: ## archive test results with timestamp
	@timestamp=$$(date +%Y%m%d_%H%M%S); \
	mkdir -p test-results/archive_$$timestamp; \
	cp test-results/*.html test-results/*.xml test-results/*.log test-results/archive_$$timestamp/ 2>/dev/null || true; \
	echo "Test results archived to test-results/archive_$$timestamp"

test-all: ## run tests on every Python version with tox
	tox
	@echo "All tests completed successfully on every Python version."

coverage: test-results-dir ## check code coverage with detailed reports
	coverage run --source src/streamlitchat -m pytest \
		--cov=src/streamlitchat \
		--cov-report=html:test-results/coverage \
		--cov-report=xml:test-results/coverage.xml \
		tests/
	coverage report -m

docs: ## generate Sphinx HTML documentation, including API docs
	rm -f docs/streamlitchat.rst
	rm -f docs/modules.rst
	sphinx-apidoc -o docs/ src/streamlitchat || { echo "sphinx-apidoc failed"; exit 1; }
	$(MAKE) -C docs clean
	$(MAKE) -C docs html || { echo "Sphinx build failed"; exit 1; }
	$(BROWSER) docs/_build/html/index.html
	@echo "Documentation generated successfully."

clean-docs: ## Remove documentation build artifacts
	rm -rf docs/_build
	@echo "Documentation build artifacts removed successfully."

servedocs: docs ## compile the docs watching for changes
	watchmedo shell-command -p '*.rst' -c '$(MAKE) -C docs html' -R -D .
	@echo "Documentation server started successfully."

release: dist ## package and upload a release
	twine upload dist/*
	@echo "Release uploaded successfully."

dist: ## builds source and wheel package
	python -m build
	ls -l dist
	@echo "Distribution packages built successfully."

install: ## install the package to the active Python's site-packages
	pip install .
	@echo "Package installed successfully."

lint-check: ## check style with ruff
	ruff check src/streamlitchat tests
	@echo "Linting check completed successfully."

lint-all: ## automatically fix style issues with ruff
	ruff check --fix src/streamlitchat tests
	@echo "Automatic linting completed successfully."

type-check: ## Run static type checks using mypy
	mypy src/streamlitchat
	@echo "Type checking completed successfully."

test-parallel: test-results-dir ## run tests in parallel
	pytest -n auto \
		--html=test-results/report.html \
		--self-contained-html \
		--junitxml=test-results/junit.xml \
		tests/

