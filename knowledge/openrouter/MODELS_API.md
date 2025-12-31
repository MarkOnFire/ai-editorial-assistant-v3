# OpenRouter Models API

**Scraped:** December 2024
**Source:** https://openrouter.ai/docs/guides/overview/models

---

## Accessing Models

| Method | URL |
|--------|-----|
| **Browse** | https://openrouter.ai/models |
| **API** | `GET /api/v1/models` |
| **RSS** | Subscribe for new model updates |

---

## List Models Endpoint

```bash
curl https://openrouter.ai/api/v1/models \
  -H "Authorization: Bearer $OPENROUTER_API_KEY"
```

### Python Example

```python
import requests

response = requests.get(
    "https://openrouter.ai/api/v1/models",
    headers={"Authorization": f"Bearer {api_key}"}
)
models = response.json()["data"]

# Filter by capability
text_models = [m for m in models if "text" in m.get("architecture", {}).get("modality", "")]
```

---

## Model Object Schema

```json
{
  "id": "google/gemini-2.5-pro-preview",
  "canonical_slug": "google/gemini-2.5-pro-preview",
  "name": "Gemini 2.5 Pro Preview",
  "created": 1700000000,
  "description": "Advanced reasoning model with...",
  "context_length": 1000000,
  "architecture": {
    "modality": "text+image->text",
    "tokenizer": "Gemini",
    "instruct_type": "gemini"
  },
  "pricing": {
    "prompt": "0.00000125",
    "completion": "0.00000500",
    "request": "0",
    "image": "0.00265"
  },
  "top_provider": {
    "context_length": 1000000,
    "max_completion_tokens": 8192
  },
  "supported_parameters": [
    "temperature",
    "top_p",
    "top_k",
    "max_tokens",
    "tools",
    "tool_choice"
  ]
}
```

---

## Core Model Properties

| Property | Description |
|----------|-------------|
| **id** | Unique identifier for API requests (e.g., `openai/gpt-4o`) |
| **canonical_slug** | Permanent, unchanging slug reference |
| **name** | Human-readable display name |
| **created** | Unix timestamp of addition to platform |
| **description** | Capabilities and characteristics overview |
| **context_length** | Maximum context window in tokens |

---

## Architecture Details

```json
{
  "architecture": {
    "modality": "text+image->text",
    "tokenizer": "GPT",
    "instruct_type": "openai"
  }
}
```

| Field | Description |
|-------|-------------|
| **modality** | Input/output types (text, image, file) |
| **tokenizer** | Tokenization method used |
| **instruct_type** | Instruction format type |

### Common Modalities

- `text->text` - Text only
- `text+image->text` - Multimodal input, text output
- `text->text+image` - Text input, can generate images

---

## Pricing Structure

All prices in USD per token/request/unit:

```json
{
  "pricing": {
    "prompt": "0.00000250",      // Per input token
    "completion": "0.00001000",  // Per output token
    "request": "0",              // Per request
    "image": "0.00265",          // Per image
    "web_search": "0.004",       // Per search
    "reasoning": "0.00001500",   // Per reasoning token
    "input_cache_read": "0.00000125",   // Cached input
    "input_cache_write": "0.00000315"   // Cache write
  }
}
```

---

## Model Variants

Append variant suffix to model ID:

| Variant | Purpose | Example |
|---------|---------|---------|
| `:free` | Free tier access | `meta-llama/llama-3-8b:free` |
| `:extended` | Extended context | `anthropic/claude-3-opus:extended` |
| `:online` | Web search enabled | `openai/gpt-4o:online` |
| `:thinking` | Chain of thought | `anthropic/claude-3-5-sonnet:thinking` |
| `:nitro` | Low latency | `meta-llama/llama-3-70b:nitro` |

---

## Querying Specific Model

```bash
curl "https://openrouter.ai/api/v1/models/openai/gpt-4o" \
  -H "Authorization: Bearer $OPENROUTER_API_KEY"
```

---

## Get Supported Parameters

```bash
curl "https://openrouter.ai/api/v1/parameters?model=openai/gpt-4o" \
  -H "Authorization: Bearer $OPENROUTER_API_KEY"
```

Returns:
- Which parameters the model supports
- Parameter popularity/usage statistics

---

## Filtering Models

### By Provider

```python
openai_models = [m for m in models if m["id"].startswith("openai/")]
anthropic_models = [m for m in models if m["id"].startswith("anthropic/")]
google_models = [m for m in models if m["id"].startswith("google/")]
```

### By Context Length

```python
long_context = [m for m in models if m["context_length"] >= 100000]
```

### By Pricing

```python
# Free models
free_models = [m for m in models if float(m["pricing"]["prompt"]) == 0]

# Sort by prompt cost
sorted_by_cost = sorted(models, key=lambda m: float(m["pricing"]["prompt"]))
```

### By Capability

```python
# Models with tool calling
tool_capable = [m for m in models if "tools" in m.get("supported_parameters", [])]

# Multimodal models
multimodal = [m for m in models if "image" in m.get("architecture", {}).get("modality", "")]
```

---

## Model Selection Example

```python
def find_best_model(models, requirements):
    """Find cheapest model meeting requirements."""
    candidates = models

    if requirements.get("min_context"):
        candidates = [m for m in candidates
                     if m["context_length"] >= requirements["min_context"]]

    if requirements.get("multimodal"):
        candidates = [m for m in candidates
                     if "image" in m.get("architecture", {}).get("modality", "")]

    if requirements.get("tools"):
        candidates = [m for m in candidates
                     if "tools" in m.get("supported_parameters", [])]

    # Sort by prompt cost
    candidates.sort(key=lambda m: float(m["pricing"]["prompt"]))

    return candidates[0] if candidates else None
```
