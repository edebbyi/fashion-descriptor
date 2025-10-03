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

## Makefile Commands

Convenient shortcuts for development and testing:

```bash
make ui         # Launch Streamlit interface (localhost:8501)
make api        # Start FastAPI server (localhost:8000) with hot reload
make run        # Run CLI with example parameters
make test       # Run pytest test suite
```

**Examples:**
```bash
# Start the web UI
make ui

# Start the API server for development
make api

# Run batch processing
make run

# Run tests
make test
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

### Local Development

Use the Makefile for quick local development:

```bash
# UI development
make ui

# API development with auto-reload
make api
```

### Docker Build

```bash
# Build image
docker build -t visual-descriptor:latest .

# Run container
docker run -p 8080:8080 \
  -e GEMINI_API_KEY=your_key \
  -e API_KEY=your_auth_key \
  -e VD_MODEL=gemini \
  visual-descriptor:latest
```

### Google Cloud Run Deployment

The project includes automated deployment via Cloud Build:

#### Prerequisites

```bash
# Install gcloud CLI
# https://cloud.google.com/sdk/docs/install

# Set project
gcloud config set project YOUR_PROJECT_ID

# Enable required APIs
gcloud services enable \
  cloudbuild.googleapis.com \
  run.googleapis.com \
  artifactregistry.googleapis.com

# Create Artifact Registry repository
gcloud artifacts repositories create visual-descriptor \
  --repository-format=docker \
  --location=us-central1

# Store secrets
echo -n "your_api_key" | gcloud secrets create API_KEY --data-file=-
echo -n "your_gemini_key" | gcloud secrets create GEMINI_API_KEY --data-file=-
```

#### Deploy with Cloud Build

The `cloudbuild.yaml` configuration handles:
- Building the Docker image
- Pushing to Artifact Registry
- Deploying to Cloud Run with:
  - Auto-scaling (0-10 instances)
  - 2GB memory, 2 CPUs
  - 5-minute timeout
  - Environment variables and secrets injection

**Trigger deployment:**

```bash
# Manual deployment
gcloud builds submit --config cloudbuild.yaml

# Or set up automatic deployment from GitHub
gcloud builds triggers create github \
  --repo-name=YOUR_REPO \
  --repo-owner=YOUR_GITHUB_USER \
  --branch-pattern="^main$" \
  --build-config=cloudbuild.yaml
```

**Cloud Build Configuration** (`cloudbuild.yaml`):
```yaml
substitutions:
  _SERVICE: visual-descriptor
  _REGION: us-central1
  _REPO: visual-descriptor
  _IMAGE: app

steps:
  # Builds Docker image and tags with BUILD_ID and latest
  # Pushes both tags to Artifact Registry
  # Deploys to Cloud Run with:
  #   - VD_MODEL=gemini environment variable
  #   - API_KEY and GEMINI_API_KEY from Secret Manager
  #   - Auto-scaling, memory, CPU, and timeout settings
```

#### Deployment Configuration

Edit `cloudbuild.yaml` to customize:
- **Service name**: `_SERVICE` substitution
- **Region**: `_REGION` (default: us-central1)
- **Resources**: `--memory`, `--cpu` flags
- **Scaling**: `--min-instances`, `--max-instances`
- **Timeout**: `--timeout` (default: 300s)

#### Access Deployed Service

```bash
# Get service URL
gcloud run services describe visual-descriptor \
  --region=us-central1 \
  --format='value(status.url)'

# Test health endpoint
curl https://visual-descriptor-xxx-uc.a.run.app/healthz

# Analyze image
curl -X POST https://visual-descriptor-xxx-uc.a.run.app/v1/jobs \
  -H "Authorization: Bearer your_api_key" \
  -F "file=@image.jpg"
```

#### Monitoring

```bash
# View logs
gcloud run services logs read visual-descriptor \
  --region=us-central1 \
  --limit=50

# View metrics in Cloud Console
# https://console.cloud.google.com/run
```

## API Reference
Live API: https://visual-descriptor-516904417440.us-central1.run.app
Interactive Docs: https://visual-descriptor-516904417440.us-central1.run.app/docs

See [docs/api.md](docs/api.md) for:
- Cloud Run base URL
- Complete endpoint documentation
- Authentication details
- Rate limiting information
- Example requests and responses

## Project Structure

```
visual-descriptor/
├── api/
│   └── app.py              # FastAPI server
├── docs/
│   └── api.md              # API documentation
├── prompts/
│   ├── passA_global.txt
│   ├── passB_construction.txt
│   ├── passC_pose_lighting.txt
│   └── system.txt     
├── src/
│   └── visual_descriptor/
│       ├── captioners/     # AI model backends
│       ├── engine.py       # Core orchestration
│       ├── schema.py       # Pydantic models
│       └── multipass_merge.py
├── tests/
│   └── test_gemini.py      # Backend tests
├── ui/
│   ├── app.py              # Streamlit UI
│   └── pages/              # UI pages
├── Dockerfile              # Container image
├── Makefile                # Development shortcuts
├── cloudbuild.yaml         # Cloud deployment config
└── requirements.tct        # Python dependencies     
```

## Key Files

- **`Makefile`**: Development shortcuts (ui, api, run, test)
- **`cloudbuild.yaml`**: Automated Cloud Run deployment
- **`Dockerfile`**: Production container image
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

**Cloud Build deployment fails**
- Verify APIs are enabled
- Check Secret Manager has API_KEY and GEMINI_API_KEY
- Review logs: `gcloud builds log --region=us-central1`

## License

MIT License - see [LICENSE](LICENSE)

## Support

- Issues: artofesosa@gmail.com
- Docs: [api.md](docs/api.md)

---

**Built for fashion tech** 👗✨
