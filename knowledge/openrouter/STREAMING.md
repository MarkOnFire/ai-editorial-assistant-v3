# OpenRouter Streaming Guide

**Scraped:** December 2024
**Source:** https://openrouter.ai/docs/api/reference/streaming

---

## Enabling Streaming

Set `stream: true` in your request:

```python
response = client.chat.completions.create(
    model="openai/gpt-4o",
    messages=[{"role": "user", "content": "Hello!"}],
    stream=True
)

for chunk in response:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
```

---

## Server-Sent Events (SSE) Format

Responses arrive as SSE chunks. OpenRouter occasionally sends comments like `: OPENROUTER PROCESSING` to prevent connection timeouts—these are safe to ignore per SSE specifications.

### Chunk Structure

```json
{
  "id": "gen-xxx",
  "object": "chat.completion.chunk",
  "created": 1234567890,
  "model": "openai/gpt-4o",
  "choices": [{
    "index": 0,
    "delta": {
      "content": "Hello"
    },
    "finish_reason": null
  }]
}
```

### Final Chunk

```json
{
  "choices": [{
    "index": 0,
    "delta": {},
    "finish_reason": "stop"
  }],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 50,
    "total_tokens": 60
  }
}
```

---

## Including Usage in Stream

```python
response = client.chat.completions.create(
    model="openai/gpt-4o",
    messages=[...],
    stream=True,
    stream_options={"include_usage": True}
)
```

Usage data appears in the final chunk.

---

## Delta Handling

Extract content from each chunk:

```python
for chunk in response:
    content = chunk.choices[0].delta.content
    if content:
        print(content, end="", flush=True)
```

### Raw SSE Processing

```python
import requests

response = requests.post(
    "https://openrouter.ai/api/v1/chat/completions",
    headers={"Authorization": f"Bearer {api_key}"},
    json={"model": "openai/gpt-4o", "messages": [...], "stream": True},
    stream=True
)

for line in response.iter_lines():
    if line:
        line = line.decode('utf-8')
        if line.startswith('data: '):
            data = line[6:]
            if data == '[DONE]':
                break
            chunk = json.loads(data)
            content = chunk['choices'][0]['delta'].get('content', '')
            print(content, end='')
```

---

## Stream Cancellation

Use AbortController (or equivalent) to cancel streams:

```python
# Python with httpx
import httpx

async with httpx.AsyncClient() as client:
    async with client.stream(
        "POST",
        "https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={"model": "openai/gpt-4o", "messages": [...], "stream": True}
    ) as response:
        async for chunk in response.aiter_lines():
            # Process chunk
            if should_cancel:
                break  # Stream will be cancelled
```

### Provider Support for Cancellation

| Supported | Not Supported |
|-----------|---------------|
| OpenAI | Groq |
| Anthropic | Google |
| Cohere | Mistral |

---

## Error Handling During Streams

### Pre-Stream Errors
Standard JSON error response with HTTP status (400, 401, 402, 429, 502, 503).

### Mid-Stream Errors
Error appears as SSE event:

```json
{
  "error": {"code": 500, "message": "Provider error"},
  "choices": [{
    "delta": {"content": ""},
    "finish_reason": "error"
  }]
}
```

**Note:** HTTP status remains 200 OK since headers already transmitted.

### Handling Both Scenarios

```python
def stream_with_error_handling(client, **kwargs):
    try:
        response = client.chat.completions.create(stream=True, **kwargs)
        full_content = ""

        for chunk in response:
            # Check for mid-stream error
            if hasattr(chunk, 'error') and chunk.error:
                raise Exception(f"Stream error: {chunk.error.message}")

            # Check finish reason
            if chunk.choices[0].finish_reason == 'error':
                raise Exception("Stream ended with error")

            content = chunk.choices[0].delta.content
            if content:
                full_content += content
                print(content, end="", flush=True)

        return full_content

    except Exception as e:
        # Handle pre-stream errors
        print(f"Error: {e}")
        raise
```

---

## Streaming with Tools

Tool calls are also streamed:

```python
for chunk in response:
    delta = chunk.choices[0].delta

    if delta.tool_calls:
        for tool_call in delta.tool_calls:
            # Accumulate tool call arguments
            if tool_call.function.arguments:
                # Arguments come in chunks
                pass

    if delta.content:
        print(delta.content, end="")
```

---

## Debug Mode with Streaming

```python
response = client.chat.completions.create(
    model="openai/gpt-4o",
    messages=[...],
    stream=True,
    extra_body={
        "debug": {"echo_upstream_body": True}
    }
)

for chunk in response:
    # First chunk contains debug info
    if hasattr(chunk, 'debug'):
        print("Debug:", chunk.debug)
    # Subsequent chunks contain content
    elif chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
```
