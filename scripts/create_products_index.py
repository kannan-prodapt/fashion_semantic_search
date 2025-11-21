from scripts.opensearch_client2 import get_opensearch_client

INDEX_NAME = "products"


def main():
    client = get_opensearch_client()

    # Optional: drop existing index if you want a clean start
    if client.indices.exists(INDEX_NAME):
        print(f"Deleting existing index {INDEX_NAME}...")
        client.indices.delete(INDEX_NAME)

    body = {
        "settings": {
            "index": {
                "knn": True
            }
        },
        "mappings": {
            "properties": {
                "product_id":    {"type": "keyword"},
                "title":         {"type": "text"},
                "description":   {"type": "text"},
                "main_category": {"type": "keyword"},
                "price":         {"type": "float"},
                "embedding": {
                    "type": "knn_vector",
                    "dimension": 1536,  # matches text-embedding-ada-002
                    "method": {
                        "name": "hnsw",
                        "engine": "lucene",
                        "space_type": "l2"
                    }
                }
            }
        }
    }

    resp = client.indices.create(index=INDEX_NAME, body=body)
    print("CREATE INDEX RESPONSE:", resp)


if __name__ == "__main__":
    main()
