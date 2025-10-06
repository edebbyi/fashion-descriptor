.PHONY: run api ui test

run:
	python -m src.cli --in data/images --out outputs --passes A,B,C --normalize yes

api:
	uvicorn api.app:app --host 0.0.0.0 --port 8000 --reload

ui:
	@echo "🚀 Starting Visual Descriptor AI Interface..."
	@echo "📍 URL: http://localhost:8501"
	@echo ""
	streamlit run app.py

test:
	pytest -q