---
name: llm-integration
description: Patterns for integrating LLMs (OpenAI, Gemini) for relevance filtering and summarization.
---

# LLM Integration

## Core Libraries
- **OpenAI**: For GPT-4o / GPT-3.5 access.
- **Google Generative AI**: For Gemini Pro access.
- **LiteLLM** (Recommended): Unified interface for multiple providers.

## Pattern: Structured Output (Pydantic)
Always request structured JSON output for decision-making agents (Relevance, Guardrail).

Using `openai` > 1.0:
```python
from pydantic import BaseModel
from openai import OpenAI

client = OpenAI()

class RelevanceDecision(BaseModel):
    is_relevant: bool
    confidence: float
    reason: str

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": "You are a relevance classifier..."},
        {"role": "user", "content": content_text}
    ],
    response_format={"type": "json_object"} # or use tools/functions for strict schema
)
# Parse JSON manually or use instructor/client wrappers
```

## Pattern: Summarization
For summarization, use a specialized system prompt.
```python
SYSTEM_PROMPT = """
You are an expert tech summarizer.
Summarize the following text into 3-5 bullet points.
Ensure factual accuracy.
"""

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": content_text}
    ]
)
summary = response.choices[0].message.content
```

## Error Handling
- Use retry logic with exponential backoff (`tenacity` library).
- Handle `RateLimitError` and `APIConnectionError`.
