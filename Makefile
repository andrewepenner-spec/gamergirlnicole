.PHONY: run test
run:
	python run.py
test:
	python -m pytest -q tests/test_engine.py tests/test_api.py
