# OpenRouter Plugins Guide

**Scraped:** December 2024
**Source:** https://openrouter.ai/docs/guides/features/plugins/overview

---

## Available Plugins

| Plugin ID | Name | Purpose |
|-----------|------|---------|
| `web` | Web Search | Augment LLM responses with real-time web search results |
| `pdf` | PDF Inputs | Parse and extract content from uploaded PDF files |
| `response-healing` | Response Healing | Automatically fix malformed JSON responses from LLMs |

---

## Enabling Plugins via API

Add a `plugins` array to your chat completions request:

```python
response = client.chat.completions.create(
    model="openai/gpt-4o",
    messages=[...],
    extra_body={
        "plugins": [{"id": "web"}]
    }
)
```

### Multiple Plugins with Configuration

```python
extra_body={
    "plugins": [
        {"id": "web", "max_results": 3},
        {"id": "response-healing"}
    ]
}
```

---

## Web Search Plugin

### Quick Enable via Model Suffix

Append `:online` to any model ID:

```python
model="openai/gpt-4o:online"
# Equivalent to:
model="openai/gpt-4o" + plugins=[{"id": "web"}]
```

### Search Engines

| Engine | Details |
|--------|---------|
| **Native** | Used for Anthropic, OpenAI, Perplexity, xAI models |
| **Exa** | Fallback engine, charges $4 per 1,000 results |

### Configuration Options

```python
plugins=[{
    "id": "web",
    "max_results": 5,       # Default: 5, affects Exa cost
    "engine": "exa"         # Optional: force specific engine
}]
```

### Pricing (Exa)
- $4 per 1,000 results
- Default 5 results = max $0.02 per request
- Uses your OpenRouter credits

---

## PDF Plugin

Enables processing of PDF file content in your prompts.

```python
plugins=[{"id": "pdf"}]
```

---

## Response Healing Plugin

Automatically repairs malformed JSON in LLM responses—useful when using `response_format: {"type": "json_object"}`.

```python
plugins=[{"id": "response-healing"}]
```

---

## Default Settings vs Request-Level

### Priority Order
1. **Request-level** configurations override defaults
2. **Account defaults** apply when plugins aren't specified
3. **Prevent overrides** (admin setting) forces account settings

### Disabling Defaults Per-Request

```python
extra_body={
    "plugins": [{"id": "web", "enabled": False}]
}
```

### Setting Account Defaults
Configure via **Settings > Plugins** dashboard (admins only in organizations).

---

## Use Cases

### Real-Time Information
```python
# Get current information with web search
response = client.chat.completions.create(
    model="anthropic/claude-3-5-sonnet:online",
    messages=[{
        "role": "user",
        "content": "What are the latest developments in AI this week?"
    }]
)
```

### Reliable JSON Output
```python
# Ensure valid JSON even from models that sometimes fail
response = client.chat.completions.create(
    model="openai/gpt-4o",
    messages=[...],
    response_format={"type": "json_object"},
    extra_body={
        "plugins": [{"id": "response-healing"}]
    }
)
```

### Document Processing
```python
# Process PDF content
response = client.chat.completions.create(
    model="openai/gpt-4o",
    messages=[{
        "role": "user",
        "content": "Summarize this PDF: [pdf_content]"
    }],
    extra_body={
        "plugins": [{"id": "pdf"}]
    }
)
```
