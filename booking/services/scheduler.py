from __future__ import annotations

from datetime import datetime, date, timedelta, time
from typing import List, Dict

from django.conf import settings
from django.utils import timezone

from booking.models import Booking, DaysOff, TimeOff
from services.models import Service


# настройки
LOCK_TIMEOUT: timedelta = timedelta(minutes=settings.LOCK_TIMEOUT)
WORK_START: time = time(settings.WORK_START, 0)   # например, 10:00
WORK_END: time = time(settings.WORK_END, 0)       # например, 20:00
GRID_STEP: int = settings.GRID_STEP               # шаг сетки, мин


def get_available_days(
    service: Service,
    days_ahead: int = 60,
    grid_step: int = GRID_STEP,
) -> List[date]:
    """Вернуть список доступных дней (не воскресенье, не выходные, есть свободные слоты)."""
    today: date = timezone.localdate()
    end_date: date = today + timedelta(days=days_ahead)
    now: datetime = timezone.now()

    # все брони в диапазоне
    all_bookings: List[Booking] = list(
        Booking.objects.filter(starts_at__date__range=(today, end_date))
        .exclude(status=Booking.Status.CANCELLED)
        .exclude(
            status=Booking.Status.PENDING,
            created_at__lt=now - LOCK_TIMEOUT,
        )
    )

    # группировка броней по дню
    bookings_by_day: Dict[date, List[Booking]] = {}
    for b in all_bookings:
        bookings_by_day.setdefault(b.starts_at.date(), []).append(b)

    # timeoffs по дню
    all_timeoffs: List[TimeOff] = list(TimeOff.objects.filter(date__range=(today, end_date)))
    timeoffs_by_day: Dict[date, List[TimeOff]] = {}
    for t in all_timeoffs:
        timeoffs_by_day.setdefault(t.date, []).append(t)

    # выходные дни
    all_daysoff: List[DaysOff] = list(
        DaysOff.objects.filter(start__lte=end_date, end__gte=today)
    )

    result: List[date] = []
    for offset in range(days_ahead):
        current_day: date = today + timedelta(days=offset)

        # воскресенье
        if current_day.weekday() == 6:
            continue

        # проверка DaysOff
        if any(d.start <= current_day <= d.end for d in all_daysoff):
            continue

        bookings: List[Booking] = bookings_by_day.get(current_day, [])
        timeoffs: List[TimeOff] = timeoffs_by_day.get(current_day, [])

        slots: List[Dict[str, datetime]] = _generate_slots(
            service, current_day, bookings, timeoffs, grid_step
        )

        if slots:
            result.append(current_day)

    return result


def get_available_slots(
    service: Service,
    day: date,
    grid_step: int = GRID_STEP,
) -> List[Dict[str, datetime]]:
    """Вернуть доступные слоты на конкретный день."""
    if day.weekday() == 6:  # воскресенье
        return []

    now: datetime = timezone.now()

    bookings: List[Booking] = list(
        Booking.objects.filter(starts_at__date=day)
        .exclude(status=Booking.Status.CANCELLED)
        .exclude(
            status=Booking.Status.PENDING,
            created_at__lt=now - LOCK_TIMEOUT,
        )
    )

    timeoffs: List[TimeOff] = list(TimeOff.objects.filter(date=day))

    return _generate_slots(service, day, bookings, timeoffs, grid_step)


def _generate_slots(
    service: Service,
    day: date,
    bookings: List[Booking],
    timeoffs: List[TimeOff],
    grid_step: int = GRID_STEP,
) -> List[Dict[str, datetime]]:
    """Сгенерировать все свободные слоты для дня с учётом броней и перерывов."""
    work_start: datetime = timezone.make_aware(datetime.combine(day, WORK_START))
    work_end: datetime = timezone.make_aware(datetime.combine(day, WORK_END))

    duration: timedelta = timedelta(minutes=service.duration_min)
    buffer: timedelta = timedelta(minutes=service.buffer_after_min)
    step: timedelta = timedelta(minutes=grid_step)

    slots: List[Dict[str, datetime]] = []
    current: datetime = work_start

    # сортируем брони и тайм-оффы для удобства
    bookings = sorted(bookings, key=lambda b: b.starts_at)
    timeoffs = sorted(timeoffs, key=lambda t: t.start or time.min)

    while current <= work_end:
        candidate_start: datetime = current
        candidate_end: datetime = candidate_start + duration

        # если услуга выходит за рабочий день → стоп
        if candidate_end > work_end:
            break

        # флаг пересечения
        blocked = False

        # проверка бронирований
        for b in bookings:
            b_start: datetime = b.starts_at
            b_end: datetime = b.ends_at or (
                b.starts_at + timedelta(minutes=b.service.duration_min)
            )
            b_end = b_end + timedelta(minutes=b.service.buffer_after_min)

            # если слот пересекается с бронью
            if not (candidate_end <= b_start or candidate_start >= b_end):
                blocked = True
                current = max(current + step, b_end)
                break            

        if blocked:
            continue

        # проверка timeoff
        for to in timeoffs:
            if not (to.start and to.end):
                continue
            to_start: datetime = timezone.make_aware(datetime.combine(day, to.start))
            to_end: datetime = timezone.make_aware(datetime.combine(day, to.end))

            if candidate_start < to_end and candidate_end > to_start:
                blocked = True
                current = max(current + step, to_end)
                break

        if blocked:
            continue

        # слот валиден
        slots.append({"start": candidate_start, "end": candidate_end})

        # шаг вперёд
        current += step

    return slots
