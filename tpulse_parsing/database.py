import sqlite3
from sqlite3 import IntegrityError
from typing import Dict, List
from contextlib import contextmanager
from pathlib import Path
import logging

# Настройка логгера
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

DATABASE_NAME = "ez3nx_pulse_database.db"
SQL_SCHEMA_FILE = "create_tables.sql"

def init_db(db_name: str) -> None:
    """Инициализирует БД с указанным именем"""
    if not Path(SQL_SCHEMA_FILE).exists():
        raise FileNotFoundError(f"Schema file {SQL_SCHEMA_FILE} not found")
        
    with open(SQL_SCHEMA_FILE, "r") as f:
        sql = f.read()
        
    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()
        cursor.executescript(sql)
        conn.commit()

def ensure_db_exists(db_name: str) -> None:
    """Проверяет существование БД и создает её при необходимости"""
    if not Path(db_name).exists():
        init_db(db_name)

@contextmanager
def db_connection(db_name: str = DATABASE_NAME):
    """Контекстный менеджер для автоматического закрытия соединения"""
    conn = sqlite3.connect(db_name)
    try:
        yield conn
    finally:
        conn.close()

def insert(table: str, column_values: Dict, db_name: str = DATABASE_NAME):
    """
    Вставляет данные в указанную таблицу
    Args:
        table: имя таблицы
        column_values: словарь с данными {column_name: value}
        db_name: имя базы данных
    """
    ensure_db_exists(db_name)
    columns = ", ".join(column_values.keys())
    values = [tuple(column_values.values())]
    placeholders = ", ".join("?" * len(column_values.keys()))
    
    with db_connection(db_name) as conn:
        cursor = conn.cursor()
        try:
            cursor.executemany(
                f"INSERT INTO {table} " f"({columns}) " f"VALUES ({placeholders})",
                values,
            )
            conn.commit()
        except IntegrityError:
            pass

def batch_insert(table: str, records: List[Dict], db_name: str = DATABASE_NAME):
    """
    Пакетная вставка множества записей с проверкой на дубликаты
    Args:
        table: имя таблицы
        records: список словарей с данными
        db_name: имя базы данных
    """
    if not records:
        return
        
    ensure_db_exists(db_name)
    
    with db_connection(db_name) as conn:
        cursor = conn.cursor()
        
        # Получаем существующие post_id
        cursor.execute(f"SELECT post_id FROM {table}")
        existing_ids = {row[0] for row in cursor.fetchall()}
        
        # Фильтруем только новые записи
        new_records = [
            record for record in records 
            if str(record['post_id']) not in existing_ids  # преобразуем в строку для сравнения
        ]
        
        if not new_records:
            return
            
        columns = ", ".join(new_records[0].keys())
        placeholders = ", ".join("?" * len(new_records[0]))
        values = [tuple(record.values()) for record in new_records]
        
        try:
            cursor.executemany(
                f"INSERT INTO {table} ({columns}) VALUES ({placeholders})",
                values,
            )
            conn.commit()
        except IntegrityError as e:
            logger.warning(f"Encountered duplicates during insert: {e}")
            pass

# Инициализация дефолтной БД при импорте модуля
# ensure_db_exists(DATABASE_NAME)