# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import UserError


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    is_hotel_line = fields.Boolean(
        string="Línea hotelera",
        related="product_id.is_hotel_product",
        store=True,
    )
    checkin_date = fields.Date(string="Fecha entrada")
    checkout_date = fields.Date(string="Fecha salida")
    nights = fields.Integer(
        string="Número de noches",
        compute="_compute_nights",
        store=True,
    )
    room_qty = fields.Integer(string="Número de habitaciones", default=1)
    availability_info = fields.Char(
        string="Disponibilidad",
        compute="_compute_availability_info",
    )
    allotment_id = fields.Many2one(
        comodel_name="ganafote.hotel.allotment",
        string="Cupo bloqueado",
        readonly=True,
        copy=False,
        help="Cupo cuyo stock quedó bloqueado al confirmar esta línea.",
    )
    hotel_blocked = fields.Boolean(
        string="Cupo bloqueado",
        readonly=True,
        copy=False,
        help="Indica si la línea está consumiendo disponibilidad actualmente.",
    )

    @api.depends("checkin_date", "checkout_date")
    def _compute_nights(self):
        availability = self.env["ganafote.hotel.availability"]
        for line in self:
            line.nights = len(
                availability._get_nights(line.checkin_date, line.checkout_date)
            )

    @api.depends(
        "is_hotel_line",
        "product_id",
        "checkin_date",
        "checkout_date",
        "room_qty",
    )
    def _compute_availability_info(self):
        availability = self.env["ganafote.hotel.availability"]
        for line in self:
            if not line._has_hotel_data():
                line.availability_info = False
                continue
            missing = availability.check_availability(
                line.product_id.id,
                line.checkin_date,
                line.checkout_date,
                line.room_qty,
                line.company_id.id,
            )
            if missing:
                line.availability_info = self.env._(
                    "Sin disponibilidad suficiente en %(count)s noche(s).",
                    count=len(missing),
                )
            else:
                line.availability_info = self.env._("Disponibilidad orientativa: OK")

    def _has_hotel_data(self):
        self.ensure_one()
        return bool(
            self.is_hotel_line
            and self.product_id
            and self.checkin_date
            and self.checkout_date
            and self.room_qty > 0
        )

    @api.onchange("checkin_date", "checkout_date", "room_qty", "is_hotel_line")
    def _onchange_hotel_quantity(self):
        for line in self:
            if line.is_hotel_line and line.nights and line.room_qty > 0:
                line.product_uom_qty = line.room_qty * line.nights

    @api.constrains("checkin_date", "checkout_date", "is_hotel_line")
    def _check_hotel_dates(self):
        for line in self:
            if not line.is_hotel_line:
                continue
            if line.checkin_date and line.checkout_date:
                if line.checkout_date <= line.checkin_date:
                    raise UserError(
                        self.env._(
                            "La fecha de salida debe ser posterior a la fecha de "
                            "entrada."
                        )
                    )

    def _block_availability(self):
        """Bloquea la disponibilidad de las líneas hoteleras aún no bloqueadas."""
        availability = self.env["ganafote.hotel.availability"]
        for line in self.filtered(
            lambda record: record.is_hotel_line and not record.hotel_blocked
        ):
            allotment = availability._records_for(
                line.product_id.id,
                line.checkin_date,
                line.checkout_date,
                line.company_id.id,
            )[:1].allotment_id
            availability.reserve(
                line.product_id.id,
                line.checkin_date,
                line.checkout_date,
                line.room_qty,
                line.company_id.id,
            )
            line.write({"allotment_id": allotment.id, "hotel_blocked": True})

    def _release_availability(self):
        """Libera la disponibilidad de las líneas hoteleras bloqueadas."""
        availability = self.env["ganafote.hotel.availability"]
        for line in self.filtered("hotel_blocked"):
            availability.release(
                line.product_id.id,
                line.checkin_date,
                line.checkout_date,
                line.room_qty,
                line.company_id.id,
            )
            line.hotel_blocked = False
