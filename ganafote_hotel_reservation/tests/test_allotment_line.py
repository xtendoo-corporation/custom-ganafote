# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date

from odoo.exceptions import UserError
from odoo.tests.common import tagged

from .common import HotelReservationCommon


@tagged("post_install", "-at_install")
class TestAllotmentLine(HotelReservationCommon):
    """Tests de la línea de cupo: precio sugerido y validaciones."""

    def test_suggested_price_percent(self):
        allotment = self._create_allotment(
            [
                self._allotment_line_vals(
                    self.hotel_product,
                    self.date_start,
                    self.date_end,
                    5,
                    cost=100.0,
                    margin_type="percent",
                    margin_value=20.0,
                )
            ]
        )
        self.assertAlmostEqual(allotment.line_ids.suggested_price, 120.0)

    def test_suggested_price_fixed(self):
        allotment = self._create_allotment(
            [
                self._allotment_line_vals(
                    self.hotel_product,
                    self.date_start,
                    self.date_end,
                    5,
                    cost=100.0,
                    margin_type="fixed",
                    margin_value=25.0,
                )
            ]
        )
        self.assertAlmostEqual(allotment.line_ids.suggested_price, 125.0)

    def test_quota_must_be_positive(self):
        with self.assertRaises(UserError):
            self._create_allotment(
                [
                    self._allotment_line_vals(
                        self.hotel_product, self.date_start, self.date_end, 0
                    )
                ]
            )

    def test_line_dates_constraint(self):
        with self.assertRaises(UserError):
            self._create_allotment(
                [
                    self._allotment_line_vals(
                        self.hotel_product, date(2026, 8, 8), date(2026, 8, 1), 5
                    )
                ]
            )

    def test_reserved_available_without_availability(self):
        allotment = self._create_allotment(
            [
                self._allotment_line_vals(
                    self.hotel_product, self.date_start, self.date_end, 5
                )
            ]
        )
        line = allotment.line_ids
        self.assertEqual(line.reserved_qty, 0)
        self.assertEqual(line.available_qty, 5)

    def test_reserved_available_after_reservation(self):
        allotment = self._create_confirmed_allotment(quota=5)
        order = self._create_sale_order(rooms=2)
        order.action_confirm()
        line = allotment.line_ids
        line.invalidate_recordset()
        self.assertEqual(line.reserved_qty, 2)
        self.assertEqual(line.available_qty, 3)
