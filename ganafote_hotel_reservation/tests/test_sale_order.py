# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from unittest.mock import patch

from odoo.exceptions import UserError
from odoo.tests.common import tagged

from .common import HotelReservationCommon


@tagged("post_install", "-at_install")
class TestSaleOrder(HotelReservationCommon):
    """Tests del flujo de venta: bloqueo al confirmar y liberación al cancelar."""

    # ------------------------------------------------------------------
    # Confirmación: bloqueo de disponibilidad
    # ------------------------------------------------------------------
    def test_confirm_blocks_availability(self):
        allotment = self._create_confirmed_allotment(quota=5)
        order = self._create_sale_order(rooms=2)
        order.action_confirm()
        line = order.order_line
        self.assertTrue(line.hotel_blocked)
        self.assertEqual(line.allotment_id, allotment)
        for record in allotment.availability_ids:
            self.assertEqual(record.reserved_qty, 2)

    def test_confirm_insufficient_raises(self):
        self._create_confirmed_allotment(quota=2)
        order = self._create_sale_order(rooms=3)
        with self.assertRaises(UserError):
            order.action_confirm()

    def test_confirm_without_cupo_raises(self):
        order = self._create_sale_order(rooms=1)
        with self.assertRaises(UserError):
            order.action_confirm()

    def test_confirm_missing_dates_raises(self):
        self._create_confirmed_allotment(quota=5)
        order = self.env["sale.order"].create({"partner_id": self.customer.id})
        self.env["sale.order.line"].create(
            {
                "order_id": order.id,
                "product_id": self.hotel_product.id,
                "room_qty": 1,
                "product_uom_qty": 1,
            }
        )
        with self.assertRaises(UserError):
            order.action_confirm()

    def test_confirm_zero_rooms_raises(self):
        self._create_confirmed_allotment(quota=5)
        order = self._create_sale_order(rooms=1)
        order.order_line.room_qty = 0
        with self.assertRaises(UserError):
            order.action_confirm()

    def test_confirm_multiple_hotel_lines(self):
        allotment_a = self._create_confirmed_allotment(
            product=self.hotel_product, quota=5
        )
        allotment_b = self._create_confirmed_allotment(
            product=self.hotel_product_alt, quota=5
        )
        order = self.env["sale.order"].create({"partner_id": self.customer.id})
        nights = (self.date_end - self.date_start).days
        for product in (self.hotel_product, self.hotel_product_alt):
            self.env["sale.order.line"].create(
                {
                    "order_id": order.id,
                    "product_id": product.id,
                    "checkin_date": self.date_start,
                    "checkout_date": self.date_end,
                    "room_qty": 1,
                    "product_uom_qty": nights,
                }
            )
        order.action_confirm()
        self.assertTrue(all(order.order_line.mapped("hotel_blocked")))
        self.assertEqual(allotment_a.availability_ids[0].reserved_qty, 1)
        self.assertEqual(allotment_b.availability_ids[0].reserved_qty, 1)

    def test_non_hotel_order_confirms_normally(self):
        order = self._create_sale_order(product=self.regular_product, rooms=3)
        order.action_confirm()
        self.assertEqual(order.state, "sale")
        self.assertFalse(order.order_line.hotel_blocked)

    def test_double_block_does_not_duplicate(self):
        allotment = self._create_confirmed_allotment(quota=5)
        order = self._create_sale_order(rooms=2)
        order.action_confirm()
        # Volver a invocar el bloqueo no debe descontar dos veces.
        order._hotel_lines()._block_availability()
        self.assertEqual(allotment.availability_ids[0].reserved_qty, 2)

    # ------------------------------------------------------------------
    # Cancelación: liberación de disponibilidad
    # ------------------------------------------------------------------
    def test_cancel_releases_availability(self):
        allotment = self._create_confirmed_allotment(quota=5)
        order = self._create_sale_order(rooms=2)
        order.action_confirm()
        order._action_cancel()
        self.assertFalse(order.order_line.hotel_blocked)
        for record in allotment.availability_ids:
            self.assertEqual(record.reserved_qty, 0)

    def test_cancel_keeps_traceability(self):
        allotment = self._create_confirmed_allotment(quota=5)
        order = self._create_sale_order(rooms=2)
        order.action_confirm()
        order._action_cancel()
        line = order.order_line
        # Se conserva el cupo asignado y los datos de la línea como traza.
        self.assertEqual(line.allotment_id, allotment)
        self.assertEqual(line.checkin_date, self.date_start)
        self.assertEqual(line.room_qty, 2)

    def test_cancel_without_invoice_no_warning(self):
        self._create_confirmed_allotment(quota=5)
        order = self._create_sale_order(rooms=2)
        order.action_confirm()
        order._action_cancel()
        self.assertFalse(order._has_posted_invoices())
        self.assertFalse(
            any(
                "regularización contable" in (m.body or "")
                for m in order.message_ids
            )
        )

    def test_cancel_with_posted_invoice_posts_warning(self):
        self._create_confirmed_allotment(quota=5)
        order = self._create_sale_order(rooms=2)
        order.action_confirm()
        with patch.object(
            type(order), "_has_posted_invoices", return_value=True
        ):
            order._action_cancel()
        self.assertTrue(
            any(
                "regularización contable" in (m.body or "")
                for m in order.message_ids
            )
        )

    def test_reconfirm_after_cancel_reblocks(self):
        allotment = self._create_confirmed_allotment(quota=5)
        order = self._create_sale_order(rooms=2)
        order.action_confirm()
        order._action_cancel()
        order.action_draft()
        order.action_confirm()
        self.assertTrue(order.order_line.hotel_blocked)
        self.assertEqual(allotment.availability_ids[0].reserved_qty, 2)
