# Visual Descriptor AI

AI-powered fashion image analysis using Gemini Flash 2.5 or GPT-4o. Extracts structured garment data (fabric, colors, construction, etc.) from product photos.

## Quick Start

```bash
# Install
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Get API key from https://aistudio.google.com/app/apikey
export GEMINI_API_KEY=your_key_here
export API_KEY=your_auth_key

# Run
streamlit run ui/app.py              # Web UI at localhost:8501
# OR
uvicorn api.app:app --reload         # API at localhost:8000
# OR
python -m src.cli --in image.jpg --out outputs --model gemini
```

## Features

- **Multi-pass analysis**: Global → Construction → Presentation
- **Multiple backends**: Gemini (free), GPT-4o (paid), or stub (testing)
- **Structured output**: 50+ JSON fields with Pydantic validation
- **Three interfaces**: Web UI, REST API, CLI
- **Cloud-ready**: Docker + Google Cloud Run deployment

## Architecture

```
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│ Streamlit UI│  │  FastAPI    │  │     CLI     │
└──────┬──────┘  └──────┬──────┘  └──────┬──────┘
       │                │                │
       └────────────────┴────────────────┘
                        │
                 ┌──────▼──────┐
                 │   Engine    │
                 │ (multipass) │
                 └──────┬──────┘
                        │
       ┌────────────────┼────────────────┐
       │                │                │
┌──────▼──────┐  ┌──────▼──────┐  ┌─────▼─────┐
│   Gemini    │  │   GPT-4o    │  │   Stub    │
│  Flash 2.5  │  │             │  │ (testing) │
└─────────────┘  └─────────────┘  └───────────┘
```

## API Usage

### Start Server

```bash
export VD_MODEL=gemini
export GEMINI_API_KEY=your_key
export API_KEY=dev_key_123
uvicorn api.app:app --port 8000
```

### Analyze Image

```bash
curl -X POST http://localhost:8000/v1/jobs \
  -H "Authorization: Bearer dev_key_123" \
  -F "file=@image.jpg" \
  -F "passes=A,B,C"
```

### Response

```json
{
  "job_id": "j_abc123",
  "status": "completed",
  "records": [{
    "image_id": "image",
    "garment_type": "dress",
    "silhouette": "bodycon",
    "fabric": {
      "type": "jersey",
      "texture": "smooth",
      "weight": "medium",
      "finish": "matte"
    },
    "colors": {
      "primary": "royal purple",
      "pattern": {"type": "polka_dot"}
    },
    "construction": {
      "seams": "princess seams",
      "closure": "zipper"
    },
    "prompt_text": "Long sleeve bodycon dress..."
  }]
}
```

## Configuration

### Model Selection

```bash
export VD_MODEL=gemini    # Free, recommended
export VD_MODEL=openai    # Paid, $0.03/image
export VD_MODEL=stub      # Testing only
```

### Analysis Passes

- **A** (required): Garment type, fabric, colors, silhouette
- **B** (optional): Construction details (seams, stitching, closures)
- **C** (optional): Photography (pose, lighting, camera)

```bash
# Use all passes for complete data
python -m src.cli --passes A,B,C --in image.jpg
```

## Deployment

See [deployment.md](deployment.md) for Cloud Run, Docker, and production setup.

## Development

```bash
# Run tests
pytest

# Format code
black src/ tests/

# Lint
pylint src/

# Type check
mypy src/
```

## Project Structure

```
visual-descriptor/
├── api/
│   └── app.py              # FastAPI server
├── src/
│   └── visual_descriptor/
│       ├── captioners/     # AI model backends
│       ├── engine.py       # Core orchestration
│       ├── schema.py       # Pydantic models
│       └── multipass_merge.py
├── ui/
│   ├── app.py             # Streamlit UI
│   └── pages/             # UI pages
├── requirements.txt
├── Dockerfile
└── deploy.sh
```

## Key Files

- **`engine.py`**: Main orchestrator, handles multi-pass workflow
- **`captioners/gemini_vlm.py`**: Gemini backend
- **`captioners/openai_vlm.py`**: GPT-4o backend
- **`schema.py`**: Pydantic data models
- **`api/app.py`**: FastAPI endpoints
- **`ui/app.py`**: Streamlit interface

## Performance

| Model | Speed | Cost | Quality |
|-------|-------|------|---------|
| Gemini Flash 2.5 | 2-4s | Free | ⭐⭐⭐⭐⭐ |
| GPT-4o | 3-5s | $0.03 | ⭐⭐⭐⭐ |

**Rate Limits (Gemini free tier):**
- 15 requests/minute
- 1,500 requests/day

## Troubleshooting

**"Module google.generativeai not found"**
```bash
pip install google-generativeai==0.8.3
```

**"GEMINI_API_KEY not set"**
```bash
export GEMINI_API_KEY=your_key
# Get from https://aistudio.google.com/app/apikey
```

**Rate limit exceeded**
- Wait 1 minute or implement exponential backoff
- Free tier: 15/min, upgrade to paid for more

**Poor quality results**
- Use high-resolution images (800px+)
- Run all 3 passes (A,B,C)
- Try switching models

## License

MIT License - see [LICENSE](LICENSE)

## Support

- Issues: artofesosa@gmail.com
- Docs: [deployment.md](deployment.md), [api.md](api.md)

---

**Built for fashion tech** 👗✨
