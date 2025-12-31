# OpenRouter API Parameters Reference

**Scraped:** December 2024
**Source:** https://openrouter.ai/docs/api/reference/parameters

---

## Endpoint

**POST** `https://openrouter.ai/api/v1/chat/completions`

---

## Sampling Parameters

### Temperature
- **Key:** `temperature`
- **Type:** float
- **Range:** 0.0 to 2.0
- **Default:** 1.0
- **Purpose:** Influences variety in model responses. Lower values = more predictable; higher values = more diverse. At 0, always returns the same response for a given input.

### Top P (Nucleus Sampling)
- **Key:** `top_p`
- **Type:** float
- **Range:** 0.0 to 1.0
- **Default:** 1.0
- **Purpose:** Restricts token selection to cumulative probability threshold. Lower values reduce unpredictability.

### Top K
- **Key:** `top_k`
- **Type:** integer
- **Range:** 0 or above
- **Default:** 0 (disabled)
- **Purpose:** Limits model's token choices at each step to a smaller set.

### Min P
- **Key:** `min_p`
- **Type:** float
- **Range:** 0.0 to 1.0
- **Default:** 0.0
- **Purpose:** Establishes minimum probability threshold relative to the most likely token.

### Top A
- **Key:** `top_a`
- **Type:** float
- **Range:** 0.0 to 1.0
- **Default:** 0.0
- **Purpose:** Dynamic filtering based on maximum probability tokens with sufficient confidence.

### Seed
- **Key:** `seed`
- **Type:** integer
- **Purpose:** Enables deterministic sampling. Repeated requests with same seed and parameters should return same result. Note: Determinism not guaranteed for all models.

---

## Repetition Control

### Frequency Penalty
- **Key:** `frequency_penalty`
- **Type:** float
- **Range:** -2.0 to 2.0
- **Default:** 0.0
- **Purpose:** Controls token repetition based on input frequency. Negative values encourage reuse.

### Presence Penalty
- **Key:** `presence_penalty`
- **Type:** float
- **Range:** -2.0 to 2.0
- **Default:** 0.0
- **Purpose:** Adjusts how often the model repeats specific tokens already used in the input.

### Repetition Penalty
- **Key:** `repetition_penalty`
- **Type:** float
- **Range:** 0.0 to 2.0
- **Default:** 1.0
- **Purpose:** Reduces input token repetition without scaling by occurrence frequency.

---

## Output Control

### Max Tokens
- **Key:** `max_tokens`
- **Type:** integer
- **Minimum:** 1
- **Purpose:** Sets upper generation limit. Cannot exceed context length minus prompt length.

### Stop Sequences
- **Key:** `stop`
- **Type:** array of strings
- **Purpose:** Terminates generation upon encountering specified tokens.

### Verbosity
- **Key:** `verbosity`
- **Type:** enum (`low`, `medium`, `high`)
- **Default:** `medium`
- **Purpose:** Controls the verbosity and length of the model response.

---

## Structured Output

### Response Format
- **Key:** `response_format`
- **Type:** object
- **Example:** `{ "type": "json_object" }`
- **Purpose:** Forces specific output format. Enables JSON mode guaranteeing valid JSON output.

```python
response_format={"type": "json_object"}
```

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

### Structured Outputs
- **Key:** `structured_outputs`
- **Type:** boolean
- **Purpose:** Enables structured outputs using JSON schema format when supported.

---

## Tool Calling

### Tools
- **Key:** `tools`
- **Type:** array
- **Purpose:** Tool calling parameter, following OpenAI's tool calling request shape. Transformed for non-OpenAI providers.

### Tool Choice
- **Key:** `tool_choice`
- **Type:** string or object
- **Options:**
  - `"none"` - Model will not call any tool
  - `"auto"` - Model can pick between message or tool call
  - `"required"` - Model must call one or more tools
  - `{"type": "function", "function": {"name": "my_function"}}` - Forces specific tool

### Parallel Tool Calls
- **Key:** `parallel_tool_calls`
- **Type:** boolean
- **Default:** true
- **Purpose:** Determines whether multiple functions execute simultaneously or sequentially.

---

## Token Probability

### Logit Bias
- **Key:** `logit_bias`
- **Type:** JSON object (token_id → bias)
- **Value Range:** -100 to 100
- **Purpose:** Adjusts token selection probabilities before sampling. Values -1 to 1 decrease/increase likelihood; -100 or 100 result in ban/exclusive selection.

### Logprobs
- **Key:** `logprobs`
- **Type:** boolean
- **Purpose:** Returns log probabilities for each output token when enabled.

### Top Logprobs
- **Key:** `top_logprobs`
- **Type:** integer
- **Range:** 0 to 20
- **Requirement:** Requires `logprobs: true`
- **Purpose:** Returns the specified number of most probable tokens with associated probabilities.

---

## OpenRouter-Specific Parameters

### Transforms
- **Key:** `transforms`
- **Type:** array of strings
- **Default:** `["middle-out"]`
- **Purpose:** Apply transformations to prompt before sending to model.
- **Available:** `"middle-out"` - Compresses prompts/message chains to fit context size

```python
# Disable transforms
extra_body={"transforms": []}
```

### Provider Routing
```python
extra_body={
    "provider": {
        "order": ["Azure", "OpenAI"],  # Priority order
        "allow_fallbacks": True  # Allow fallbacks to other providers
    }
}
```

### Model Fallbacks
```python
extra_body={
    "models": ["openai/gpt-4o", "anthropic/claude-3-opus", "google/gemini-pro"]
}
```

### User Identifier
- **Key:** `user`
- **Type:** string
- **Purpose:** Identifier for sub-user tracking in multi-tenant apps.

### Debug
```python
extra_body={
    "debug": {
        "echo_upstream_body": True  # Only works with stream: True
    }
}
```

---

## Parameter Support Notes

- If a model doesn't support a parameter (e.g., `logit_bias` in non-OpenAI models, `top_k` for OpenAI), the parameter is **ignored**
- Provider-specific parameters (e.g., `safe_prompt` for Mistral, `raw_mode` for Hyperbolic) are passed directly to providers
- Check the model's provider section to confirm which parameters are supported
