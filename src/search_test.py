# -*- coding: utf-8 -*-
"""
search_test.py — проверка семантического поиска (серверный Qdrant).

Запуск:
  python search_test.py "текст запроса"
"""

import sys
import requests
from qdrant_client import QdrantClient

import config

TOP_K = 5


def embed(text: str) -> list[float]:
    resp = requests.post(
        f"{config.OLLAMA_HOST}/api/embed",
        json={"model": config.OLLAMA_MODEL, "input": text},
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()["embeddings"][0]


def main():
    if len(sys.argv) < 2:
        print('Использование: python search_test.py "текст запроса"')
        sys.exit(1)

    query = " ".join(sys.argv[1:])
    print(f"Запрос: {query}\n")

    client = QdrantClient(host=config.QDRANT_HOST, port=config.QDRANT_PORT, api_key=config.QDRANT_API_KEY or None, https=config.QDRANT_HTTPS, check_compatibility=False)
    vec = embed(query)

    results = client.query_points(
        collection_name=config.COLLECTION,
        query=vec,
        limit=TOP_K,
    ).points

    if not results:
        print("Ничего не найдено.")
        return

    for i, r in enumerate(results, 1):
        p = r.payload
        score = r.score
        if p["chunk_type"] == "metadata":
            print(f"{i}. [{score:.3f}] ОБЪЕКТ: {p['object_type']}.{p['object_name']}  ({p['synonym']})")
            print(f"     {p['file_path']}")
        else:
            print(f"{i}. [{score:.3f}] КОД: {p['kind']} {p['procedure_name']}  "
                  f"в {p['object_type']}.{p['object_name']} ({p['module_kind']})")
            print(f"     {p['file_path']}")
        print()


if __name__ == "__main__":
    main()
