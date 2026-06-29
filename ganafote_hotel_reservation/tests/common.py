# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date

from odoo import Command
from odoo.tests.common import TransactionCase


class HotelReservationCommon(TransactionCase):
    """Datos compartidos para los tests de reservas hoteleras.

    Cada producto se crea nuevo en cada clase de test, de modo que las búsquedas
    globales de disponibilidad quedan aisladas de cualquier dato preexistente.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("base.main_company")

        cls.hotel = cls.env["res.partner"].create(
            {
                "name": "Hotel Test Barceló",
                "is_company": True,
                "supplier_rank": 1,
            }
        )
        cls.customer = cls.env["res.partner"].create(
            {
                "name": "Cliente Test",
            }
        )

        # Producto hotelero simple (una sola variante).
        cls.hotel_product = cls.env["product.product"].create(
            {
                "name": "Pernoctación Hotel Test",
                "type": "service",
                "is_hotel_product": True,
                "hotel_id": cls.hotel.id,
                "list_price": 108.0,
            }
        )
        # Segundo producto hotelero para escenarios de variante/producto distinto.
        cls.hotel_product_alt = cls.env["product.product"].create(
            {
                "name": "Pernoctación Hotel Test (Individual)",
                "type": "service",
                "is_hotel_product": True,
                "hotel_id": cls.hotel.id,
                "list_price": 80.0,
            }
        )
        # Producto NO hotelero, para comprobar que el flujo estándar no se rompe.
        cls.regular_product = cls.env["product.product"].create(
            {
                "name": "Servicio normal",
                "type": "service",
                "list_price": 50.0,
            }
        )

        cls.date_start = date(2026, 8, 1)
        cls.date_end = date(2026, 8, 8)

    @classmethod
    def _allotment_line_vals(
        cls,
        product,
        date_start,
        date_end,
        quota,
        cost=90.0,
        margin_type="percent",
        margin_value=20.0,
        final_price=108.0,
    ):
        return {
            "product_id": product.id,
            "date_start": date_start,
            "date_end": date_end,
            "quota_qty": quota,
            "cost_price": cost,
            "margin_type": margin_type,
            "margin_value": margin_value,
            "final_price": final_price,
        }

    @classmethod
    def _create_allotment(cls, lines_vals, hotel=None):
        hotel = hotel or cls.hotel
        return cls.env["ganafote.hotel.allotment"].create(
            {
                "hotel_id": hotel.id,
                "date_start": min(line["date_start"] for line in lines_vals),
                "date_end": max(line["date_end"] for line in lines_vals),
                "line_ids": [Command.create(vals) for vals in lines_vals],
            }
        )

    @classmethod
    def _create_confirmed_allotment(
        cls, product=None, date_start=None, date_end=None, quota=5
    ):
        product = product or cls.hotel_product
        date_start = date_start or cls.date_start
        date_end = date_end or cls.date_end
        allotment = cls._create_allotment(
            [cls._allotment_line_vals(product, date_start, date_end, quota)]
        )
        allotment.action_confirm()
        return allotment

    def _create_sale_order(
        self, product=None, checkin=None, checkout=None, rooms=1, price=108.0
    ):
        product = product or self.hotel_product
        checkin = checkin or self.date_start
        checkout = checkout or self.date_end
        order = self.env["sale.order"].create({"partner_id": self.customer.id})
        line_vals = {
            "order_id": order.id,
            "product_id": product.id,
            "price_unit": price,
        }
        if product.is_hotel_product:
            nights = (checkout - checkin).days
            line_vals.update(
                {
                    "checkin_date": checkin,
                    "checkout_date": checkout,
                    "room_qty": rooms,
                    "product_uom_qty": rooms * nights,
                }
            )
        else:
            line_vals["product_uom_qty"] = rooms
        self.env["sale.order.line"].create(line_vals)
        return order
