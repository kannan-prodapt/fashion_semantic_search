import os
import json
import openai

from scripts.opensearch_client2 import get_opensearch_client

OPENAI_EMBED_MODEL = "text-embedding-ada-002"
openai.api_key = os.getenv("OPENAI_API_KEY")

INDEX_NAME = "products"


def get_query_embedding(text: str):
    resp = openai.Embedding.create(
        model=OPENAI_EMBED_MODEL,
        input=text,
    )
    return resp["data"][0]["embedding"]


def main():
    client = get_opensearch_client()

    query_text = "sporty men's socks for running under 800"
    print("Query:", query_text)

    vec = get_query_embedding(query_text)

    body = {
        "size": 10,
        "query": {
            "knn": {
                "embedding": {
                    "vector": vec,
                    "k": 10
                }
            }
        }
    }

    resp = client.search(index=INDEX_NAME, body=body)
    print(json.dumps(resp, indent=2)[:2000])

    print("\nTop hits:")
    for hit in resp["hits"]["hits"]:
        src = hit["_source"]
        print(f"- id={src.get('product_id')} score={hit.get('_score'):.3f} title={src.get('title')}")


if __name__ == "__main__":
    main()
