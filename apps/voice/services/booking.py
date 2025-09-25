from datetime import datetime, timedelta
import pytz

TZ = pytz.timezone("America/Toronto")
BOOK_START_HOUR = 9
BOOK_END_HOUR = 21  # 9 PM

class BookingPolicy:
    @staticmethod
    def next_slots(now: datetime, n: int = 4):
        now_local = now.astimezone(TZ)
        slots = []
        cursor = now_local
        for _ in range(72):  # ~3 দিনের ভেতর স্ক্যান
            cursor += timedelta(minutes=30)
            if BOOK_START_HOUR <= cursor.hour < BOOK_END_HOUR:
                slots.append(cursor.replace(second=0, microsecond=0))
            if len(slots) >= n:
                break
        return slots

    @staticmethod
    def inside_window(dt: datetime) -> bool:
        local = dt.astimezone(TZ)
        return BOOK_START_HOUR <= local.hour < BOOK_END_HOUR
