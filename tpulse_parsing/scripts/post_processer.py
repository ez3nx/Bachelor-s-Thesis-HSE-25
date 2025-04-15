import re


def preprocess_text_base(text):
    # Базовая предобработка
    text = re.sub(r"http\S+|www\S+|https\S+", "", text)  # Удаление URLs
    text = re.sub(r"<.*?>", "", text)  # Удаление HTML тегов
    text = re.sub(r"#\w+", "", text)  # Удаление хэштегов

    return text.strip()


def preprocess_other_tickets(text, ticker, ticker_patterns):

    paragraphs = text.split("\n\n")
    processed_paragraphs = []

    for paragraph in paragraphs:
        if any(
            re.search(pattern, paragraph, re.IGNORECASE) for pattern in ticker_patterns
        ):
            sentences = re.split(r"([.!?]+(?:\s+|$))", paragraph)
            processed_sentences = []

            i = 0
            while i < len(sentences):
                if i + 1 < len(sentences):
                    current_sentence = sentences[i] + sentences[i + 1]
                else:
                    current_sentence = sentences[i]

                has_sber = any(
                    re.search(pattern, current_sentence, re.IGNORECASE)
                    for pattern in ticker_patterns
                )

                has_other_ticker = bool(
                    re.search(rf"\{{\$(?!{ticker})[A-Z]+\}}", current_sentence)
                )

                if has_sber or not has_other_ticker:
                    processed_sentences.append(current_sentence.strip())

                i += 2

            if processed_sentences:
                processed_paragraphs.append(" ".join(processed_sentences))

    result = "\n\n".join(processed_paragraphs)

    return result.strip()


def clean_promotional_content(text):
    # Паттерны для рекламы
    promo_patterns = [
        r"[^\n]*(?:Тиньк(?:офф|ов)|Tinkoff)[^\n]*\n?",
        r"[^\n]*подар(?:ок|ки|очн)[^\n]*\n?",
        r"[^\n]*подпи(?:ши|ска|сывай)[^\n]*\n?",
        r"[^\n]*(?:Услови[яе]|открыть счет)[^\n]*\n?",
        r"[^\n]*(?:загляни в профиль|смотри в профиле)[^\n]*\n?",
        r"[^\n]*(?:Жми|Нажимай|Переходи|Успей)[^\n]*\n?",
        r"[^\n]*(?:реферал|бонус|промокод)[^\n]*\n?",
    ]

    for pattern in promo_patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)

    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.strip()

    return text


def mark_ticker_only_posts(df):
    # Паттерн для поиска тикеров
    ticker_pattern = r"\{\$[A-Z]+[P]?\}"

    def is_ticker_only(text):
        if not isinstance(text, str):
            return 0

        # Очищаем текст от тикеров
        clean_text = re.sub(ticker_pattern, "", text)
        # Очищаем от запятых и пробелов
        clean_text = re.sub(r"[,\s]+", "", clean_text)

        # Если после очистки ничего не осталось - значит был только список тикеров
        return 1 if len(clean_text) == 0 else 0

    df["ticker_only"] = df["processed_posts"].progress_apply(is_ticker_only)

    return df
