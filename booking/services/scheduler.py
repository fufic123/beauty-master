from __future__ import annotations
from datetime import datetime, date, timedelta
from typing import List, Dict, Any

from django.conf import settings
from django.utils import timezone

from booking.models import Booking, DaysOff, TimeOff
from services.models import Service


LOCK_TIMEOUT = settings.LOCK_TIMEOUT
WORK_START = settings.WORK_START
WORK_END = settings.WORK_END
GRID_STEP = settings.GRID_STEP  # in minutes


def get_available_days(service: Service, days_ahead: int = 60, grid_step: int = GRID_STEP) -> List[date]:
    today: date = timezone.localdate()
    end_date: date = today + timedelta(days=days_ahead)
    now: datetime = timezone.now()

    # загружаем все брони за диапазон
    all_bookings: List[Booking] = list(
        Booking.objects.filter(
            starts_at__date__range=(today, end_date)
        ).exclude(status=Booking.Status.CANCELLED
        ).exclude(
            status=Booking.Status.PENDING,
            created_at__lt=now - LOCK_TIMEOUT
        )
    )

    # группируем брони по дню
    bookings_by_day: Dict[date, List[Booking]] = {}
    for b in all_bookings:
        day = b.starts_at.date()
        bookings_by_day.setdefault(day, []).append(b)

    # загружаем все TimeOff
    all_timeoffs: List[TimeOff] = list(TimeOff.objects.filter(date__range=(today, end_date)))
    timeoffs_by_day: Dict[date, List[TimeOff]] = {}
    for t in all_timeoffs:
        timeoffs_by_day.setdefault(t.date, []).append(t)

    # загружаем DaysOff
    all_daysoff: List[DaysOff] = list(DaysOff.objects.filter(start__lte=end_date, end__gte=today))

    result: List[date] = []
    for offset in range(days_ahead):
        current_day: date = today + timedelta(days=offset)

        if current_day.weekday() == 6:  # 6=воскресенье
            continue

        # проверка полного выходного (DaysOff)
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
    grid_step: int = GRID_STEP
) -> List[Dict[str, datetime]]:
    # Воскресенье
    if day.weekday() == 6:
        return []

    now: datetime = timezone.now()

    # брони только на выбранный день
    bookings: List[Booking] = list(
        Booking.objects.filter(starts_at__date=day
        ).exclude(status=Booking.Status.CANCELLED
        ).exclude(
            status=Booking.Status.PENDING,
            created_at__lt=now - LOCK_TIMEOUT
        )
    )

    # timeoff только на этот день
    timeoffs: List[TimeOff] = list(TimeOff.objects.filter(date=day))

    return _generate_slots(service, day, bookings, timeoffs, grid_step)


def _generate_slots(
    service: Service,
    day: date,
    bookings: List[Booking],
    timeoffs: List[TimeOff],
    grid_step: int = GRID_STEP
) -> List[Dict[str, datetime]]:
    work_start: datetime = datetime.combine(day, WORK_START)
    work_end: datetime = datetime.combine(day, WORK_END)

    duration: timedelta = timedelta(minutes=service.duration_min)
    buffer: timedelta = timedelta(minutes=service.buffer_after_min)
    step: timedelta = timedelta(minutes=grid_step)

    slots: List[Dict[str, datetime]] = []
    current: datetime = work_start

    while current <= work_end:
        candidate_start: datetime = current
        candidate_end: datetime = candidate_start + duration

        # если услуга уходит за рабочее время → прерываем цикл
        if candidate_end > work_end:
            break
            
        # пересечение с booking
        overlap_booking: bool = False
        for b in bookings:
            b_start: datetime = b.starts_at
            b_end: datetime = b.ends_at or (
                b.starts_at + timedelta(minutes=b.service.duration_min)
            )
            # добавляем буфер к броням (но не к текущему слоту)
            b_end = b_end + timedelta(minutes=b.service.buffer_after_min)

            if not (candidate_end <= b_start or candidate_start >= b_end):
                overlap_booking = True
                current = max(current + step, b_end)  # прыгаем вперёд
                break
                
        # пересечение с timeoff
        overlap_timeoff: bool = False
        for to in timeoffs:
            to_start: datetime = datetime.combine(day, to.start)
            to_end: datetime = datetime.combine(day, to.end)

            if candidate_start < to_end and candidate_end > to_start:
                overlap_timeoff = True
                current = max(current + step, to_end)
                break

        is_last_slot: bool = candidate_end == work_end
        if not overlap_booking and not overlap_timeoff:
            if is_last_slot:
                # разрешаем без учёта buffer после услуги
                slots.append({"start": candidate_start, "end": candidate_end})
            else:
                # обычный случай
                slots.append({"start": candidate_start, "end": candidate_end})

        current += step

    return slots