#!/bin/bash
set -e

echo "=== VoiceType — установка ==="
echo ""

# Python 3
if ! command -v python3 &>/dev/null; then
    echo "❌  Python 3 не найден. Установи: brew install python"
    exit 1
fi

# ffmpeg (нужен openai-whisper для декодирования аудио)
if ! command -v ffmpeg &>/dev/null; then
    if ! command -v brew &>/dev/null; then
        echo "❌  Homebrew не найден — нужен для установки ffmpeg."
        echo "    Установи Homebrew: https://brew.sh"
        exit 1
    fi
    echo "📦  Устанавливаем ffmpeg..."
    brew install ffmpeg
fi

echo "📦  Устанавливаем Python-зависимости..."
pip3 install -r requirements.txt

echo ""
echo "✅  Установка завершена!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "⚠️   ВАЖНО: нужны два разрешения в Системных настройках"
echo ""
echo "  1. Специальные возможности (Accessibility)"
echo "     → Системные настройки → Конфиденциальность"
echo "     → Специальные возможности → добавить Terminal / iTerm2"
echo "     (нужно для глобальной горячей клавиши Option+Space)"
echo ""
echo "  2. Микрофон"
echo "     → Системные настройки → Конфиденциальность → Микрофон"
echo "     → добавить Terminal / iTerm2"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🚀  Запуск: python3 app.py"
echo ""
echo "   При первом запуске Whisper скачает модель (~500 MB)."
echo "   Дальше всё работает офлайн."
