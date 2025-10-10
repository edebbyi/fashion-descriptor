# API Reference

## Overview

REST API for fashion image analysis. Returns structured JSON with garment details.

## Base URLs

* **Production (Cloud Run):** `https://visual-descriptor-me2kgc2t6q-uc.a.run.app`
* **Local:** `http://localhost:8000`

> Set a base URL for examples:
>
> ```bash
> export VD_BASE_URL="https://visual-descriptor-me2kgc2t6q-uc.a.run.app"
> # For local dev:
> # export VD_BASE_URL="http://localhost:8000"
> ```

**Authentication:** Bearer token via `Authorization` header.

**Versioning:** All stable endpoints are under `/v1`.

**Quick Links (Prod):**

* Docs (Swagger): `https://visual-descriptor-me2kgc2t6q-uc.a.run.app/docs`
* Health: `https://visual-descriptor-me2kgc2t6q-uc.a.run.app/healthz`
* Root (redirects to docs): `https://visual-descriptor-me2kgc2t6q-uc.a.run.app/`

---

## Endpoints

### POST /v1/jobs

Analyze fashion images (single image or ZIP folder).

**Request Examples:**

```bash
# Analyze single image
curl -X POST "$VD_BASE_URL/v1/jobs" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -F "file=@image.jpg" \
  -F "passes=A,B,C" \
  -F "model=openai"

# Analyze ZIP folder with multiple images
curl -X POST "$VD_BASE_URL/v1/jobs" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -F "file=@fashion_collection.zip" \
  -F "passes=A,B" \
  -F "model=gemini"
```

**Parameters:**

* `file` (required): Image file or ZIP folder (multipart/form-data)
  * **Single Images**: JPG, JPEG, PNG, WebP
  * **ZIP Folders**: ZIP files containing supported image formats
    * Processes all images found recursively in ZIP
    * Filters out system files (.DS_Store, ._* resource forks)
    * Returns one record per valid image found
  * Max size: 50MB
* `passes` (optional): Comma-separated analysis passes
  * Default: "A,B,C"
  * Options: "A", "B", "C", "A,B", "A,B,C", etc.
* `model` (optional): AI model to use for analysis
  * Default: Uses environment `VD_MODEL` setting
  * Options:
    * `"openai"` - GPT-4 Vision (recommended for production)
    * `"gemini"` - Gemini Flash 2.5 (free tier available) 
    * `"blip2"` - Local BLIP2 model
    * `"stub"` - Mock model for testing

**Response:** `200 OK`

```json
{
  "job_id": "j_abc12345",
  "status": "completed",
  "backend": "GeminiVLM",
  "model": "gemini",
  "records": [
    {
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
        "secondary": null,
        "pattern": {
          "type": "polka_dot",
          "foreground": "white",
          "background": "royal purple"
        }
      },
      "construction": {
        "seams": "princess seams",
        "stitching": "topstitch",
        "stitching_color": "matching",
        "closure": "exposed center-front zipper"
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
      },
      "prompt_text": "Long sleeve bodycon dress in royal purple jersey...",
      "version": "vd_v1.0.0",
      "source_hash": "abc123..."
    }
  ]
}
```

**Error Responses:**

`401 Unauthorized`

```json
{
  "detail": "Unauthorized"
}
```

`400 Bad Request` - Invalid model or no images in ZIP

```json
{
  "detail": "Invalid model 'invalid_model'. Supported: openai, gemini, blip2, stub"
}
```

```json
{
  "detail": "No valid images found in ZIP file. Found 3 files with extensions: ['.txt', '.pdf']. Supported formats: .jpg, .jpeg, .png, .webp"
}
```

`500 Internal Server Error`

```json
{
  "detail": "Analysis failed: <error message>"
}
```

### GET /healthz

Health check endpoint.

**Request:**

```bash
curl "$VD_BASE_URL/healthz"
```

**Response:** `200 OK`

```json
{
  "status": "ok",
  "model": "gemini",
  "backend": "GeminiVLM"
}
```

### GET /debug

Debug configuration endpoint (shows backend status).

**Request:**

```bash
curl "$VD_BASE_URL/debug"
```

**Response:** `200 OK`

```json
{
  "backend": "GeminiVLM",
  "vd_model_env": "gemini",
  "gemini_key_present": true,
  "openai_key_present": false,
  "api_key_set": true
}
```

### GET /docs

Interactive API documentation (Swagger UI).

**Access:** Navigate to `$VD_BASE_URL/docs` in a browser.

### GET /

Redirects to `/docs`.

---

## Data Schema

### Record Fields

```typescript
{
  // Core identification
  image_id: string
  source_hash: string
  version: string
  
  // Garment info
  garment_type: string | null        // "dress", "jacket", "pants"
  silhouette: string | null          // "bodycon", "A-line", "straight"
  fit_and_drape: string | null       // "structured", "flowy"
  
  // Fabric
  fabric: {
    type: string | null              // "jersey", "denim", "silk"
    texture: string | null           // "smooth", "ribbed"
    weight: string | null            // "light", "medium", "heavy"
    finish: string | null            // "matte", "glossy"
  }
  
  // Garment structure
  garment: {
    top_style: string | null         // "hoodie", "blazer"
    top: string | null               // "shirt", "sweater"
    top_sleeve: string | null        // "long sleeve", "sleeveless"
    bottom: string | null            // "pants", "skirt"
  }
  
  garment_components: {
    top_length: string | null        // "cropped", "hip", "longline"
    bottom_length: string | null     // "mini", "midi", "maxi"
    layers: string[]                 // ["jacket", "shirt"]
  }
  
  // Colors
  color_primary: string | null       // "royal purple"
  color_secondary: string | null     // "white"
  color_palette: string[]            // ["purple", "white"]
  
  colors: {
    primary: string | null
    secondary: string | null
    pattern: {
      type: string | null            // "polka_dot", "stripe"
      foreground: string | null
      background: string | null
    }
  }
  
  // Construction
  construction: {
    seams: string | null             // "princess seams"
    stitching: string | null         // "topstitch"
    stitching_color: string | null   // "matching", "contrast"
    hems: string | null              // "clean finish"
    closure: string | null           // "zipper", "buttons"
    
    top: {
      seams: string | null
      stitching: string | null
      stitching_color: string | null
      hems: string | null
      closure: string | null
    }
    
    bottom: {
      seams: string | null
      stitching: string | null
      stitching_color: string | null
      hems: string | null
      closure: string | null
    }
  }
  
  // Presentation
  pose: string | null                // "standing", "walking"
  photo_style: string | null         // "editorial", "e-commerce"
  
  model: {
    framing: string | null           // "full body", "waist up"
    expression: string | null        // "neutral", "smiling"
    gaze: string | null              // "direct", "away"
  }
  
  camera: {
    view: string | null              // "front", "back", "side"
    multiview: string | null         // "yes", "no"
    views: string | null             // "front, back"
    angle: string | null             // "eye level", "high angle"
  }
  
  environment_lighting: {
    setup: string | null             // "studio softbox"
    mood: string | null              // "bright", "warm"
    background: string | null        // "plain sweep"
  }
  
  // Extras
  footwear: {
    type: string | null              // "sneakers", "heels"
    color: string | null
  }
  
  details: string[]                  // ["zipper", "buttons"]
  
  // Generated text
  prompt_text: string | null         // Human-readable description
  
  // Metadata
  confidence: object                 // Field confidence scores
  photo_metrics: object              // Technical image metrics
}
```

---

## Analysis Passes

Configure via `passes` parameter:

### Pass A - Global Analysis (Required)

* Garment type and silhouette
* Fabric properties
* Color palette and patterns
* Overall composition
* Footwear

**Processing time:** ~1.5–2s

### Pass B - Construction Details (Optional)

* Seam types and placement
* Stitching techniques
* Closure types
* Hem finishes
* Top/bottom separation

**Processing time:** ~1s

### Pass C - Presentation Analysis (Optional)

* Model pose and expression
* Camera angles and views
* Lighting setup and mood
* Background details

**Processing time:** ~0.5–1s

**Recommended:** Use all three passes (`A,B,C`) for complete data.

---

## Authentication

All endpoints (except `/healthz`, `/debug`, `/docs`) require authentication.

**Method:** Bearer token

```bash
curl -H "Authorization: Bearer YOUR_API_KEY" ...
```

**Set via environment:**

```bash
export API_KEY=your_secret_key_here
```

**Generating secure keys:**

```bash
# Random 32-byte key
openssl rand -base64 32

# UUID-based
python -c "import uuid; print(uuid.uuid4())"
```

---

## Rate Limiting

**Gemini (free tier):**

* 15 requests per minute
* 1,500 requests per day
* 1M tokens per minute

**Response on rate limit:** `429 Too Many Requests`

Implement exponential backoff:

```python
import time
from tenacity import retry, wait_exponential, stop_after_attempt

@retry(wait=wait_exponential(min=1, max=60), stop=stop_after_attempt(5))
def call_api(image_path):
    # Your API call here
    pass
```

---

## Error Handling

**Best practices:**

```python
import requests
import os

def analyze_image(image_path, api_key, base_url=None):
    base_url = base_url or os.getenv("VD_BASE_URL", "https://visual-descriptor-me2kgc2t6q-uc.a.run.app")
    try:
        with open(image_path, 'rb') as f:
            response = requests.post(
                f"{base_url}/v1/jobs",
                headers={'Authorization': f'Bearer {api_key}'},
                files={'file': f},
                data={'passes': 'A,B,C'},
                timeout=30
            )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        print("Request timed out")
    except requests.exceptions.HTTPError as e:
        print(f"HTTP error: {e.response.status_code}")
        try:
            print(e.response.json())
        except Exception:
            print(e.response.text)
    except Exception as e:
        print(f"Error: {e}")
```

---

## Examples

### Python

```python
import requests
import os
from pathlib import Path

def analyze_fashion_image(image_path: str, api_key: str, base_url: str | None = None) -> dict:
    """Analyze a fashion image using Visual Descriptor API."""
    base_url = base_url or os.getenv("VD_BASE_URL", "https://visual-descriptor-me2kgc2t6q-uc.a.run.app")
    url = f"{base_url}/v1/jobs"
    headers = {"Authorization": f"Bearer {api_key}"}

    with open(image_path, 'rb') as f:
        files = {'file': f}
        data = {'passes': 'A,B,C'}
        response = requests.post(url, headers=headers, files=files, data=data)
    response.raise_for_status()
    return response.json()

# Usage - Single image
result = analyze_fashion_image('dress.jpg', 'your_api_key')
print(result['records'][0]['prompt_text'])

# Usage - ZIP folder with multiple images
result = analyze_fashion_image('fashion_collection.zip', 'your_api_key')
for record in result['records']:
    print(f"{record['image_id']}: {record['prompt_text']}")
```

### cURL

```bash
# Basic request
curl -X POST "$VD_BASE_URL/v1/jobs" \
  -H "Authorization: Bearer your_api_key" \
  -F "file=@image.jpg" \
  -F "passes=A,B,C"

# Save response to file
curl -X POST "$VD_BASE_URL/v1/jobs" \
  -H "Authorization: Bearer your_api_key" \
  -F "file=@image.jpg" \
  -F "passes=A,B,C" \
  -o response.json

# Batch processing
for img in images/*.jpg; do
  curl -X POST "$VD_BASE_URL/v1/jobs" \
    -H "Authorization: Bearer your_api_key" \
    -F "file=@$img" \
    -F "passes=A,B,C" \
    -o "results/$(basename "$img" .jpg).json"
done
```

### JavaScript/TypeScript (Node)

```typescript
import fs from 'node:fs';
import fetch from 'node-fetch';
import FormData from 'form-data';

const BASE_URL = process.env.VD_BASE_URL || 'https://visual-descriptor-me2kgc2t6q-uc.a.run.app';

export async function analyzeImage(imagePath: string, apiKey: string) {
  const formData = new FormData();
  formData.append('file', fs.createReadStream(imagePath));
  formData.append('passes', 'A,B,C');

  const response = await fetch(`${BASE_URL}/v1/jobs`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${apiKey}` },
    body: formData as any
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`API error ${response.status}: ${text}`);
  }
  return await response.json();
}
```

---

## Performance

| Metric                   | Value             |
| ------------------------ | ----------------- |
| Average latency (Gemini) | 2–4s              |
| Average latency (GPT-4o) | 3–5s              |
| Cold start               | 5–10s (Cloud Run) |
| Recommended timeout      | 30s               |
| Max file size            | 10MB              |

---

## Monitoring

### Prometheus Metrics (if enabled)

```
vd_requests_total
vd_request_duration_seconds
vd_errors_total
vd_active_requests
```

### Logging

All requests logged with:

* Timestamp
* Request ID
* Model used
* Processing time
* Status code

**View logs (Cloud Run):**

```bash
gcloud run services logs read visual-descriptor \
  --region=us-central1 \
  --format=json
```

---

## CORS (if calling from browsers)

If you plan to call the API directly from web apps, enable CORS in your service:

* Allowed origins: your domains (e.g., `https://yourapp.com`)
* Allowed methods: `POST, GET, OPTIONS`
* Allowed headers: `Authorization, Content-Type`

---

**Questions?** [artofesosa@gmail.com](mailto:artofesosa@gmail.com)
