#!/usr/bin/env python3
"""
Мост для вызова DeepSeek V4 через OpenRouter API.

Использование:
  python3 deepseek_call.py "твой промпт"
  python3 deepseek_call.py --stdin            # промпт из stdin
  python3 deepseek_call.py --file prompt.txt  # промпт из файла
  python3 deepseek_call.py --system sys.txt --file user.txt  # раздельно

Импорт:
  from deepseek_call import ask_deepseek
"""

import os
import sys
import json
import urllib.request
import urllib.error

API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "deepseek/deepseek-v4-pro"
DEFAULT_MAX_TOKENS = 8000


def ask_deepseek(prompt: str, system: str = "", max_tokens: int = DEFAULT_MAX_TOKENS) -> str:
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("Переменная OPENROUTER_API_KEY не задана")

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    payload = json.dumps({
        "model": MODEL,
        "messages": messages,
        "max_tokens": max_tokens,
    }).encode()

    req = urllib.request.Request(
        API_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://content-zavod.local",
            "X-Title": "Content Zavod",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode())
            msg = data["choices"][0]["message"]
            content = msg.get("content") or msg.get("reasoning") or ""
            if not content:
                raise RuntimeError(f"Пустой ответ от модели. Полный ответ: {data}")
            return content.strip()
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        raise RuntimeError(f"OpenRouter ошибка {e.code}: {body}")


if __name__ == "__main__":
    args = sys.argv[1:]

    system_text = ""
    user_text = ""

    i = 0
    while i < len(args):
        if args[i] == "--stdin":
            user_text = sys.stdin.read()
            i += 1
        elif args[i] == "--file" and i + 1 < len(args):
            with open(args[i + 1]) as f:
                user_text = f.read()
            i += 2
        elif args[i] == "--system" and i + 1 < len(args):
            with open(args[i + 1]) as f:
                system_text = f.read()
            i += 2
        else:
            user_text = " ".join(args[i:])
            break

    if not user_text:
        print("Использование: python3 deepseek_call.py 'промпт'")
        print("               python3 deepseek_call.py --stdin")
        print("               python3 deepseek_call.py --file prompt.txt")
        print("               python3 deepseek_call.py --system sys.txt --file user.txt")
        sys.exit(1)

    print("Отправляю запрос в DeepSeek...\n", file=sys.stderr)
    result = ask_deepseek(user_text, system=system_text)
    print(result)
