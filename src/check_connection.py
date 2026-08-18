# -*- coding: utf-8 -*-
"""Быстрая проверка связи с серверами Ollama и Qdrant. Запуск: python check_connection.py"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config
import requests

ok = True

# Ollama: реальный эмбеддинг (первый вызов может грузить модель до минуты)
try:
    r = requests.post(config.OLLAMA_HOST + "/api/embed",
                      json={"model": config.OLLAMA_MODEL, "input": "test"}, timeout=90)
    if r.status_code == 200 and r.json().get("embeddings"):
        size = len(r.json()["embeddings"][0])
        print(f"[OK] Ollama {config.OLLAMA_HOST} - embeddings work, vector size {size}")
        if size != config.VECTOR_SIZE:
            print(f"[!!] Vector size {size} != VECTOR_SIZE {config.VECTOR_SIZE} in config.py")
            ok = False
    else:
        print(f"[FAIL] Ollama answered {r.status_code}: {r.text[:200]}")
        ok = False
except Exception as e:
    print(f"[FAIL] Ollama {config.OLLAMA_HOST} unreachable: {e}")
    ok = False

# Qdrant: коллекция и число точек
if not config.QDRANT_API_KEY:
    print("[FAIL] Qdrant auth — QDRANT_API_KEY пустой. Скопируй .env.example → .env и впиши ключ.")
    ok = False
else:
    try:
        r = requests.get(f"http://{config.QDRANT_HOST}:{config.QDRANT_PORT}/collections/{config.COLLECTION}",
                         headers={"api-key": config.QDRANT_API_KEY}, timeout=10)
        if r.status_code == 200:
            pts = r.json()["result"].get("points_count", "?")
            print(f"[OK] Qdrant {config.QDRANT_HOST} - collection '{config.COLLECTION}', points: {pts}")
        elif r.status_code in (401, 403):
            print(f"[FAIL] Qdrant auth error - check QDRANT_API_KEY in .env")
            ok = False
        else:
            print(f"[FAIL] Qdrant answered {r.status_code}: {r.text[:200]}")
            ok = False
    except Exception as e:
        print(f"[FAIL] Qdrant {config.QDRANT_HOST} unreachable: {e}")
        ok = False

print()
print("ALL GOOD - agent is ready to use" if ok else "PROBLEMS FOUND - see lines above")
sys.exit(0 if ok else 1)
