# -*- coding: utf-8 -*-
"""
mcp_server.py — MCP-сервер семантического поиска по конфигурации 1С.

Инструменты для Claude Code:
  - search_config: поиск объектов и процедур по смыслу
  - get_code: получить полный код найденной процедуры

Подключение:
  claude mcp add --scope project 1c-search -- python C:\\1c-ai\\mcp-1c-ai\\src\\mcp_server.py

Требует:
  - запущенный Ollama
  - запущенный Qdrant (Docker)
  - готовый индекс (см. indexer.py)
"""

import requests
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from mcp.server.fastmcp import FastMCP

import config

mcp = FastMCP("1c-search")

_client = None


def get_client() -> QdrantClient:
    global _client
    if _client is None:
        _client = QdrantClient(host=config.QDRANT_HOST, port=config.QDRANT_PORT, api_key=config.QDRANT_API_KEY or None, https=config.QDRANT_HTTPS, check_compatibility=False)
    return _client


def embed(text: str) -> list[float]:
    resp = requests.post(
        f"{config.OLLAMA_HOST}/api/embed",
        json={"model": config.OLLAMA_MODEL, "input": text},
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()["embeddings"][0]


@mcp.tool()
def search_config(query: str, limit: int = 8) -> str:
    """Семантический поиск по конфигурации 1С.

    Ищет объекты метаданных (справочники, документы, регистры) и процедуры
    по смыслу запроса, а не по точному совпадению названий.

    Args:
        query: запрос на естественном языке, например
               "проведение реализации" или "расчёт себестоимости".
        limit: сколько результатов вернуть (по умолчанию 8).

    Returns:
        Форматированный список найденных объектов и процедур.
    """
    try:
        vec = embed(query)
    except Exception as e:
        return f"Ошибка при обращении к Ollama: {e}"

    try:
        results = get_client().query_points(
            collection_name=config.COLLECTION,
            query=vec,
            limit=limit,
        ).points
    except Exception as e:
        return f"Ошибка при поиске в Qdrant: {e}"

    if not results:
        return "Ничего не найдено."

    lines = [f"Найдено по запросу «{query}»:\n"]
    for i, r in enumerate(results, 1):
        p = r.payload
        score = r.score
        if p["chunk_type"] == "metadata":
            lines.append(
                f"{i}. [{score:.3f}] ОБЪЕКТ: {p['object_type']}.{p['object_name']}"
                f" — {p['synonym']}\n   Файл: {p['file_path']}"
            )
        else:
            lines.append(
                f"{i}. [{score:.3f}] {p['kind']} {p['procedure_name']}"
                f" в {p['object_type']}.{p['object_name']} ({p['module_kind']})"
                f"\n   Файл: {p['file_path']}"
            )
    return "\n".join(lines)


@mcp.tool()
def get_code(procedure_name: str, object_name: str = "") -> str:
    """Получить полный исходный код процедуры или функции по имени.

    Args:
        procedure_name: имя процедуры или функции.
        object_name: имя объекта-владельца для уточнения (можно опустить).

    Returns:
        Исходный код процедуры или сообщение, что она не найдена.
    """
    try:
        conditions = [
            FieldCondition(key="chunk_type", match=MatchValue(value="procedure")),
            FieldCondition(key="procedure_name", match=MatchValue(value=procedure_name)),
        ]
        if object_name:
            conditions.append(
                FieldCondition(key="object_name", match=MatchValue(value=object_name))
            )

        records, _ = get_client().scroll(
            collection_name=config.COLLECTION,
            scroll_filter=Filter(must=conditions),
            limit=10,
            with_payload=True,
        )
    except Exception as e:
        return f"Ошибка при поиске кода: {e}"

    if not records:
        return f"Процедура «{procedure_name}» не найдена в индексе."

    out = []
    for rec in records:
        p = rec.payload
        out.append(
            f"// {p['object_type']}.{p['object_name']} ({p['module_kind']})\n"
            f"// Файл: {p['file_path']}\n\n{p['code']}"
        )
    return "\n\n" + ("\n\n" + "─" * 60 + "\n\n").join(out)


if __name__ == "__main__":
    mcp.run()
