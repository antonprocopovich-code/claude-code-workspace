#!/usr/bin/env python3
"""Публикация контента в Google Docs и Google Sheets."""

import sys
import json
import argparse
from pathlib import Path

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/spreadsheets",
]

import os
os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "1"

BASE_DIR = Path(__file__).parent
CREDENTIALS_FILE = BASE_DIR / "credentials.json"
TOKEN_FILE = BASE_DIR / "token.json"


def get_service(api, version):
    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        TOKEN_FILE.write_text(creds.to_json())
    return build(api, version, credentials=creds)


def create_doc(title, body_text, folder_id=None):
    """Создать Google Doc и вернуть ссылку."""
    docs = get_service("docs", "v1")
    drive = get_service("drive", "v3")

    doc = docs.documents().create(body={"title": title}).execute()
    doc_id = doc["documentId"]

    if body_text:
        docs.documents().batchUpdate(
            documentId=doc_id,
            body={
                "requests": [
                    {
                        "insertText": {
                            "location": {"index": 1},
                            "text": body_text,
                        }
                    }
                ]
            },
        ).execute()

    return f"https://docs.google.com/document/d/{doc_id}/edit"


def append_sheet(spreadsheet_id, sheet_name, values):
    """Добавить строки в Google Sheet."""
    sheets = get_service("sheets", "v4")
    range_ = f"{sheet_name}!A1" if sheet_name else "A1"
    result = (
        sheets.spreadsheets()
        .values()
        .append(
            spreadsheetId=spreadsheet_id,
            range=range_,
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body={"values": values},
        )
        .execute()
    )
    return f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit"


def create_sheet(title, values=None):
    """Создать новый Google Sheet и вернуть ссылку."""
    sheets = get_service("sheets", "v4")
    body = {"properties": {"title": title}}
    spreadsheet = sheets.spreadsheets().create(body=body).execute()
    spreadsheet_id = spreadsheet["spreadsheetId"]

    if values:
        sheets.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range="A1",
            valueInputOption="USER_ENTERED",
            body={"values": values},
        ).execute()

    return f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit"


def main():
    parser = argparse.ArgumentParser(description="Публикация в Google Docs/Sheets")
    subparsers = parser.add_subparsers(dest="command")

    # doc create
    p_doc = subparsers.add_parser("doc", help="Создать Google Doc")
    p_doc.add_argument("title", help="Заголовок документа")
    p_doc.add_argument("--body", help="Текст документа")
    p_doc.add_argument("--body-file", help="Путь к файлу с текстом")
    p_doc.add_argument("--folder-id", help="ID папки в Drive")

    # sheet append
    p_append = subparsers.add_parser("sheet-append", help="Добавить строки в Sheet")
    p_append.add_argument("spreadsheet_id", help="ID таблицы")
    p_append.add_argument("--sheet", default="Sheet1", help="Название листа")
    p_append.add_argument("--values", help="JSON-массив строк [[col1, col2], ...]")

    # sheet create
    p_create = subparsers.add_parser("sheet-create", help="Создать новый Sheet")
    p_create.add_argument("title", help="Название таблицы")
    p_create.add_argument("--values", help="JSON-массив строк [[col1, col2], ...]")

    args = parser.parse_args()

    if args.command == "doc":
        body_text = args.body or ""
        if args.body_file:
            body_text = Path(args.body_file).read_text()
        url = create_doc(args.title, body_text, args.folder_id)
        print(url)

    elif args.command == "sheet-append":
        values = json.loads(args.values) if args.values else []
        url = append_sheet(args.spreadsheet_id, args.sheet, values)
        print(url)

    elif args.command == "sheet-create":
        values = json.loads(args.values) if args.values else None
        url = create_sheet(args.title, values)
        print(url)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
