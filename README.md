# Visual Descriptor Tool - Gemini Flash 2.5 Edition

**AI-powered fashion image analysis** that extracts structured descriptors (fabric, silhouette, construction, colors, lighting) from photos. Now powered by **Google's Gemini Flash 2.5** for superior vision analysis.

## 🎯 Key Features

- **Advanced Fashion Analysis**: Detects garment types, fabrics, construction details, colors, patterns
- **Multi-pass Processing**: Global → Construction → Pose/Lighting for comprehensive analysis
- **Production-Ready API**: FastAPI with authentication, ready for Google Cloud Run
- **Multiple Backends**: Gemini Flash 2.5, GPT-4o, or local stub
- **Structured Output**: Validated JSON schema with fabric details, colors, stitching, lighting

## 🚀 Quick Start

### 1. Install Dependencies

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Set Up API Keys

```bash
# Copy environment template
cp .env.example .env

# Get your Gemini API key from: https://aistudio.google.com/app/apikey
# Edit .env and add:
# - GEMINI_API_KEY=your_key_here
# - API_KEY=your_auth_key
```

### 3. Run Locally

#### CLI Mode
```bash
# Single image
python -m src.cli --in data/images/look1.jpg --out outputs --model gemini

# Folder of images
python -m src.cli --in data/images --out outputs --passes A,B,C --model gemini
```

#### API Mode
```bash
# Start API server
export VD_MODEL=gemini
export GEMINI_API_KEY=your_key_here
export API_KEY=dev_key_123

make api
# OR: uvicorn api.app:app --reload --port 8000
```

#### Test API
```bash
curl -X POST http://localhost:8000/v1/jobs \
  -H "Authorization: Bearer dev_key_123" \
  -F "file=@your_image.jpg" \
  -F "passes=A,B,C"
```

## ☁️ Deploy to Google Cloud Run

### Quick Deploy

```bash
export PROJECT_ID=your-google-cloud-project
./deploy.sh
```

This automated script will:
1. Enable required APIs
2. Create Artifact Registry
3. Set up secrets (API_KEY, GEMINI_API_KEY)
4. Build and deploy to Cloud Run

### Manual Deploy

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions.

## 📊 Output Format

The API returns structured JSON with comprehensive fashion descriptors:

```json
{
  "image_id": "look1",
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
    "secondary": null,
    "pattern": {
      "type": "polka_dot",
      "foreground": "white",
      "background": "royal purple"
    },
    "accents": [
      {"role": "zipper_tape", "color": "silver", "hex": "#C0C0C0"}
    ]
  },
  "construction": {
    "seams": "princess seams",
    "stitching": "topstitch",
    "stitching_color": "matching",
    "closure": "exposed center-front zipper",
    "top": { ... },
    "bottom": { ... }
  },
  "pose": "walking, facing camera",
  "model": {
    "framing": "full body",
    "expression": "confident",
    "gaze": "direct"
  },
  "camera": {
    "view": "front",
    "angle": "eye level"
  },
  "environment_lighting": {
    "setup": "studio softbox",
    "mood": "bright",
    "background": "plain white sweep"
  }
}
```

## 🎨 Model Comparison

| Backend | Quality | Speed | Cost | Best For |
|---------|---------|-------|------|----------|
| **Gemini Flash 2.5** | ⭐⭐⭐⭐⭐ | Fast | **FREE** | Production (recommended) |
| GPT-4o | ⭐⭐⭐⭐ | Medium | $$$ | When Gemini unavailable |
| Stub | ⭐⭐ | Instant | Free | Testing/development |

## 🔧 Configuration

### Switch Models

```bash
# Use Gemini (recommended)
export VD_MODEL=gemini
export GEMINI_API_KEY=your_key

# Use OpenAI GPT-4o
export VD_MODEL=openai
export OPENAI_API_KEY=your_key

# Use stub (free, for testing)
export VD_MODEL=stub
```

### Analysis Passes

- **Pass A (Global)**: Garment type, silhouette, fabric, colors, patterns, footwear
- **Pass B (Construction)**: Seams, stitching, hems, closures, construction details
- **Pass C (Presentation)**: Pose, model framing, camera angle, lighting setup

Run all three for comprehensive analysis: `--passes A,B,C`

## 📁 Project Structure

```
visual-descriptor/
├── api/
│   └── app.py              # FastAPI server
├── src/
│   └── visual_descriptor/
│       ├── captioners/
│       │   ├── gemini_vlm.py    # Gemini Flash 2.5
│       │   ├── openai_vlm.py    # GPT-4o
│       │   └── stub.py          # Test stub
│       ├── engine.py            # Core analysis engine
│       ├── schema.py            # Pydantic models
│       └── normalize_vocab.py   # Vocab standardization
├── requirements.txt
├── Dockerfile
├── cloudbuild.yaml
├── deploy.sh               # Automated deployment
└── DEPLOYMENT.md           # Detailed deploy guide
```

## 🐛 Troubleshooting

### "Module google.generativeai not found"
```bash
pip install google-generativeai==0.8.3
```

### "GEMINI_API_KEY not set"
Get your key from: https://aistudio.google.com/app/apikey

### Cloud Run build fails
See common fixes in [DEPLOYMENT.md](DEPLOYMENT.md#common-build-errors--fixes)

### Poor output quality
- Ensure you're using `gemini` or `openai` backend (not stub)
- Try adjusting passes: use all three (`A,B,C`) for best results
- Provide high-quality images (good lighting, clear garment details)

## 📚 API Documentation

Once deployed, visit your service URL + `/docs` for interactive API documentation:
- Local: http://localhost:8000/docs
- Cloud Run: https://your-service-url.run.app/docs

## 💡 Use Cases

- **E-commerce**: Auto-generate product descriptions
- **Fashion Design**: Analyze competitor designs
- **Wardrobe Apps**: Catalog clothing collections
- **Style Matching**: Find similar garments
- **Fashion Research**: Dataset annotation

## 🔒 Security

- API key authentication via `Authorization: Bearer <key>` header
- Secrets stored in Google Cloud Secret Manager
- No data persistence beyond processing
- HTTPS-only on Cloud Run

## 📊 Performance

- **Gemini Flash 2.5**: ~2-4 seconds per image
- **Cold start**: ~5-10 seconds (Cloud Run min-instances=0)
- **Memory**: 2GB recommended
- **Concurrent requests**: 10 max (configurable)

## 🆘 Support

- Report issues: https://github.com/your-repo/issues
- Cloud Run docs: https://cloud.google.com/run/docs
- Gemini API: https://ai.google.dev/docs

## 📄 License

MIT License - see [LICENSE](LICENSE) for details

---

**Built for fashion tech innovators** 👗✨
