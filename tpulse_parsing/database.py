import sqlite3
from sqlite3 import IntegrityError
from typing import Dict, List
from contextlib import contextmanager
from pathlib import Path

DATABASE_NAME = "ez3nx_pulse_database.db"
SQL_SCHEMA_FILE = "create_tables.sql"


def get_db_connection():
    return sqlite3.connect(DATABASE_NAME)


@contextmanager
def db_connection():
    """Контекстный менеджер для автоматического закрытия соединения"""
    conn = get_db_connection()
    try:
        yield conn
    finally:
        conn.close()


def _init_db():
    """Инициализирует БД"""
    if not Path(SQL_SCHEMA_FILE).exists():
        raise FileNotFoundError(f"Schema file {SQL_SCHEMA_FILE} not found")

    with open(SQL_SCHEMA_FILE, "r") as f:
        sql = f.read()

    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.executescript(sql)
        conn.commit()


def insert(table: str, column_values: Dict):
    """
    Вставляет данные в указанную таблицу
    Args:
        table: имя таблицы
        column_values: словарь с данными {column_name: value}
    """
    columns = ", ".join(column_values.keys())
    values = [tuple(column_values.values())]
    placeholders = ", ".join("?" * len(column_values.keys()))

    with db_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.executemany(
                f"INSERT INTO {table} " f"({columns}) " f"VALUES ({placeholders})",
                values,
            )
            conn.commit()
        except IntegrityError:
            pass


def batch_insert(table: str, records: List[Dict]):
    """
    Пакетная вставка множества записей
    Args:
        table: имя таблицы
        records: список словарей с данными
    """
    if not records:
        return

    columns = ", ".join(records[0].keys())
    placeholders = ", ".join("?" * len(records[0]))
    values = [tuple(record.values()) for record in records]

    with db_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.executemany(
                f"INSERT INTO {table} " f"({columns}) " f"VALUES ({placeholders})",
                values,
            )
            conn.commit()
        except IntegrityError:
            pass


# Инициализация БД при импорте модуля
if not Path(DATABASE_NAME).exists():
    _init_db()
