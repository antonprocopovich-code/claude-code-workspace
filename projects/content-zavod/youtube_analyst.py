#!/usr/bin/env python3
"""
YouTube Analyst — транскрибация и анализ YouTube-видео.

Режимы:
  python3 youtube_analyst.py transcript <url>       # получить транскрипцию
  python3 youtube_analyst.py analyze <url>          # транскрипция + AI-анализ (DeepSeek)
  python3 youtube_analyst.py channel <url> [N=5]    # анализ N последних видео канала

Зависимости:
  pip install youtube-transcript-api        # основной путь (авто-субтитры)
  pip install yt-dlp                        # fallback: скачивание аудио
  brew install whisper-cpp                  # fallback: локальная транскрипция
  whisper-cpp --download-model base         # скачать модель (~150 MB)

Переменные окружения:
  OPENROUTER_API_KEY — для AI-анализа через deepseek_call.py
"""

import os
import sys
import json
import re
import subprocess
import tempfile
from pathlib import Path

DEEPSEEK = Path(__file__).parent / "deepseek_call.py"

ANALYZE_PROMPT = """\
Проанализируй транскрипцию YouTube-видео. Верни ТОЛЬКО JSON, без markdown и пояснений.

Транскрипция:
{transcript}

Структура JSON:
{{
  "content_type": "обучающий|продающий|вовлекающий|личный|развлекательный",
  "hook": "зацепка первых 15–30 секунд (1–2 предложения)",
  "main_thesis": "главный тезис в 1 предложении",
  "key_points": ["пункт 1", "пункт 2", "пункт 3"],
  "cta": "призыв к действию (пусто если нет)",
  "content_pillars": ["смысловой столп 1", "столп 2"],
  "tone": "формальный|разговорный|экспертный|вдохновляющий|провокационный",
  "viral_mechanics": ["механика 1 если есть"],
  "summary": "краткое содержание в 2–3 предложениях"
}}"""


# ── Получение транскрипции ────────────────────────────────────────────────────

def video_id(url: str) -> str:
    m = re.search(r"(?:v=|youtu\.be/|/embed/)([A-Za-z0-9_-]{11})", url)
    if m:
        return m.group(1)
    if re.match(r"^[A-Za-z0-9_-]{11}$", url):
        return url
    raise ValueError(f"Не удалось извлечь video ID из: {url}")


def transcript_api(vid: str) -> str:
    """Быстрый путь: авто-субтитры через youtube-transcript-api."""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError:
        raise RuntimeError("pip install youtube-transcript-api")

    try:
        segs = YouTubeTranscriptApi.get_transcript(vid, languages=["ru", "en"])
    except Exception:
        tlist = YouTubeTranscriptApi.list_transcripts(vid)
        segs = tlist.find_generated_transcript(["ru", "en"]).fetch()
    return " ".join(s["text"] for s in segs)


def _whisper_model() -> str:
    """Ищет модель whisper в стандартных путях Homebrew."""
    for base in ("/usr/local/share/whisper-cpp", "/opt/homebrew/share/whisper-cpp"):
        for name in ("ggml-base.bin", "ggml-small.bin", "ggml-medium.bin"):
            p = Path(base) / name
            if p.exists():
                return str(p)
    raise RuntimeError(
        "Модель whisper не найдена. Скачайте:\n"
        "  curl -L 'https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin'"
        " -o /usr/local/share/whisper-cpp/ggml-base.bin"
    )


def transcript_whisper(url: str) -> str:
    """Fallback: yt-dlp скачивает аудио → whisper-cli транскрибирует локально."""
    with tempfile.TemporaryDirectory() as tmp:
        audio = os.path.join(tmp, "audio.mp3")
        r = subprocess.run(
            ["yt-dlp", "-x", "--audio-format", "mp3", "-o", audio, url],
            capture_output=True, text=True, timeout=180,
        )
        if r.returncode != 0:
            raise RuntimeError(f"yt-dlp: {r.stderr[:300]}")

        model = _whisper_model()
        out_prefix = os.path.join(tmp, "transcript")
        r = subprocess.run(
            ["/usr/local/bin/whisper-cli", "-m", model, "-f", audio,
             "-l", "auto", "-otxt", "-of", out_prefix, "-np"],
            capture_output=True, text=True, timeout=600,
        )
        if r.returncode != 0:
            raise RuntimeError(f"whisper-cli: {r.stderr[:300]}")

        txt_path = out_prefix + ".txt"
        if not Path(txt_path).exists():
            raise RuntimeError("whisper-cli не создал файл транскрипции")
        return Path(txt_path).read_text(encoding="utf-8").strip()


def get_transcript(url: str) -> str:
    vid = video_id(url)
    try:
        return transcript_api(vid)
    except Exception as e1:
        try:
            return transcript_whisper(url)
        except Exception as e2:
            raise RuntimeError(f"API: {e1} | Whisper: {e2}")


# ── Анализ через DeepSeek ─────────────────────────────────────────────────────

def analyze(url: str) -> dict:
    text = get_transcript(url)
    trimmed = text[:6000] + ("\n[... обрезано ...]" if len(text) > 6000 else "")

    prompt = ANALYZE_PROMPT.format(transcript=trimmed)
    r = subprocess.run(
        [sys.executable, str(DEEPSEEK), prompt],
        capture_output=True, text=True, timeout=90,
    )
    if r.returncode != 0:
        raise RuntimeError(f"deepseek_call.py: {r.stderr[:300]}")

    raw = r.stdout.strip()
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    if not m:
        raise RuntimeError(f"JSON не найден в ответе: {raw[:200]}")
    return {"url": url, "transcript_chars": len(text), **json.loads(m.group())}


# ── Анализ канала ─────────────────────────────────────────────────────────────

def analyze_channel(channel_url: str, n: int = 5) -> list:
    try:
        r = subprocess.run(
            ["yt-dlp", "--flat-playlist", "-J", "--playlist-end", str(n), channel_url],
            capture_output=True, text=True, timeout=60,
        )
        entries = json.loads(r.stdout).get("entries", [])
    except Exception as e:
        return [{"error": f"Не удалось получить список видео: {e}"}]

    results = []
    for entry in entries:
        video_url = f"https://youtube.com/watch?v={entry.get('id', '')}"
        try:
            results.append(analyze(video_url))
        except Exception as e:
            results.append({"url": video_url, "error": str(e)})
    return results


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    args = sys.argv[1:]

    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0)

    mode = args[0]
    try:
        if mode == "transcript":
            text = get_transcript(args[1])
            result = {"transcript": text, "chars": len(text)}

        elif mode == "analyze":
            result = analyze(args[1])

        elif mode == "channel":
            n = int(args[2]) if len(args) > 2 else 5
            result = {"channel": args[1], "videos": analyze_channel(args[1], n)}

        else:
            result = {"error": f"Неизвестный режим '{mode}'. Доступны: transcript, analyze, channel"}

    except (IndexError, ValueError):
        result = {"error": f"Укажите URL. Пример: {mode} <url>"}
    except Exception as e:
        result = {"error": str(e)}

    print(json.dumps(result, ensure_ascii=False, indent=2))
