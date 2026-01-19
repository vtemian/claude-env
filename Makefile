.PHONY: install test test-cov typecheck lint format check clean \
       docker-build docker-test-portability docker-test-portability-shell docker-test-real-import

install:
	uv pip install -e ".[dev]"

test:
	pytest tests/ -v

test-cov:
	pytest --cov=src/cenv --cov-report=term-missing --cov-report=xml -v

typecheck:
	mypy src/cenv --strict

lint:
	ruff check src/cenv tests/

format:
	ruff check --fix src/cenv tests/

check: lint typecheck test-cov
	@echo "✅ All checks passed!"

clean:
	rm -rf build/ dist/ *.egg-info
	rm -f coverage.xml .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
	find . -type d -name .mypy_cache -exec rm -rf {} +
	find . -type d -name .ruff_cache -exec rm -rf {} +

# Docker-based path portability testing
docker-build:
	docker build -t cenv-test -f Dockerfile.test .

docker-test-portability: docker-build
	@echo "Running path portability test in Docker..."
	docker run --rm cenv-test

docker-test-portability-shell: docker-build
	@echo "Opening shell in Docker container for manual testing..."
	@echo "Try: cenv create test --from-repo <your-repo-url>"
	docker run --rm -it cenv-test bash

# Test with a real GitHub repo (pass REPO=<url> to test with your repo)
# Example: make docker-test-real-import REPO=https://github.com/vtemian/.claude.git
# This tests the clone_from_github function directly (which does path expansion)
docker-test-real-import: docker-build
	@if [ -z "$(REPO)" ]; then \
		echo "Usage: make docker-test-real-import REPO=<github-url>"; \
		echo "Example: make docker-test-real-import REPO=https://github.com/vtemian/.claude.git"; \
		exit 1; \
	fi
	@echo "Testing real import from $(REPO)..."
	docker run --rm cenv-test /bin/bash -c '\
		set -e; \
		TARGET=~/test-import; \
		echo "=== Cloning and expanding paths from repo ==="; \
		echo "Target: $$TARGET"; \
		echo "Home: $$HOME"; \
		python3 -c "from pathlib import Path; from cenv.github import clone_from_github; clone_from_github(\"$(REPO)\", Path.home() / \"test-import\"); print(\"Clone successful!\")"; \
		echo ""; \
		echo "=== Checking for unexpanded placeholders ==="; \
		if grep -r "{{CLAUDE_HOME}}\|{{USER_HOME}}" $$TARGET/ 2>/dev/null; then \
			echo "FAILED: Found unexpanded placeholders!"; \
			exit 1; \
		else \
			echo "OK: No unexpanded placeholders found"; \
		fi; \
		echo ""; \
		echo "=== Checking for original user paths ==="; \
		if grep -r "/Users/" $$TARGET/*.json 2>/dev/null; then \
			echo "FAILED: Found macOS user paths that should have been expanded:"; \
			grep -r "/Users/" $$TARGET/*.json; \
			exit 1; \
		else \
			echo "OK: No original macOS user paths found"; \
		fi; \
		echo ""; \
		echo "=== Checking paths are expanded to local user ==="; \
		if grep -r "/home/testuser" $$TARGET/*.json 2>/dev/null; then \
			echo "OK: Paths correctly expanded to local user:"; \
			grep -r "/home/testuser" $$TARGET/*.json | head -5; \
		else \
			echo "WARNING: No paths with local user found (may be OK if no paths in config)"; \
		fi; \
		echo ""; \
		echo "=== JSON files content ==="; \
		find $$TARGET -name "*.json" -exec echo "--- {} ---" \; -exec cat {} \; -exec echo "" \; 2>/dev/null || echo "No JSON files found"; \
		echo ""; \
		echo "=== TEST PASSED ===" \
	'
