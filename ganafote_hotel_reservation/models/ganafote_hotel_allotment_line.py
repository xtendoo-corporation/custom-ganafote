# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import UserError


class GanafoteHotelAllotmentLine(models.Model):
    _name = "ganafote.hotel.allotment.line"
    _description = "Línea de cupo hotelero"
    _order = "date_start, id"

    allotment_id = fields.Many2one(
        comodel_name="ganafote.hotel.allotment",
        string="Cupo",
        required=True,
        ondelete="cascade",
    )
    company_id = fields.Many2one(
        related="allotment_id.company_id",
        store=True,
        readonly=True,
    )
    currency_id = fields.Many2one(
        related="allotment_id.currency_id",
        store=True,
        readonly=True,
    )
    product_id = fields.Many2one(
        comodel_name="product.product",
        string="Producto/Variante",
        required=True,
        domain="[('is_hotel_product', '=', True)]",
    )
    date_start = fields.Date(string="Fecha inicio", required=True)
    date_end = fields.Date(string="Fecha fin", required=True)
    quota_qty = fields.Integer(
        string="Cantidad cedida",
        required=True,
        default=1,
        help="Número de habitaciones cedidas por noche en este tramo.",
    )
    cost_price = fields.Monetary(
        string="Coste por noche",
        currency_field="currency_id",
    )
    margin_type = fields.Selection(
        selection=[
            ("percent", "Porcentaje"),
            ("fixed", "Importe fijo"),
        ],
        string="Tipo de margen",
        default="percent",
    )
    margin_value = fields.Float(string="Valor margen")
    suggested_price = fields.Monetary(
        string="Precio venta sugerido",
        compute="_compute_suggested_price",
        store=True,
        currency_field="currency_id",
    )
    final_price = fields.Monetary(
        string="Precio venta final",
        currency_field="currency_id",
        help="Precio de venta por habitación/noche. Editable por el usuario.",
    )
    reserved_qty = fields.Integer(
        string="Cantidad reservada",
        compute="_compute_reserved_available",
        help="Máximo de habitaciones reservadas en las noches del tramo.",
    )
    available_qty = fields.Integer(
        string="Cantidad disponible",
        compute="_compute_reserved_available",
        help="Disponibilidad mínima entre las noches del tramo.",
    )
    notes = fields.Char(string="Notas")

    @api.depends("cost_price", "margin_type", "margin_value")
    def _compute_suggested_price(self):
        for line in self:
            if line.margin_type == "percent":
                line.suggested_price = line.cost_price * (
                    1 + (line.margin_value or 0.0) / 100.0
                )
            else:
                line.suggested_price = line.cost_price + (line.margin_value or 0.0)

    def _compute_reserved_available(self):
        availability_model = self.env["ganafote.hotel.availability"]
        for line in self:
            availabilities = availability_model.search(
                [("allotment_line_id", "=", line.id)]
            )
            if availabilities:
                line.reserved_qty = max(availabilities.mapped("reserved_qty"))
                line.available_qty = min(availabilities.mapped("available_qty"))
            else:
                line.reserved_qty = 0
                line.available_qty = line.quota_qty

    @api.onchange("suggested_price")
    def _onchange_suggested_price(self):
        for line in self:
            if not line.final_price:
                line.final_price = line.suggested_price

    @api.constrains("date_start", "date_end")
    def _check_dates(self):
        for line in self:
            if line.date_end <= line.date_start:
                raise UserError(
                    self.env._(
                        "La fecha de fin debe ser posterior a la fecha de inicio "
                        "en las líneas de cupo."
                    )
                )

    @api.constrains("quota_qty")
    def _check_quota(self):
        for line in self:
            if line.quota_qty <= 0:
                raise UserError(
                    self.env._("La cantidad de cupo debe ser mayor que cero.")
                )
