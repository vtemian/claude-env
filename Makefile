.PHONY: install test clean

install:
	uv pip install -e ".[dev]"

test:
	pytest tests/ -v

clean:
	rm -rf build/ dist/ *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
