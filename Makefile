PYTHON ?= python3
.PHONY: test run docker
test:
	$(PYTHON) -m pytest -q
run:
	PYTHONPATH=src $(PYTHON) -m uvicorn k8strouble.main:app --reload --port 8080
docker:
	docker build -t ai-kubernetes-troubleshooter:local .
