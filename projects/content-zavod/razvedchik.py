#!/usr/bin/env python3
"""
Разведчик — агент мониторинга конкурентов.
Отправляет запрос параллельно в Claude Opus 4.8 и DeepSeek V4 Pro через OpenRouter.
Использование: python3 razvedchik.py "что исследовать"
"""

import os
import sys
import json
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed

API_URL = "https://openrouter.ai/api/v1/chat/completions"

MODELS = {
    "Claude Opus 4.8": "anthropic/claude-opus-4.8",
    "DeepSeek V4 Pro": "deepseek/deepseek-v4-pro",
}

SYSTEM_PROMPT = """Ты — Разведчик, агент мониторинга конкурентного поля личного бренда.
Твоя задача: анализировать конкурентов, выявлять вирусные форматы, тренды и механики.

Отвечай строго по шаблону:
🔍 Объект анализа: [что анализируешь]
📌 Ключевые находки: [2-3 главных наблюдения]
📊 Тренды: [что сейчас работает в нише]
💡 Механики и приёмы: [конкретные техники]
🎯 Как применить: [3 конкретные идеи для личного бренда]"""


def call_model(model_name: str, model_id: str, prompt: str) -> tuple[str, str]:
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY не задана")

    payload = json.dumps({
        "model": model_id,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": 2000,
    }).encode()

    req = urllib.request.Request(
        API_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://content-zavod.local",
            "X-Title": "Content Zavod - Razvedchik",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            return model_name, data["choices"][0]["message"]["content"].strip()
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        return model_name, f"ОШИБКА {e.code}: {body}"


def scout(prompt: str) -> dict[str, str]:
    results = {}
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = {
            executor.submit(call_model, name, model_id, prompt): name
            for name, model_id in MODELS.items()
        }
        for future in as_completed(futures):
            name, response = future.result()
            results[name] = response
    return results


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python3 razvedchik.py 'что исследовать'")
        print("Пример: python3 razvedchik.py 'топ блогеры по теме продуктивность в Telegram'")
        sys.exit(1)

    prompt = " ".join(sys.argv[1:])
    print(f"Разведчик запущен. Запрос к двум агентам параллельно...\n{'='*60}\n")

    results = scout(prompt)

    for model_name, response in results.items():
        print(f"{'='*60}")
        print(f"  {model_name}")
        print(f"{'='*60}")
        print(response)
        print()
