import os, json
import threading
from typing import Dict, Any

import openai

from prompts.schema_prompts import SCHEMA_DESCRIPTION

OPENAI_MODEL = "gpt-4o-mini"
openai.api_key = os.getenv("OPENAI_API_KEY")

QUERY_CACHE: Dict[str, Any] = {}
CACHE_LOCK = threading.Lock()


def normalize_query(q: str) -> str:
    return " ".join(q.strip().lower().split())


def call_llm_for_filters(user_query: str) -> Dict[str, Any]:
    response = openai.ChatCompletion.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": SCHEMA_DESCRIPTION},
            {"role": "user", "content": user_query},
        ],
    )
    content = response["choices"][0]["message"]["content"]
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return {}


def llm_filters_cached(query: str) -> Dict[str, Any]:
    key = normalize_query(query)

    with CACHE_LOCK:
        if key in QUERY_CACHE:
            print(f"[CACHE HIT] query='{key}'")
            return QUERY_CACHE[key]

    print(f"[CACHE MISS] query='{key}' → calling LLM")
    filters = call_llm_for_filters(query)

    with CACHE_LOCK:
        QUERY_CACHE[key] = filters

    return filters
