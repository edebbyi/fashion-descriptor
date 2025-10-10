.PHONY: run api ui test test-api test-single test-folder health

run:
	python -m src.cli --in data/images --out outputs --passes A,B,C --normalize yes

api:
	set -a && source .env && set +a && .venv/bin/uvicorn api.app:app --host 0.0.0.0 --port 8000 --reload

ui:
	@echo "Starting Visual Descriptor AI Interface..."
	@echo "URL: http://localhost:8501"
	@echo ""
	streamlit run app.py

test:
	pytest -q

# API Testing Commands
health:
	@echo "Testing API health endpoint..."
	curl -s http://localhost:8000/healthz | jq .

test-api: health
	@echo "\nRunning API tests..."
	@echo "Make sure the API server is running: make api"

test-single:
	@echo "Testing single image analysis..."
	@echo "Usage: make test-single IMAGE=path/to/image.jpg"
	@if [ -z "$(IMAGE)" ]; then \
		echo "Error: Please specify IMAGE=path/to/image.jpg"; \
		exit 1; \
	fi
	@echo "Analyzing: $(IMAGE)"
	curl -X POST http://localhost:8000/v1/jobs \
		-H "Authorization: Bearer dev_key_123" \
		-F "file=@$(IMAGE)" \
		-F "passes=A,B,C" \
		| jq .

test-folder:
	@echo "Testing ZIP folder analysis..."
	@echo "Usage: make test-folder ZIP=path/to/images.zip"
	@if [ -z "$(ZIP)" ]; then \
		echo "Error: Please specify ZIP=path/to/images.zip"; \
		exit 1; \
	fi
	@echo "Analyzing: $(ZIP)"
	curl -X POST http://localhost:8000/v1/jobs \
		-H "Authorization: Bearer dev_key_123" \
		-F "file=@$(ZIP)" \
		-F "passes=A,B,C" \
		| jq .
