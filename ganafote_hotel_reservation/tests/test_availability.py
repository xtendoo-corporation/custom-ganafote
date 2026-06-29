# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date

from odoo.tests.common import tagged

from .common import HotelReservationCommon


@tagged("post_install", "-at_install")
class TestAvailability(HotelReservationCommon):
    """Tests unitarios del servicio de disponibilidad por noche."""

    def setUp(self):
        super().setUp()
        self.availability = self.env["ganafote.hotel.availability"]

    # ------------------------------------------------------------------
    # _get_nights
    # ------------------------------------------------------------------
    def test_get_nights_full_range(self):
        nights = self.availability._get_nights(date(2026, 8, 1), date(2026, 8, 8))
        self.assertEqual(len(nights), 7)
        self.assertEqual(nights[0], date(2026, 8, 1))
        self.assertEqual(nights[-1], date(2026, 8, 7))
        self.assertNotIn(date(2026, 8, 8), nights)

    def test_get_nights_single_night(self):
        nights = self.availability._get_nights(date(2026, 8, 1), date(2026, 8, 2))
        self.assertEqual(nights, [date(2026, 8, 1)])

    def test_get_nights_same_day_is_empty(self):
        self.assertEqual(
            self.availability._get_nights(date(2026, 8, 1), date(2026, 8, 1)), []
        )

    def test_get_nights_reversed_is_empty(self):
        self.assertEqual(
            self.availability._get_nights(date(2026, 8, 8), date(2026, 8, 1)), []
        )

    def test_get_nights_missing_dates_is_empty(self):
        self.assertEqual(self.availability._get_nights(False, date(2026, 8, 8)), [])
        self.assertEqual(self.availability._get_nights(date(2026, 8, 1), False), [])

    # ------------------------------------------------------------------
    # check_availability
    # ------------------------------------------------------------------
    def test_check_availability_ok(self):
        self._create_confirmed_allotment(quota=5)
        missing = self.availability.check_availability(
            self.hotel_product.id,
            self.date_start,
            self.date_end,
            5,
            self.company.id,
        )
        self.assertEqual(missing, [])

    def test_check_availability_insufficient_returns_all_nights(self):
        self._create_confirmed_allotment(quota=2)
        missing = self.availability.check_availability(
            self.hotel_product.id,
            self.date_start,
            self.date_end,
            3,
            self.company.id,
        )
        self.assertEqual(len(missing), 7)

    def test_check_availability_without_cupo_returns_all_nights(self):
        missing = self.availability.check_availability(
            self.hotel_product.id,
            self.date_start,
            self.date_end,
            1,
            self.company.id,
        )
        self.assertEqual(len(missing), 7)

    def test_check_availability_empty_range(self):
        missing = self.availability.check_availability(
            self.hotel_product.id,
            self.date_start,
            self.date_start,
            1,
            self.company.id,
        )
        self.assertEqual(missing, [])

    # ------------------------------------------------------------------
    # reserve / release
    # ------------------------------------------------------------------
    def test_reserve_decrements_available(self):
        allotment = self._create_confirmed_allotment(quota=5)
        self.availability.reserve(
            self.hotel_product.id,
            self.date_start,
            self.date_end,
            2,
            self.company.id,
        )
        for record in allotment.availability_ids:
            self.assertEqual(record.reserved_qty, 2)
            self.assertEqual(record.available_qty, 3)

    def test_release_restores_available(self):
        allotment = self._create_confirmed_allotment(quota=5)
        self.availability.reserve(
            self.hotel_product.id, self.date_start, self.date_end, 2, self.company.id
        )
        self.availability.release(
            self.hotel_product.id, self.date_start, self.date_end, 2, self.company.id
        )
        for record in allotment.availability_ids:
            self.assertEqual(record.reserved_qty, 0)
            self.assertEqual(record.available_qty, 5)

    def test_release_never_goes_negative(self):
        allotment = self._create_confirmed_allotment(quota=5)
        self.availability.release(
            self.hotel_product.id, self.date_start, self.date_end, 10, self.company.id
        )
        for record in allotment.availability_ids:
            self.assertEqual(record.reserved_qty, 0)

    def test_available_qty_compute(self):
        allotment = self._create_confirmed_allotment(quota=5)
        record = allotment.availability_ids[0]
        record.reserved_qty = 4
        self.assertEqual(record.available_qty, 1)

    def test_records_for_empty_range(self):
        records = self.availability._records_for(
            self.hotel_product.id, self.date_start, self.date_start, self.company.id
        )
        self.assertFalse(records)
