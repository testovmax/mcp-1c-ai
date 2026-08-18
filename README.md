# mcp-1c-ai

MCP-сервер семантического поиска по конфигурации 1С для Claude Code.

Позволяет Claude Code искать объекты метаданных (справочники, документы, регистры) и процедуры по смыслу запроса, а не по точному совпадению названий. Под капотом: эмбеддинги через Ollama (`qwen3-embedding`) и векторная база Qdrant с проиндексированной конфигурацией (10500+ файлов).

## Инструменты MCP

- `search_config(query, limit)` — семантический поиск по конфигурации: «проведение реализации», «расчёт себестоимости» и т.п.
- `get_code(procedure_name, object_name)` — полный исходный код процедуры или функции по имени.

## Требования

- Python 3.10+
- Запущенный сервер Ollama с моделью `qwen3-embedding` (см. `OLLAMA_HOST` в `src/config.py`)
- Запущенный Qdrant с готовым индексом — коллекция `rep_1c` (см. `QDRANT_HOST` в `src/config.py`)

## Установка

```bash
pip install -r requirements.txt
copy .env.example .env   # и впиши QDRANT_API_KEY
```

Проверка связи с серверами:

```bash
python src/check_connection.py
```

Проверка поиска из консоли:

```bash
python src/search_test.py "проведение реализации"
```

## Подключение к Claude Code

Сервер уже описан в `.mcp.json` (project scope) — Claude Code, открытый в папке проекта, подхватит его автоматически. Либо вручную:

```bash
claude mcp add --scope project 1c-search -- python C:\1c-ai\mcp-1c-ai\src\mcp_server.py
```

## Структура

```
src/
  mcp_server.py        # MCP-сервер (FastMCP): search_config, get_code
  config.py            # общие настройки: адреса Ollama/Qdrant, прокси, .env
  check_connection.py  # быстрая проверка связи с Ollama и Qdrant
  search_test.py       # проверка поиска из консоли
CLAUDE.md              # правила работы Claude Code в проекте
.mcp.json              # регистрация MCP-сервера (project scope)
.env.example           # шаблон секретов (QDRANT_API_KEY)
```

## Секреты

API-ключ Qdrant хранится только в `.env` (в git не попадает). Скопируй `.env.example` → `.env` и впиши ключ.
