from datetime import datetime, date, time, timedelta
from django.test import TestCase
from django.utils import timezone

from booking.models import Booking, TimeOff, DaysOff
from services.models import Service
from booking.services.scheduler import get_available_days, get_available_slots


class SchedulerTests(TestCase):
    def setUp(self):
        """Создаём тестовый сервис (услуга)"""
        self.service = Service.objects.create(
            name="Маникюр",
            duration_min=60,
            buffer_after_min=15,
        )
        self.day = date(2025, 9, 15)  # понедельник

    def test_sunday_is_always_day_off(self):
        """Воскресенье всегда пустое"""
        sunday = date(2025, 9, 21)
        slots = get_available_slots(self.service, sunday)
        self.assertEqual(slots, [])

    def test_last_slot_can_end_at_work_end(self):
        """Последний слот может заканчиваться ровно в WORK_END"""
        slots = get_available_slots(self.service, self.day)
        last_slot = slots[-1]
        self.assertEqual(last_slot["end"].time(), time(20, 0))

    def test_booking_blocks_slots(self):
        """Бронь должна блокировать слоты внутри диапазона + buffer"""
        booking_start = datetime.combine(self.day, time(13, 0))
        Booking.objects.create(
            service=self.service,
            starts_at=booking_start,
            ends_at=booking_start + timedelta(minutes=90),  # услуга 1ч30м
            status=Booking.Status.CONFIRMED,
            customer_name="Test",
            customer_phone="123",
        )

        slots = get_available_slots(self.service, self.day)

        # 13:00-14:00 пересекается
        self.assertFalse(any(s["start"].time() == time(13, 0) for s in slots))

        # ближайший допустимый слот — 14:50
        self.assertTrue(any(s["start"].time() == time(14, 50) for s in slots))

    def test_timeoff_blocks_slots(self):
        """TimeOff должен вырезать диапазон"""
        TimeOff.objects.create(
            date=self.day,
            start=time(12, 0),
            end=time(14, 0),
            reason="Lunch"
        )

        slots = get_available_slots(self.service, self.day)

        # слоты 12:00–14:00 должны быть заблокированы
        self.assertFalse(any(time(12, 0) <= s["start"].time() < time(14, 0) for s in slots))

        # до и после — есть
        self.assertTrue(any(s["start"].time() == time(11, 0) for s in slots))
        self.assertTrue(any(s["start"].time() == time(14, 0) for s in slots))

    def test_days_off_blocks_entire_day(self):
        """DaysOff блокирует весь день"""
        DaysOff.objects.create(
            start=self.day,
            end=self.day,
            reason="Holiday"
        )
        slots = get_available_slots(self.service, self.day)
        self.assertEqual(slots, [])
