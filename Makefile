.PHONY: install test clean typecheck

install:
	uv pip install -e ".[dev]"

test:
	pytest tests/ -v

typecheck:
	uvx mypy src/cenv

clean:
	rm -rf build/ dist/ *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
