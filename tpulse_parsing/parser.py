from tpulse import TinkoffPulse
from random import randint
from httpx import HTTPStatusError, ConnectError, ConnectTimeout, ReadTimeout
from typing import List, Dict
from dataclasses import dataclass
from time import sleep
from datetime import datetime
import logging
from tqdm import trange
from database import batch_insert


# Настройка логгера
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
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


def get_tickers_list() -> List[str]:
    with open("tickers.txt", "r") as f:
        tickers = [i.strip() for i in f.read().split("\n")]
    return tickers


def parse_posts_batch(posts):
    posts_data = []
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

    batch_insert("tcs_pulse_posts_sber", posts_data)


def parse_posts_by_ticker_list():
    errors: List[ErrorLog] = []
    pulse = TinkoffPulse()
    tickers = get_tickers_list()

    # Константы в начало
    MAX_STEPS = 400

    for ticker in tickers:
        fetch_cursor = 999999999

        for step in trange(1, MAX_STEPS):
            logger.info(f"Прокрутка для тикера {ticker} № {step}")

            try:
                # Получаем посты пакетом
                posts_from_ticker = pulse.get_posts_by_ticker(
                    ticker=ticker, cursor=fetch_cursor
                )
                posts = posts_from_ticker["items"]

                if not posts:
                    logger.info(f"Для тикера {ticker} больше нет постов")
                    break

                # Batch insert вместо поштучного
                parse_posts_batch(posts)

                fetch_cursor = posts_from_ticker["nextCursor"]
                logger.info(f"Получено постов: {len(posts)}")

                sleep(randint(1, 3))

            except (HTTPStatusError, ConnectError, ConnectTimeout, ReadTimeout) as e:
                logger.error("Network error", exc_info=e)
                sleep(25)
                errors.append(ErrorLog(ticker, fetch_cursor, e))

            except Exception as e:
                logger.error("Unexpected error", exc_info=e)
                sleep(15)
                errors.append(ErrorLog(ticker, fetch_cursor, e))

            finally:
                pulse = TinkoffPulse()

    return errors


if __name__ == "__main__":
    errors = parse_posts_by_ticker_list()
    if errors:
        logger.error(f"Encountered {len(errors)} errors during execution")
