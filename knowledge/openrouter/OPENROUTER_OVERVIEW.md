# OpenRouter Documentation

**Scraped:** December 2024
**Source:** https://openrouter.ai/docs

---

## What is OpenRouter?

OpenRouter provides unified API access to 500+ AI models from 60+ providers through a single endpoint. It automatically handles fallbacks and selects cost-effective options.

**Primary endpoint:** `https://openrouter.ai/api/v1/chat/completions`

---

## Quickstart

### Installation Options

**OpenRouter SDK (TypeScript):**
```bash
npm install @openrouter/sdk
```

**Python (OpenAI SDK compatible):**
```python
from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="<OPENROUTER_API_KEY>"
)

response = client.chat.completions.create(
    model="openai/gpt-4o",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

### Authentication

- API key passed as `Authorization: Bearer <OPENROUTER_API_KEY>`
- Optional headers for app attribution:
  - `HTTP-Referer`: Your site URL (for leaderboard rankings)
  - `X-Title`: Your application name

---

## Pricing

### Platform Fees
- **5.5% fee** (minimum $0.80) when purchasing credits (non-crypto)
- **5% flat** for crypto payments
- **No markup** on underlying provider pricing - you pay the same rate as direct

### BYOK (Bring Your Own Key)
- Route traffic using your own provider API keys
- OpenRouter charges 5% usage fee on underlying provider cost

### Per-Token Pricing
- Pricing per million tokens (varies by model)
- Separate rates for input (prompt) and output (completion) tokens
- Output typically costs 2-5x more than input
- Some models charge per-request or for images/reasoning tokens

### Rate Limits
| Tier | Limits |
|------|--------|
| Free | 50 requests/day, 20 requests/minute |
| Pay-as-you-go | No platform limits |
| Enterprise | No platform limits |

### Cost Optimization
- Opt-in prompt/completion logging for **1% discount** on usage costs
- Credits expire after one year

---

## Provider Routing (Key Feature)

### Automatic Fallback Behavior
- If a provider returns an error, OpenRouter automatically falls back to the next provider
- Transparent to the user - enables production app resilience
- Handles 5xx responses and rate limits automatically

### Default Load Balancing Strategy
1. Prioritize providers with no significant outages in last 30 seconds
2. Among stable providers, select lowest-cost candidates weighted by inverse square of price
3. Use remaining providers as fallbacks

### Custom Provider Routing

```python
response = client.chat.completions.create(
    model="openai/gpt-4o",
    messages=[...],
    extra_body={
        "provider": {
            "order": ["Azure", "OpenAI"],  # Prioritize these in order
            "allow_fallbacks": True  # Still allow fallbacks to other providers
        }
    }
)
```

### Disabling Fallbacks
To guarantee only top (lowest-cost) provider:
```python
extra_body={
    "provider": {
        "allow_fallbacks": False
    }
}
```

### Manual Fallback Chains
```python
extra_body={
    "models": ["openai/gpt-4o", "anthropic/claude-3-opus", "google/gemini-pro"]
}
```
- Tries primary model first
- Falls back to next models if unavailable/rate-limited/blocked
- `response.model` shows which model actually responded

---

## Structured Outputs

### JSON Mode
```python
response_format={"type": "json_object"}
```
Guarantees valid JSON output.

### JSON Schema Mode
```python
response_format={
    "type": "json_schema",
    "json_schema": {
        "name": "my_schema",
        "schema": {...}
    }
}
```
Constrains output to match your schema.

### Model Compatibility
- Supported: OpenAI 4o, Fireworks models
- More providers coming soon
- Check model listing for Structured Outputs support

### Streaming with Structured Outputs
```python
stream=True
```
Streams valid partial JSON that forms valid response when complete.

---

## Tool Calling

### Format
Follows OpenAI's tool calling request shape. Transformed for non-OpenAI providers.

### Tool Choice Options
| Value | Behavior |
|-------|----------|
| `"none"` | Model will not call any tool |
| `"auto"` | Model can pick between message or tool call |
| `"required"` | Model must call one or more tools |
| `{"type": "function", "function": {"name": "my_function"}}` | Forces specific tool |

### Parallel Tool Calls
Can be toggled on/off (2025 feature).

---

## Key Features Summary

| Feature | Description |
|---------|-------------|
| **Provider Routing** | Automatic load balancing and fallback |
| **Model Fallbacks** | Define fallback chains across models |
| **Structured Outputs** | JSON Schema enforcement |
| **Tool Calling** | OpenAI-compatible function calling |
| **Streaming** | SSE streaming with all features |
| **BYOK** | Use your own API keys with 5% fee |
| **Prompt Caching** | Cost reduction for repeated prompts |
| **Zero Data Retention** | Privacy controls available |
| **Message Transforms** | Context optimization |
| **Plugins** | Web search, PDF processing, response healing |

---

## Integration Options

### Native SDKs
- TypeScript SDK
- Python SDK

### OpenAI SDK Compatible
Works as drop-in replacement by changing base URL.

### Community Integrations
- LangChain (Python/JavaScript)
- Vercel AI SDK (Next.js)
- PydanticAI (Python)
- LangSmith / Langfuse
- Mastra framework
- LiveKit voice agents
- Zapier (8000+ apps)

### Observability
- Langfuse integration
- LangSmith integration
- Datadog integration
- Braintrust integration
- Weights & Biases Weave

---

## Model Variants

| Variant | Purpose |
|---------|---------|
| **free** | Free tier access |
| **extended** | Extended context |
| **exacto** | Exact matching |
| **thinking** | Chain of thought |
| **online** | Internet access |
| **nitro** | Low latency |

---

## Best Practices

1. **Validate failover** - Configure fallback chain and test during off-peak hours
2. **Monitor costs** - Use activity export (CSV/PDF) for reporting
3. **Use user tracking** - Sub-user reporting for multi-tenant apps
4. **Implement streaming** - Better UX and lower perceived latency
5. **Check model support** - Verify features (structured outputs, tools) per model
