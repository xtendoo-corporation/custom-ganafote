# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date

from odoo.exceptions import UserError
from odoo.tests import Form
from odoo.tests.common import tagged

from .common import HotelReservationCommon


@tagged("post_install", "-at_install")
class TestSaleOrderLine(HotelReservationCommon):
    """Tests de la extensión de la línea de venta hotelera."""

    def test_nights_computed(self):
        order = self._create_sale_order(rooms=1)
        self.assertEqual(order.order_line.nights, 7)

    def test_is_hotel_line_related(self):
        order = self._create_sale_order(rooms=1)
        self.assertTrue(order.order_line.is_hotel_line)

    def test_regular_line_not_hotel(self):
        order = self._create_sale_order(product=self.regular_product, rooms=3)
        self.assertFalse(order.order_line.is_hotel_line)
        self.assertEqual(order.order_line.product_uom_qty, 3)

    def test_quantity_is_rooms_times_nights(self):
        order = self._create_sale_order(rooms=2)
        # 2 habitaciones * 7 noches = 14
        self.assertEqual(order.order_line.product_uom_qty, 14)

    def test_onchange_sets_quantity(self):
        self._create_confirmed_allotment(quota=5)
        order = self.env["sale.order"].create({"partner_id": self.customer.id})
        with Form(order) as order_form:
            with order_form.order_line.new() as line:
                line.product_id = self.hotel_product
                line.checkin_date = self.date_start
                line.checkout_date = self.date_end
                line.room_qty = 2
        self.assertEqual(order.order_line.product_uom_qty, 14)

    def test_availability_info_ok(self):
        self._create_confirmed_allotment(quota=5)
        order = self._create_sale_order(rooms=2)
        self.assertIn("OK", order.order_line.availability_info)

    def test_availability_info_insufficient(self):
        self._create_confirmed_allotment(quota=1)
        order = self._create_sale_order(rooms=3)
        self.assertIn("Sin disponibilidad", order.order_line.availability_info)

    def test_availability_info_empty_for_regular(self):
        order = self._create_sale_order(product=self.regular_product, rooms=1)
        self.assertFalse(order.order_line.availability_info)

    def test_dates_constraint(self):
        order = self.env["sale.order"].create({"partner_id": self.customer.id})
        with self.assertRaises(UserError):
            self.env["sale.order.line"].create(
                {
                    "order_id": order.id,
                    "product_id": self.hotel_product.id,
                    "checkin_date": date(2026, 8, 8),
                    "checkout_date": date(2026, 8, 1),
                    "room_qty": 1,
                    "product_uom_qty": 1,
                }
            )
