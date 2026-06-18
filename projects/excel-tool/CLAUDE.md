# CLAUDE.md — Excel Tool

> Инструмент работы с локальными .xlsx файлами через CLI. Минимальное потребление токенов: только запрошенные данные, никаких файлов в контексте.

---

## Как работать

**Всегда используй CLI.** Не читай `.xlsx` файлы напрямую — только через `excel_cli.py`.

```bash
python3 ~/Documents/Claude\ Code/projects/excel-tool/excel_cli.py <команда> [аргументы]
```

Алиас для удобства:
```bash
alias xls="python3 ~/Documents/Claude\ Code/projects/excel-tool/excel_cli.py"
```

---

## Команды

| Команда | Что делает | Пример |
|---------|-----------|--------|
| `list-sheets` | Список листов | `-f file.xlsx` |
| `info` | Размеры листа, max_row/col | `-f file.xlsx -s Sheet1` |
| `read` | Читать диапазон → JSON | `-f file.xlsx -r A1:D10` |
| `write` | Записать данные в диапазон | `-f file.xlsx -r A1 --data '[[...]]'` |
| `append` | Добавить строки в конец | `-f file.xlsx --data '[[...]]'` |
| `create` | Создать новый .xlsx | `-f new.xlsx -s Лист1` |
| `add-sheet` | Добавить лист | `-f file.xlsx -s Новый` |
| `delete-sheet` | Удалить лист | `-f file.xlsx -s Старый` |
| `clear` | Очистить диапазон | `-f file.xlsx -r A1:C10` |
| `delete-rows` | Удалить строки | `-f file.xlsx --start 3 --count 2` |
| `delete-cols` | Удалить столбцы | `-f file.xlsx --start 2 --count 1` |

---

## Правила экономии токенов

1. **Сначала `info`** — никогда не предполагай размер листа.
2. **Читай только нужный диапазон** — `read -r A1:D20`, не весь лист.
3. **`--data` всегда JSON** — строки в кавычках, числа без: `[["Имя", "Сумма"], ["Антон", 1000]]`
4. **Ошибка → стоп** — если `{"ok": false, "error": "..."}`, сообщи пользователю, не продолжай вслепую.

---

## Зависимости

```bash
pip3 install openpyxl
```

Python 3.x, стандартная библиотека + openpyxl. Без интернета, без API.

---

## Типовой рабочий процесс

```bash
# 1. Разведка
python3 .../excel_cli.py list-sheets -f report.xlsx
# → {"sheets": ["Продажи", "Сводка"]}

# 2. Размеры
python3 .../excel_cli.py info -f report.xlsx -s Продажи
# → {"dims": "A1:F200", "max_row": 200, "max_col": 6, ...}

# 3. Шапка + 2 строки для понимания структуры
python3 .../excel_cli.py read -f report.xlsx -s Продажи -r A1:F3

# 4. Работа
python3 .../excel_cli.py append -f report.xlsx -s Продажи --data '[["2026-06-18", "Товар А", 5000]]'
```
