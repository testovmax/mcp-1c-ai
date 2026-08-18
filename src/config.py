# -*- coding: utf-8 -*-
"""
config.py — общие настройки для всех скриптов системы.
Меняешь тут — меняется везде (indexer, mcp_server, search_test).

ПРОД-ВЕРСИЯ: серверная схема (RDP-виртуалка + ollama-1 + qdrant-1).
"""
from pathlib import Path
import os as _os

# ── Загрузка секретов из .env (корень проекта) ───────────────────────────────
# Файл .env в git не попадает. Скопируй .env.example → .env и впиши ключ.
def _load_dotenv(path: Path) -> None:
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        if key and key not in _os.environ:
            _os.environ[key] = value

_load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# ── Ollama (сервер эмбеддингов) ──────────────────────────────────────────────
# Отдельный сервер ollama-1 (172.20.0.17). Модель :latest, вектор 4096.
OLLAMA_HOST = "http://172.20.0.17:11434"   # IP надёжнее DNS-имени ollama-1
OLLAMA_MODEL = "qwen3-embedding:latest"
VECTOR_SIZE = 4096                       # размерность вектора серверной модели
                                         # (проверено запросом /api/embed)

# ── Qdrant (векторная база, отдельный сервер) ────────────────────────────────
# Полное имя надёжнее короткого (короткое qdrant-1 не всегда резолвится).
QDRANT_HOST = "172.20.0.144"               # IP надёжнее qdrant-1.5s.local
QDRANT_PORT = 6333
COLLECTION = "rep_1c"

# API-ключ Qdrant: только из переменной окружения / файла .env (не в git).
QDRANT_API_KEY = _os.environ.get("QDRANT_API_KEY", "")
QDRANT_HTTPS = False   # сервер слушает обычный HTTP на 6333

# ── Индексация ───────────────────────────────────────────────────────────────
EMBED_BATCH = 8         # сколько текстов отправлять в Ollama за один запрос
UPSERT_BATCH = 64       # сколько точек грузить в Qdrant за раз

# ── Прокси: умная маршрутизация ──────────────────────────────────────────────
# Корпоративный SOCKS5-прокси нужен только для выхода в «дальний» интернет
# (Claude API и т.п.). Напрямую, мимо прокси, ходят:
#   1) внутренние серверы (ollama-1, qdrant-1) — иначе запросы падают;
#   2) российские зоны и сервисы (.ru/.su/.by/.рф + CDN на не-ru доменах).
# Формат NO_PROXY — суффиксы: ".ru" матчит любой хост *.ru.
_internal = "ollama-1,qdrant-1,qdrant-1.5s.local,172.20.0.17,172.20.0.144,localhost,127.0.0.1"
_russia = (".ru,.su,.by,.рф,.xn--p1ai,"
           "vk.com,.vk.com,.userapi.com,.vkuservideo.net,.vkuseraudio.net,"
           ".mycdn.me,.yandex.net,.yastatic.net,.yandex.com,"
           "sberbank.com,.sberbank.com,.ozonusercontent.com,.wbstatic.net,.2gis.com")
_existing = _os.environ.get("NO_PROXY", "")
_os.environ["NO_PROXY"] = (_existing + "," + _internal + "," + _russia).strip(",")
_os.environ["no_proxy"] = _os.environ["NO_PROXY"]
