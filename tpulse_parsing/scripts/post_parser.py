from tpulse import TinkoffPulse
from random import randint
from httpx import HTTPStatusError, ConnectError, ConnectTimeout, ReadTimeout
from typing import List, Dict
from dataclasses import dataclass
from time import sleep
from datetime import datetime
import logging

from IPython.display import clear_output # type: ignore

from scripts.database import batch_insert
import dateutil.parser
from dateutil.tz import UTC

# Настройка логгера
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Очищаем все существующие обработчики
logger.handlers.clear()

handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

@dataclass
class ErrorLog:
    ticker: str
    cursor: int
    error: Exception

def get_dt():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

class TinkoffPulseParser:
    def __init__(self, start_date: str = None, db_name: str = None):
        """
        Args:
            start_date: дата в формате 'YYYY-MM-DD'
            db_name: имя базы данных
        """
        self.pulse = TinkoffPulse()
        self.db_name = db_name
        self.errors: List[ErrorLog] = []
        self.total_posts = 0
        self.rounds = 0
        
        # Преобразуем строку даты в datetime объект с UTC
        self.start_date = (
            datetime.strptime(start_date, '%Y-%m-%d').replace(tzinfo=UTC)
            if start_date
            else None
        )

    @staticmethod
    def _parse_date(date_str: str) -> datetime:
        """Безопасный парсинг даты из разных форматов"""
        return dateutil.parser.parse(date_str).astimezone(UTC)

    def parse_single_ticker(self, ticker: str) -> None:
        """Парсит посты для одного тикера"""
        if self.db_name is None:
            self.db_name = self._generate_db_name(ticker)
        
        fetch_cursor = 999999999
        
        logger.info(f"Парсинг постов по тикеру {ticker}...")

        while True:
            # logger.info(f"Прокрутка для тикера {ticker}")
            try:
                posts_from_ticker = self.pulse.get_posts_by_ticker(
                    ticker=ticker, 
                    cursor=fetch_cursor
                )
                posts = posts_from_ticker["items"]
                
                # Проверяем дату самого старого поста
                oldest_post_date = self._parse_date(posts[-1]["inserted"])
                
                # Если дошли до постов раньше заданной даты, прерываем цикл
                if self.start_date and oldest_post_date < self.start_date:
                    # Фильтруем только посты после start_date
                    posts = [
                        post for post in posts
                        if self._parse_date(post["inserted"]) >= self.start_date
                    ]
                    if posts:  # Если остались посты после фильтрации
                        self._parse_posts_batch(posts)
                    logger.info(f"Достигнута целевая дата {self.start_date}")
                    break
                
                self._parse_posts_batch(posts)
                fetch_cursor = posts_from_ticker["nextCursor"]
                # logger.info(f"Получено постов: {len(posts)}")
                sleep(randint(2, 5))
                
            except (HTTPStatusError, ConnectError, ConnectTimeout, ReadTimeout) as e:
                logger.error("Network error", exc_info=e)
                sleep(25)
                self.errors.append(ErrorLog(ticker, fetch_cursor, e))
            except Exception as e:
                logger.error("Unexpected error", exc_info=e)
                sleep(15)
                self.errors.append(ErrorLog(ticker, fetch_cursor, e))
            finally:
                self.pulse = TinkoffPulse()

    def _parse_posts_batch(self, posts: List[Dict]) -> None:
        """Обработка и сохранение batch постов"""
        posts_data = []

        self.rounds += 1
        self.total_posts += len(posts)

        if self.rounds % 10 == 1:
            clear_output(wait=True)
            print(f"Обрабатывается дата: {posts[0]['inserted']}")
            print(f"Получено постов: {self.total_posts}")

        for post in posts:
            post_data = {
                "post_id": post["id"],
                "inserted": post["inserted"],
                "instruments": (
                    ", ".join([i["ticker"] for i in post["content"]["instruments"]])
                    if len(post["content"]["instruments"]) > 0
                    else None
                ),
                "hashtags": (
                    ", ".join([i["title"] for i in post["content"]["hashtags"]])
                    if len(post["content"]["hashtags"]) > 0
                    else None
                ),
                "content": post["content"]["text"],
                "reactions_count": post.get("reactions", {}).get("totalCount", 0),
                "comments_count": post.get("commentsCount", 0),
                "parse_dt": get_dt(),
            }
            posts_data.append(post_data)
        batch_insert("tcs_pulse_posts", posts_data, db_name=self.db_name)

    def parse_from_file(self, filename: str = "tickers.txt") -> List[ErrorLog]:
        """Парсит посты для списка тикеров из файла"""
        with open(filename, "r") as f:
            tickers = [i.strip() for i in f.read().split("\n")]
        
        for ticker in tickers:
            self.parse_single_ticker(ticker)
        
        return self.errors

if __name__ == "__main__":
    parser = TinkoffPulseParser()
    errors = parser.parse_from_file()
    if errors:
        logger.error(f"Encountered {len(errors)} errors during execution")