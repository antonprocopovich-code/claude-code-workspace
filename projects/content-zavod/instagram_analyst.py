#!/usr/bin/env python3
"""
Instagram Analyst — сбор и анализ метрик Instagram.

Использование:
  python3 instagram_analyst.py own                           # свой аккаунт (Graph API)
  python3 instagram_analyst.py competitor @username [N]      # публичный профиль (instaloader)
  python3 instagram_analyst.py compare @user1 @user2 ...    # сравнение нескольких профилей

Переменные окружения (только для режима own):
  INSTAGRAM_ACCESS_TOKEN  — токен Instagram Graph API
  INSTAGRAM_ACCOUNT_ID    — ID бизнес-аккаунта

Установка зависимости для competitor/compare:
  pip install instaloader
"""

import os
import sys
import json
import urllib.request
from datetime import datetime

GRAPH_API = "https://graph.facebook.com/v19.0"

BENCHMARKS = {
    "weak": 1.0,
    "avg": 3.0,
    "good": 6.0,
}


# ── Режим 1: свой аккаунт через Graph API ────────────────────────────────────

def fetch_own(account_id: str, token: str, limit: int = 20) -> dict:
    account = _graph(
        f"{account_id}?fields=username,followers_count,follows_count,media_count&access_token={token}"
    )
    media = _graph(
        f"{account_id}/media"
        f"?fields=media_type,like_count,comments_count,timestamp,caption"
        f"&limit={limit}&access_token={token}"
    )
    return _analyze(account, media.get("data", []), mode="own")


# ── Режим 2: публичный профиль через instaloader ─────────────────────────────

def fetch_competitor(username: str, limit: int = 12) -> dict:
    try:
        import instaloader
    except ImportError:
        return {"error": "instaloader не установлен — запустите: pip install instaloader"}

    L = instaloader.Instaloader(
        download_pictures=False,
        download_videos=False,
        download_comments=False,
        save_metadata=False,
        quiet=True,
    )
    try:
        profile = instaloader.Profile.from_username(L.context, username.lstrip("@"))
    except Exception as e:
        return {"error": str(e)}

    account = {
        "username": profile.username,
        "followers_count": profile.followers,
        "follows_count": profile.followees,
        "media_count": profile.mediacount,
    }
    posts = []
    for i, post in enumerate(profile.get_posts()):
        if i >= limit:
            break
        posts.append({
            "media_type": (
                "VIDEO" if post.is_video
                else "CAROUSEL_ALBUM" if post.typename == "GraphSidecar"
                else "IMAGE"
            ),
            "like_count": post.likes,
            "comments_count": post.comments,
            "timestamp": post.date_utc.isoformat(),
            "caption": (post.caption or "")[:100],
        })
    return _analyze(account, posts, mode="competitor")


# ── Общий анализ ─────────────────────────────────────────────────────────────

def _analyze(account: dict, posts: list, mode: str) -> dict:
    followers = account.get("followers_count", 1)

    format_er: dict[str, list] = {"IMAGE": [], "VIDEO": [], "CAROUSEL_ALBUM": []}
    er_list = []

    for p in posts:
        engagement = p.get("like_count", 0) + p.get("comments_count", 0)
        er = round(engagement / followers * 100, 2)
        er_list.append(er)
        fmt = p.get("media_type", "IMAGE")
        if fmt in format_er:
            format_er[fmt].append(er)

    avg_er = round(sum(er_list) / len(er_list), 2) if er_list else 0

    fmt_avg = {k: round(sum(v) / len(v), 2) if v else 0 for k, v in format_er.items()}
    top_format = max(fmt_avg, key=fmt_avg.get) if any(fmt_avg.values()) else "—"

    if avg_er >= BENCHMARKS["good"]:
        grade = "отличный"
    elif avg_er >= BENCHMARKS["avg"]:
        grade = "хороший"
    elif avg_er >= BENCHMARKS["weak"]:
        grade = "средний"
    else:
        grade = "слабый"

    top3 = sorted(
        posts,
        key=lambda p: p.get("like_count", 0) + p.get("comments_count", 0),
        reverse=True,
    )[:3]

    return {
        "mode": mode,
        "account": account.get("username", ""),
        "followers": followers,
        "following": account.get("follows_count", 0),
        "posts_total": account.get("media_count", 0),
        "posts_analyzed": len(posts),
        "avg_er": avg_er,
        "er_grade": grade,
        "benchmark": {
            "weak": f"<{BENCHMARKS['weak']}%",
            "avg": f"{BENCHMARKS['avg']}%",
            "good": f">{BENCHMARKS['good']}%",
        },
        "format_er": fmt_avg,
        "top_format": top_format,
        "top_posts": [
            {
                "type": p.get("media_type"),
                "likes": p.get("like_count", 0),
                "comments": p.get("comments_count", 0),
                "caption": (p.get("caption") or "")[:80],
            }
            for p in top3
        ],
        "fetched_at": datetime.utcnow().isoformat(),
    }


def _graph(path: str) -> dict:
    with urllib.request.urlopen(f"{GRAPH_API}/{path}", timeout=15) as r:
        return json.loads(r.read().decode())


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    args = sys.argv[1:]

    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0)

    mode = args[0]

    if mode == "own":
        token = os.environ.get("INSTAGRAM_ACCESS_TOKEN")
        acct  = os.environ.get("INSTAGRAM_ACCOUNT_ID")
        if not token or not acct:
            print(json.dumps({"error": "Нужны INSTAGRAM_ACCESS_TOKEN и INSTAGRAM_ACCOUNT_ID"}))
            sys.exit(1)
        result = fetch_own(acct, token)

    elif mode == "competitor":
        if len(args) < 2:
            print(json.dumps({"error": "Укажите username: competitor @username [N]"}))
            sys.exit(1)
        limit = int(args[2]) if len(args) > 2 else 12
        result = fetch_competitor(args[1], limit)

    elif mode == "compare":
        if len(args) < 2:
            print(json.dumps({"error": "Укажите хотя бы один @username"}))
            sys.exit(1)
        result = {"comparison": [fetch_competitor(u) for u in args[1:]]}

    else:
        result = {"error": f"Неизвестный режим '{mode}'. Доступны: own, competitor, compare"}

    print(json.dumps(result, ensure_ascii=False, indent=2))
