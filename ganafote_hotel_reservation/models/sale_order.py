# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def action_confirm(self):
        for order in self:
            order._check_hotel_lines_data()
            order._check_hotel_availability()
        result = super().action_confirm()
        for order in self:
            order._hotel_lines()._block_availability()
        return result

    def _action_cancel(self):
        for order in self:
            order._hotel_lines()._release_availability()
            if order._has_posted_invoices():
                order.message_post(
                    body=self.env._(
                        "Se ha cancelado el pedido y liberado las habitaciones "
                        "bloqueadas. Existen facturas o anticipos asociados: revise "
                        "manualmente la regularización contable."
                    )
                )
        return super()._action_cancel()

    def _hotel_lines(self):
        return self.order_line.filtered("is_hotel_line")

    def _has_posted_invoices(self):
        self.ensure_one()
        return bool(self.invoice_ids.filtered(lambda move: move.state == "posted"))

    def _check_hotel_lines_data(self):
        self.ensure_one()
        for line in self._hotel_lines():
            if not line.checkin_date or not line.checkout_date:
                raise UserError(
                    self.env._(
                        "La línea «%(product)s» es un producto hotelero y debe "
                        "tener fecha de entrada y de salida.",
                        product=line.product_id.display_name,
                    )
                )
            if line.room_qty <= 0:
                raise UserError(
                    self.env._(
                        "La línea «%(product)s» debe indicar un número de "
                        "habitaciones mayor que cero.",
                        product=line.product_id.display_name,
                    )
                )

    def _check_hotel_availability(self):
        self.ensure_one()
        availability = self.env["ganafote.hotel.availability"]
        for line in self._hotel_lines():
            if line.hotel_blocked:
                continue
            missing = availability.check_availability(
                line.product_id.id,
                line.checkin_date,
                line.checkout_date,
                line.room_qty,
                line.company_id.id,
            )
            if missing:
                raise UserError(
                    self.env._(
                        "No hay disponibilidad suficiente para %(product)s entre "
                        "el %(date_from)s y el %(date_to)s.",
                        product=line.product_id.display_name,
                        date_from=min(missing).strftime("%d/%m/%Y"),
                        date_to=line.checkout_date.strftime("%d/%m/%Y"),
                    )
                )
