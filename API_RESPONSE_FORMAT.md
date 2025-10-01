# API Response Format Guide

## 🎯 Best Practice: Include Both JSON + prompt_text

The API now returns **both structured JSON AND a human-readable prompt_text field** in every response.

## 📊 Response Structure

```json
{
  "job_id": "j_abc12345",
  "status": "completed",
  "backend": "GeminiVLM",
  "model": "gemini",
  "records": [
    {
      "image_id": "purple_dress_001",
      "garment_type": "bodycon dress",
      "silhouette": "sheath",
      
      "fabric": {
        "type": "ponte jersey",
        "texture": "smooth",
        "weight": "medium",
        "finish": "matte"
      },
      
      "garment": {
        "top_style": null,
        "top": null,
        "top_sleeve": "long sleeve",
        "bottom": null
      },
      
      "garment_components": {
        "top_length": null,
        "bottom_length": "midi",
        "layers": []
      },
      
      "colors": {
        "primary": "royal purple",
        "secondary": null,
        "pattern": {
          "type": "polka_dot",
          "foreground": "white",
          "background": "royal purple",
          "ratio_foreground": 0.15,
          "orientation": "n/a"
        }
      },
      
      "construction": {
        "seams": "princess seams",
        "stitching": "topstitch",
        "stitching_color": "white",
        "hems": "clean finish",
        "closure": "exposed zipper",
        "top": {
          "seams": "princess panel seams",
          "stitching": "contrast topstitch",
          "stitching_color": "white",
          "hems": "clean finish",
          "closure": "exposed center-front zipper"
        },
        "bottom": null
      },
      
      "fit_and_drape": "structured, bodycon",
      "pose": "standing, facing camera",
      
      "model": {
        "framing": "full body",
        "expression": "confident",
        "gaze": "direct to camera"
      },
      
      "camera": {
        "view": "front",
        "multiview": "no",
        "views": null,
        "angle": "eye level"
      },
      
      "environment_lighting": {
        "setup": "studio softbox",
        "mood": "bright and clean",
        "background": "plain white sweep"
      },
      
      "photo_style": "editorial",
      "footwear": {
        "type": null,
        "color": null
      },
      
      "details": [
        "white contrast stitching",
        "exposed zipper with ring pull"
      ],
      
      "color_palette": ["royal purple"],
      "confidence": {},
      "version": "vd_v1.0.0",
      
      "prompt_text": "bodycon dress, long sleeve, midi — ponte jersey, smooth, medium-weight, matte — sheath silhouette, structured fit — Colors: royal purple, white polka dots || Details: white contrast stitching, exposed zipper with ring pull || Construction: top: white contrast topstitch, princess panel seams, clean finish hems, exposed center-front zipper || Photo: standing, facing camera, full body, confident expression, gaze direct to camera, front view, eye level angle, studio softbox, bright and clean mood, bg: plain white sweep, editorial"
    }
  ]
}
```

## 🎯 Use Cases

### 1. Quick Display / UI
```javascript
// Show human-readable summary
response.records.forEach(record => {
  console.log(record.prompt_text);
  // "bodycon dress, long sleeve — ponte jersey, smooth..."
});
```

### 2. Database Storage
```python
# Store structured data for filtering/searching
db.garments.insert({
    'image_id': record['image_id'],
    'fabric_type': record['fabric']['type'],
    'color': record['colors']['primary'],
    'garment_type': record['garment_type'],
    'full_data': record,  # Store complete JSON
    'prompt_text': record['prompt_text']  # For full-text search
})

# Later: search by fabric
results = db.garments.find({'fabric_type': 'jersey'})

# Or: full-text search
results = db.garments.find({'$text': {'$search': 'polka dots'}})
```

### 3. AI Training Dataset
```python
# Create training pairs for text-to-image models
training_data = []
for record in response['records']:
    training_data.append({
        'image': f"images/{record['image_id']}.jpg",
        'caption': record['prompt_text'],  # Rich description
        'metadata': {
            'fabric': record['fabric'],
            'colors': record['colors'],
            'construction': record['construction']
        }
    })
```

### 4. E-commerce Product Page
```html
<!-- Quick description from prompt_text -->
<div class="product-summary">
  {{ record.prompt_text }}
</div>

<!-- Detailed specs from JSON -->
<table class="product-specs">
  <tr>
    <td>Fabric:</td>
    <td>{{ record.fabric.type }}, {{ record.fabric.texture }}</td>
  </tr>
  <tr>
    <td>Weight:</td>
    <td>{{ record.fabric.weight }}</td>
  </tr>
  <tr>
    <td>Color:</td>
    <td>{{ record.colors.primary }}</td>
  </tr>
  <tr>
    <td>Pattern:</td>
    <td>{{ record.colors.pattern.foreground }} {{ record.colors.pattern.type }}</td>
  </tr>
</table>
```

### 5. Search & Filtering
```python
# Filter by specific attributes (use JSON)
def search_garments(fabric_type=None, color=None, pattern=None):
    results = []
    for record in all_records:
        if fabric_type and record['fabric']['type'] != fabric_type:
            continue
        if color and record['colors']['primary'] != color:
            continue
        if pattern and record['colors'].get('pattern', {}).get('type') != pattern:
            continue
        results.append(record)
    return results

# Full-text search (use prompt_text)
def search_text(query):
    return [r for r in all_records if query.lower() in r['prompt_text'].lower()]
```

### 6. Product Recommendations
```python
# Find similar items based on fabric and style
def find_similar(target_record):
    similar = []
    target_fabric = target_record['fabric']['type']
    target_silhouette = target_record['silhouette']
    
    for record in all_records:
        if record['fabric']['type'] == target_fabric:
            if record['silhouette'] == target_silhouette:
                similar.append(record)
    
    return similar
```

## 🔧 Implementation Details

### Engine Automatically Adds prompt_text

The `engine.py` now automatically generates `prompt_text` after analysis:

```python
# In engine.describe_image():
output = r.model_dump(mode="python", exclude_none=False)

# Generate and add prompt_text
from .export_csv_prompt import prompt_line
output["prompt_text"] = prompt_line(output)

return output
```

### Schema Update Required

Add to `schema.py` Record class:

```python
class Record(BaseModel):
    # ... existing fields ...
    
    prompt_text: Optional[str] = None  # Human-readable description
    
    version: Optional[str] = None
    source_hash: Optional[str] = None
```

## 📋 Comparison

### JSON Only (Old Approach)
```json
{
  "garment_type": "dress",
  "fabric": {"type": "jersey"},
  "colors": {"primary": "purple"}
}
```

**Problems:**
- ❌ Need to parse and format for display
- ❌ Hard to use for AI training
- ❌ Not human-readable at a glance
- ❌ Requires code to generate descriptions

### JSON + prompt_text (New Approach)
```json
{
  "garment_type": "bodycon dress",
  "fabric": {"type": "ponte jersey", "texture": "smooth", "weight": "medium"},
  "colors": {"primary": "royal purple", "pattern": {"type": "polka_dot"}},
  "prompt_text": "bodycon dress — ponte jersey, smooth, medium-weight — royal purple, white polka dots"
}
```

**Benefits:**
- ✅ Structured data for filtering/searching
- ✅ Human-readable text ready to use
- ✅ Perfect for AI training
- ✅ Best of both worlds

## 🚀 Example API Calls

### Basic Request
```bash
curl -X POST http://localhost:8000/v1/jobs \
  -H "Authorization: Bearer your_api_key" \
  -F "file=@dress.jpg" \
  -F "passes=A,B,C"
```

### Response (Abbreviated)
```json
{
  "job_id": "j_abc123",
  "status": "completed",
  "records": [{
    "image_id": "dress",
    "fabric": {"type": "jersey", "texture": "smooth"},
    "colors": {"primary": "purple"},
    "prompt_text": "dress — jersey, smooth — purple"
  }]
}
```

### Using the Response
```python
import requests

response = requests.post(
    'http://localhost:8000/v1/jobs',
    headers={'Authorization': 'Bearer your_key'},
    files={'file': open('dress.jpg', 'rb')},
    data={'passes': 'A,B,C'}
)

data = response.json()
record = data['records'][0]

# Get structured data
fabric_type = record['fabric']['type']  # "jersey"
color = record['colors']['primary']     # "purple"

# Get human-readable text
description = record['prompt_text']
# "dress — jersey, smooth — purple"

# Use for AI training
training_pair = {
    'image': 'dress.jpg',
    'caption': description
}
```

## 💡 Pro Tips

### 1. Cache Both Formats
```python
# Store both in your database
db.save({
    'id': record['image_id'],
    'structured': record,  # Full JSON for queries
    'text': record['prompt_text']  # For display/search
})
```

### 2. Generate Variants
```python
# Create different text formats from JSON
def short_description(record):
    return f"{record['garment_type']} in {record['colors']['primary']}"

def detailed_description(record):
    return record['prompt_text']

def seo_description(record):
    fabric = record['fabric']
    return f"{fabric['type']} {record['garment_type']}, {fabric['weight']}-weight"
```

### 3. Multilingual Support
```python
# Translate prompt_text for international markets
from translate import Translator

def translate_description(record, target_lang):
    translator = Translator(to_lang=target_lang)
    return translator.translate(record['prompt_text'])
```

## ✅ Summary

**Include both JSON and prompt_text because:**

1. **JSON** = structured, queryable, type-safe
2. **prompt_text** = readable, ready-to-use, AI-friendly
3. **Together** = maximum flexibility for any use case

**Response format:**
```
JSON {
  ... all structured fields ...
  "prompt_text": "comprehensive human-readable description"
}
```

This gives you the best of both worlds! 🎉
