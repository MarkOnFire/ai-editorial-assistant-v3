# OpenRouter Error Handling & Debugging

**Scraped:** December 2024
**Source:** https://openrouter.ai/docs/api/reference/errors-and-debugging

---

## Error Response Structure

```json
{
  "error": {
    "code": 400,
    "message": "Error description",
    "metadata": {}
  }
}
```

HTTP status code matches the error code, except when LLM processing has begun—then responses return 200 OK with error details in the body or SSE events.

---

## HTTP Error Codes

| Code | Meaning | Common Causes |
|------|---------|---------------|
| **400** | Bad Request | Invalid/missing parameters, CORS issues |
| **401** | Unauthorized | Expired OAuth, disabled/invalid API key |
| **402** | Payment Required | Insufficient account credits |
| **403** | Forbidden | Input flagged by moderation |
| **408** | Timeout | Request timeout |
| **429** | Too Many Requests | Rate limiting active |
| **502** | Bad Gateway | Model provider down or invalid response |
| **503** | Service Unavailable | No provider matching requirements |

---

## Specialized Error Metadata

### Moderation Errors (403)

```json
{
  "error": {
    "code": 403,
    "message": "Content flagged by moderation",
    "metadata": {
      "reasons": ["violence", "explicit"],
      "flagged_input": "The specific text that...",
      "provider_name": "OpenAI",
      "model_slug": "gpt-4o"
    }
  }
}
```

- `flagged_input` is truncated to 100 characters with "..."

### Provider Errors (502)

```json
{
  "error": {
    "code": 502,
    "message": "Provider error",
    "metadata": {
      "provider_name": "Anthropic",
      "raw": { "original": "error details" }
    }
  }
}
```

---

## Streaming Error Handling

### Pre-Stream Errors
Standard JSON error response with appropriate HTTP status code.

### Mid-Stream Errors
Sent as SSE events with `finish_reason: 'error'`:

```json
{
  "error": {"code": "string | number", "message": "Error description"},
  "choices": [{
    "delta": {"content": ""},
    "finish_reason": "error"
  }]
}
```

**Note:** HTTP status remains 200 OK since headers already transmitted.

### Error Transformations (Responses API)
Certain errors transform to success responses:

| Error | Becomes |
|-------|---------|
| `context_length_exceeded` | `finish_reason: "length"` |
| `max_tokens_exceeded` | `finish_reason: "length"` |
| `token_limit_exceeded` | `finish_reason: "length"` |
| `string_too_long` | `finish_reason: "length"` |

---

## Rate Limits

### Checking Your Limits

```bash
curl https://openrouter.ai/api/v1/key \
  -H "Authorization: Bearer $OPENROUTER_API_KEY"
```

Response includes:
- Credit limits (overall and remaining)
- Usage tracking (all-time, daily, weekly, monthly)
- BYOK usage tracking
- Account status (free tier qualification)

### Limit Tiers

| Tier | Limits |
|------|--------|
| **Free** | 50 requests/day, 20 requests/minute |
| **Purchased 10+ credits** | 1,000+ `:free` model requests/day |
| **Pay-as-you-go** | No platform limits |
| **Enterprise** | No platform limits |

### Important Notes

- Rate limits apply **globally**—multiple accounts/keys don't increase capacity
- Different models have different rate limits—distribute load across models
- Negative credit balance triggers 402 errors even for free models
- Cloudflare DDoS protection blocks dramatically excessive requests

---

## Debugging

### Echo Upstream Body

See the exact request sent to the provider:

```python
response = client.chat.completions.create(
    model="openai/gpt-4o",
    messages=[...],
    stream=True,  # Required!
    extra_body={
        "debug": {
            "echo_upstream_body": True
        }
    }
)
```

**Requirements:**
- Only works with `stream: True`
- Only for Chat Completions API

**Output:** Debug chunk arrives as first response event:

```json
{
  "choices": [],
  "debug": {
    "echo_upstream_body": {
      "system": [...],
      "messages": [...],
      "model": "...",
      "stream": true
    }
  }
}
```

### Debug Use Cases

- Observe parameter transformations across providers
- Verify message formatting and system prompt handling
- Identify default values applied automatically
- Track provider fallback attempts (separate chunks per provider)

### Restrictions

- **Development only**—avoid production use
- May expose sensitive information in request data
- Non-streaming and Responses API requests ignore this parameter

---

## No-Content Scenarios

Models occasionally produce no output during:
- Cold start warm-up phases
- System scaling operations

**Solutions:**
1. Implement retry mechanism
2. Test alternate providers
3. Note: Prompt processing costs may still apply

---

## Retry Strategy

```python
import time
from openai import OpenAI

def call_with_retry(client, max_retries=3, **kwargs):
    for attempt in range(max_retries):
        try:
            return client.chat.completions.create(**kwargs)
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            if hasattr(e, 'status_code'):
                if e.status_code == 429:
                    time.sleep(2 ** attempt)  # Exponential backoff
                elif e.status_code >= 500:
                    time.sleep(1)
                else:
                    raise
    return None
```
