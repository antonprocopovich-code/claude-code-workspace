#!/usr/bin/env python3
"""
Telegram Parser — парсинг постов из публичных каналов конкурентов.
Результат сохраняется в runtime/ для агента Разведчик.

Использование:
  python3 telegram_parser.py @channel1 @channel2 --limit 20 --output runtime/2026-06-18-razvedka-tg.md

Переменные окружения:
  TELEGRAM_API_ID    — API ID из my.telegram.org
  TELEGRAM_API_HASH  — API Hash из my.telegram.org
  TELEGRAM_PHONE     — номер телефона аккаунта (с кодом страны, например +79001234567)
"""

import os
import sys
import argparse
from datetime import datetime, date
from pathlib import Path

try:
    from telethon import TelegramClient
    from telethon.tl.types import MessageReactions
    from telethon.errors import ChannelInvalidError, UsernameNotOccupiedError, UsernameInvalidError
except ImportError:
    print("Ошибка: telethon не установлен — запустите: pip install telethon")
    sys.exit(1)


def get_env(key: str) -> str:
    value = os.environ.get(key)
    if not value:
        print(f"Ошибка: переменная окружения {key} не задана")
        sys.exit(1)
    return value


def count_reactions(reactions) -> int:
    if reactions is None:
        return 0
    if not hasattr(reactions, "results"):
        return 0
    return sum(r.count for r in reactions.results)


def format_post(post_num: int, msg, channel_username: str) -> str:
    dt = msg.date
    date_str = dt.strftime("%d.%m.%Y")
    views = msg.views or 0
    reactions_count = count_reactions(msg.reactions)
    post_url = f"https://t.me/{channel_username.lstrip('@')}/{msg.id}"

    lines = [
        f"### Пост {post_num} — {date_str}",
        f"👁 {views} просмотров | ❤️ {reactions_count} реакций",
        "",
        msg.text.strip(),
        "",
        post_url,
        "",
        "---",
    ]
    return "\n".join(lines)


async def parse_channel(client: TelegramClient, channel: str, limit: int) -> tuple[str, list[str]]:
    username = channel.lstrip("@")
    print(f"Парсинг @{username}...", end=" ", flush=True)

    try:
        entity = await client.get_entity(channel)
    except (ChannelInvalidError, UsernameNotOccupiedError, UsernameInvalidError, ValueError) as e:
        print(f"⚠️  канал не найден: {e}")
        return channel, []
    except Exception as e:
        print(f"⚠️  ошибка при получении канала: {e}")
        return channel, []

    posts = []
    async for msg in client.iter_messages(entity, limit=limit * 3):
        if not msg.text or not msg.text.strip():
            continue
        posts.append(msg)
        if len(posts) >= limit:
            break

    print(f"получено {len(posts)} постов")
    return f"@{username}", posts


async def run(channels: list[str], limit: int, output_path: Path) -> None:
    api_id = int(get_env("TELEGRAM_API_ID"))
    api_hash = get_env("TELEGRAM_API_HASH")
    phone = get_env("TELEGRAM_PHONE")

    session_path = Path(__file__).parent / "content_zavod"

    client = TelegramClient(str(session_path), api_id, api_hash)

    await client.start(
        phone=lambda: phone,
        code_callback=lambda: input("Введите код подтверждения из Telegram: "),
    )

    today = date.today().strftime("%Y-%m-%d")
    sections = [f"# Telegram Разведка — {today}", ""]

    for channel in channels:
        username, posts = await parse_channel(client, channel, limit)

        display_name = username if username.startswith("@") else f"@{username.lstrip('@')}"
        sections.append(f"## {display_name} ({len(posts)} постов)")
        sections.append("")

        if not posts:
            sections.append("_Посты не найдены или канал недоступен._")
            sections.append("")
            sections.append("---")
            sections.append("")
            continue

        for i, msg in enumerate(posts, start=1):
            raw_username = username.lstrip("@")
            sections.append(format_post(i, msg, raw_username))
            sections.append("")

    await client.disconnect()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(sections), encoding="utf-8")
    print(f"\nГотово → {output_path}")


def build_default_output() -> Path:
    today = date.today().strftime("%Y-%m-%d")
    script_dir = Path(__file__).parent
    return script_dir / "runtime" / f"{today}-razvedka-tg.md"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Парсинг постов из публичных Telegram каналов"
    )
    parser.add_argument(
        "channels",
        nargs="+",
        help="Каналы для парсинга (например: @channel1 @channel2)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Сколько последних постов брать из каждого канала (по умолчанию: 20)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Путь к выходному файлу (по умолчанию: runtime/YYYY-MM-DD-razvedka-tg.md)",
    )
    args = parser.parse_args()

    output_path = Path(args.output) if args.output else build_default_output()
    if not output_path.is_absolute():
        output_path = Path(__file__).parent / output_path

    import asyncio
    asyncio.run(run(args.channels, args.limit, output_path))


if __name__ == "__main__":
    main()
