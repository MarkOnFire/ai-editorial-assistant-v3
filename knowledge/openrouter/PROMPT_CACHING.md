# OpenRouter Prompt Caching Guide

**Scraped:** December 2024
**Source:** https://openrouter.ai/docs/guides/best-practices/prompt-caching

---

## Overview

Prompt caching reduces inference costs by reusing previously processed prompts. Most providers handle caching automatically, though some (like Anthropic) require per-message configuration.

---

## Provider-Specific Implementation

### OpenAI

| Aspect | Details |
|--------|---------|
| **Setup** | Fully automated, no configuration needed |
| **Minimum Tokens** | 1,024 tokens required |
| **Cache Write Cost** | Free |
| **Cache Read Cost** | 0.25x-0.50x standard input pricing |

### Anthropic Claude

| Aspect | Details |
|--------|---------|
| **Setup** | Requires manual `cache_control` breakpoints |
| **Maximum Breakpoints** | 4 per request |
| **TTL** | 5 minutes |
| **Cache Write Cost** | ~1.25x standard cost |
| **Cache Read Cost** | ~0.1x standard cost |

**Implementation:**
```json
{
  "content": [
    {"type": "text", "text": "initial prompt"},
    {
      "type": "text",
      "text": "LARGE CONTENT TO CACHE (datasets, character cards, etc.)",
      "cache_control": {"type": "ephemeral"}
    },
    {"type": "text", "text": "follow-up query"}
  ]
}
```

**Best Practices for Anthropic:**
- Reserve breakpoints for substantial content (datasets, character cards, extracted text)
- Breakpoints only work with multipart text content
- Place cacheable content early in the message

### Google Gemini

| Aspect | Details |
|--------|---------|
| **Setup** | Automatic (implicit caching) for 2.5 Pro/Flash |
| **TTL** | 3-5 minutes (variable) |
| **Cache Write Cost** | Free (no storage costs) |
| **Cache Read Cost** | 0.25x input pricing |
| **Min Tokens (2.5 Flash)** | 1,028 tokens |
| **Min Tokens (2.5 Pro)** | 2,048 tokens |

**Note:** Optional explicit `cache_control` breakpoints supported; only final breakpoint used.

### DeepSeek

| Aspect | Details |
|--------|---------|
| **Setup** | Fully automated |
| **Cache Write Cost** | Standard input cost |
| **Cache Read Cost** | ~0.1x standard cost |

### Other Providers

| Provider | Setup | Cache Read Cost |
|----------|-------|-----------------|
| **Grok** | Automated | ~0.25x |
| **Moonshot AI** | Automated | Discounted |
| **Groq** (Kimi K2) | Automated | Discounted |

---

## Best Practices for Cache Hits

1. **Keep initial message portion consistent** between requests
2. **Push variations to the end** (user questions, dynamic context)
3. **Structure prompts strategically:**
   - System prompt (static) → first
   - Reference materials (static) → middle
   - User query (dynamic) → last

```python
messages = [
    {"role": "system", "content": "Your static system prompt..."},
    {"role": "user", "content": "Large static context/documents..."},
    {"role": "user", "content": "Dynamic user question"}  # Only this changes
]
```

---

## Provider Routing with Caching

OpenRouter makes a best-effort to continue routing to the same provider to utilize warm caches. If the cached provider is unavailable, it falls back to the next-best provider.

---

## Tracking Cache Usage

### Via API Request
```python
response = client.chat.completions.create(
    model="openai/gpt-4o",
    messages=[...],
    extra_body={
        "usage": {"include": True}
    }
)
```

The response includes:
- `cache_discount`: How much the response saved on cache usage
- Cache token counts in the usage object

### Via Dashboard
- Activity page detail view shows cache savings
- `/api/v1/generation?id=$GENERATION_ID` endpoint provides detailed usage

---

## Cost Calculation Example

For a request with 10,000 input tokens at $0.01/1K tokens:

| Scenario | Cost |
|----------|------|
| No caching | $0.10 |
| OpenAI cache hit (0.5x) | $0.05 |
| Anthropic cache hit (0.1x) | $0.01 |
| Gemini cache hit (0.25x) | $0.025 |
