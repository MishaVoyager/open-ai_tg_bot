from datetime import datetime as dt, timezone as tz


def get_time_now() -> dt:
    return dt.now(tz=tz.utc)


def reduce_datetime_to_date_utc(datetime: dt) -> dt:
    return dt(year=datetime.year, month=datetime.month, day=datetime.day, tzinfo=tz.utc)


def format_interval(since: dt, until: dt, lower: bool = False) -> str:
    message = f"С {format_date(since)} по {format_date(until)}"
    return message.lower() if lower else message


def format_date(date: dt) -> str:
    return date.strftime('%d.%m.%Y')


def get_word_ending(count: int, variants: list[str]) -> str:
    """
    Возвращает окончание слова в зависимости от количества.
    :variants - варианты окончания, первое - например, для количества 1, второе для 2, третье для 5
    """
    count = count % 100
    if 11 <= count <= 19:
        return variants[2]
    count = count % 10
    if count == 1:
        return variants[0]
    elif count in [2, 3, 4]:
        return variants[1]
    return variants[2]
