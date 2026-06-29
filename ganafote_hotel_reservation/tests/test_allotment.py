# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date

from odoo.exceptions import UserError
from odoo.tests.common import tagged

from .common import HotelReservationCommon


@tagged("post_install", "-at_install")
class TestAllotment(HotelReservationCommon):
    """Tests de la cabecera de cupo hotelero."""

    # ------------------------------------------------------------------
    # Confirmación / generación de disponibilidad
    # ------------------------------------------------------------------
    def test_confirm_sets_state(self):
        allotment = self._create_confirmed_allotment(quota=5)
        self.assertEqual(allotment.state, "confirmed")

    def test_confirm_generates_one_record_per_night(self):
        allotment = self._create_confirmed_allotment(quota=5)
        self.assertEqual(len(allotment.availability_ids), 7)
        self.assertNotIn(self.date_end, allotment.availability_ids.mapped("date"))
        self.assertTrue(
            all(record.total_qty == 5 for record in allotment.availability_ids)
        )

    def test_confirm_without_lines_raises(self):
        allotment = self.env["ganafote.hotel.allotment"].create(
            {
                "hotel_id": self.hotel.id,
                "date_start": self.date_start,
                "date_end": self.date_end,
            }
        )
        with self.assertRaises(UserError):
            allotment.action_confirm()

    def test_name_uses_sequence(self):
        allotment = self._create_confirmed_allotment(quota=5)
        self.assertNotEqual(allotment.name, "Nuevo")
        self.assertTrue(allotment.name.startswith("CUPO/"))

    # ------------------------------------------------------------------
    # Solapamientos
    # ------------------------------------------------------------------
    def test_overlap_same_product_raises(self):
        self._create_confirmed_allotment(
            product=self.hotel_product,
            date_start=date(2026, 8, 1),
            date_end=date(2026, 8, 8),
            quota=5,
        )
        overlapping = self._create_allotment(
            [
                self._allotment_line_vals(
                    self.hotel_product, date(2026, 8, 5), date(2026, 8, 10), 2
                )
            ]
        )
        with self.assertRaises(UserError):
            overlapping.action_confirm()

    def test_adjacent_ranges_do_not_overlap(self):
        self._create_confirmed_allotment(
            product=self.hotel_product,
            date_start=date(2026, 8, 1),
            date_end=date(2026, 8, 5),
            quota=5,
        )
        adjacent = self._create_allotment(
            [
                self._allotment_line_vals(
                    self.hotel_product, date(2026, 8, 5), date(2026, 8, 8), 2
                )
            ]
        )
        adjacent.action_confirm()
        self.assertEqual(adjacent.state, "confirmed")

    def test_different_product_does_not_overlap(self):
        self._create_confirmed_allotment(
            product=self.hotel_product,
            date_start=date(2026, 8, 1),
            date_end=date(2026, 8, 8),
            quota=5,
        )
        other = self._create_allotment(
            [
                self._allotment_line_vals(
                    self.hotel_product_alt, date(2026, 8, 1), date(2026, 8, 8), 3
                )
            ]
        )
        other.action_confirm()
        self.assertEqual(other.state, "confirmed")

    # ------------------------------------------------------------------
    # Cancelación / borrador
    # ------------------------------------------------------------------
    def test_cancel_removes_availability(self):
        allotment = self._create_confirmed_allotment(quota=5)
        allotment.action_cancel()
        self.assertEqual(allotment.state, "cancelled")
        self.assertFalse(allotment.availability_ids)

    def test_draft_from_confirmed_removes_availability(self):
        allotment = self._create_confirmed_allotment(quota=5)
        allotment.action_draft()
        self.assertEqual(allotment.state, "draft")
        self.assertFalse(allotment.availability_ids)

    def test_cancel_with_active_reservation_raises(self):
        allotment = self._create_confirmed_allotment(quota=5)
        order = self._create_sale_order(rooms=2)
        order.action_confirm()
        with self.assertRaises(UserError):
            allotment.action_cancel()

    def test_cancel_allowed_after_order_cancel(self):
        allotment = self._create_confirmed_allotment(quota=5)
        order = self._create_sale_order(rooms=2)
        order.action_confirm()
        order._action_cancel()
        allotment.action_cancel()
        self.assertEqual(allotment.state, "cancelled")

    # ------------------------------------------------------------------
    # Validaciones
    # ------------------------------------------------------------------
    def test_dates_constraint(self):
        with self.assertRaises(UserError):
            self.env["ganafote.hotel.allotment"].create(
                {
                    "hotel_id": self.hotel.id,
                    "date_start": date(2026, 8, 8),
                    "date_end": date(2026, 8, 1),
                }
            )

    # ------------------------------------------------------------------
    # Conteos y acciones
    # ------------------------------------------------------------------
    def test_counts(self):
        allotment = self._create_confirmed_allotment(quota=5)
        self.assertEqual(allotment.availability_count, 7)
        self.assertEqual(allotment.booking_count, 0)
        order = self._create_sale_order(rooms=2)
        order.action_confirm()
        allotment.invalidate_recordset()
        self.assertEqual(allotment.booking_count, 1)

    def test_action_view_availability(self):
        allotment = self._create_confirmed_allotment(quota=5)
        action = allotment.action_view_availability()
        self.assertEqual(action["res_model"], "ganafote.hotel.availability")
        self.assertIn(("allotment_id", "=", allotment.id), action["domain"])

    def test_action_view_bookings(self):
        allotment = self._create_confirmed_allotment(quota=5)
        order = self._create_sale_order(rooms=2)
        order.action_confirm()
        action = allotment.action_view_bookings()
        self.assertEqual(action["res_model"], "sale.order")
        self.assertIn(order.id, action["domain"][0][2])
