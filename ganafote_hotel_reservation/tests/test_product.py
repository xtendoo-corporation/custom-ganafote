# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import tagged

from .common import HotelReservationCommon


@tagged("post_install", "-at_install")
class TestProduct(HotelReservationCommon):
    """Tests de la extensión de producto hotelero."""

    def test_hotel_fields_set(self):
        self.assertTrue(self.hotel_product.is_hotel_product)
        self.assertEqual(self.hotel_product.hotel_id, self.hotel)

    def test_regular_product_not_hotel(self):
        self.assertFalse(self.regular_product.is_hotel_product)
        self.assertFalse(self.regular_product.hotel_id)

    def test_variant_inherits_hotel_flag(self):
        attribute = self.env["product.attribute"].create(
            {"name": "Tipo", "create_variant": "always"}
        )
        value_doble = self.env["product.attribute.value"].create(
            {"name": "Doble", "attribute_id": attribute.id}
        )
        value_individual = self.env["product.attribute.value"].create(
            {"name": "Individual", "attribute_id": attribute.id}
        )
        template = self.env["product.template"].create(
            {
                "name": "Pernoctación con variantes",
                "type": "service",
                "is_hotel_product": True,
                "hotel_id": self.hotel.id,
                "attribute_line_ids": [
                    (
                        0,
                        0,
                        {
                            "attribute_id": attribute.id,
                            "value_ids": [
                                (6, 0, [value_doble.id, value_individual.id])
                            ],
                        },
                    )
                ],
            }
        )
        self.assertEqual(len(template.product_variant_ids), 2)
        self.assertTrue(
            all(template.product_variant_ids.mapped("is_hotel_product"))
        )
