# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import UserError


class GanafoteHotelAllotment(models.Model):
    _name = "ganafote.hotel.allotment"
    _description = "Cupo hotelero"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date_start desc, id desc"

    name = fields.Char(
        string="Nombre",
        required=True,
        default=lambda self: self.env._("Nuevo"),
        copy=False,
    )
    hotel_id = fields.Many2one(
        comodel_name="res.partner",
        string="Hotel",
        required=True,
        tracking=True,
    )
    date_start = fields.Date(string="Fecha inicio", required=True, tracking=True)
    date_end = fields.Date(string="Fecha fin", required=True, tracking=True)
    state = fields.Selection(
        selection=[
            ("draft", "Borrador"),
            ("confirmed", "Confirmado"),
            ("cancelled", "Cancelado"),
        ],
        string="Estado",
        default="draft",
        required=True,
        tracking=True,
        copy=False,
    )
    line_ids = fields.One2many(
        comodel_name="ganafote.hotel.allotment.line",
        inverse_name="allotment_id",
        string="Líneas de cupo",
        copy=True,
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Compañía",
        required=True,
        default=lambda self: self.env.company,
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Moneda",
        related="company_id.currency_id",
        store=True,
        readonly=True,
    )
    notes = fields.Text(string="Notas")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", self.env._("Nuevo")) == self.env._("Nuevo"):
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "ganafote.hotel.allotment"
                ) or self.env._("Nuevo")
        return super().create(vals_list)

    availability_ids = fields.One2many(
        comodel_name="ganafote.hotel.availability",
        inverse_name="allotment_id",
        string="Disponibilidad diaria",
    )
    availability_count = fields.Integer(
        string="Días de disponibilidad",
        compute="_compute_counts",
    )
    booking_count = fields.Integer(
        string="Reservas",
        compute="_compute_counts",
    )

    @api.depends("availability_ids")
    def _compute_counts(self):
        sale_line = self.env["sale.order.line"]
        for allotment in self:
            allotment.availability_count = len(allotment.availability_ids)
            allotment.booking_count = sale_line.search_count(
                [
                    ("allotment_id", "=", allotment.id),
                    ("hotel_blocked", "=", True),
                ]
            )

    @api.constrains("date_start", "date_end")
    def _check_dates(self):
        for allotment in self:
            if allotment.date_end <= allotment.date_start:
                raise UserError(
                    self.env._(
                        "La fecha de fin debe ser posterior a la fecha de inicio."
                    )
                )

    def action_confirm(self):
        for allotment in self:
            allotment._check_confirmable()
            allotment._check_overlaps()
            allotment._generate_availability()
            allotment.state = "confirmed"
        return True

    def action_cancel(self):
        for allotment in self:
            allotment._check_no_active_bookings()
            allotment.availability_ids.unlink()
            allotment.state = "cancelled"
        return True

    def action_draft(self):
        for allotment in self:
            if allotment.state == "confirmed":
                allotment._check_no_active_bookings()
                allotment.availability_ids.unlink()
            allotment.state = "draft"
        return True

    def _check_confirmable(self):
        self.ensure_one()
        if not self.line_ids:
            raise UserError(
                self.env._("No se puede confirmar un cupo sin líneas.")
            )

    def _check_overlaps(self):
        """Evita solapamientos de noches para el mismo hotel + variante en
        cupos confirmados distintos."""
        self.ensure_one()
        availability = self.env["ganafote.hotel.availability"]
        for line in self.line_ids:
            nights = availability._get_nights(line.date_start, line.date_end)
            overlapping = availability.search(
                [
                    ("hotel_id", "=", self.hotel_id.id),
                    ("product_id", "=", line.product_id.id),
                    ("date", "in", nights),
                    ("allotment_id", "!=", self.id),
                    ("company_id", "=", self.company_id.id),
                ],
                limit=1,
            )
            if overlapping:
                raise UserError(
                    self.env._(
                        "Este cupo se solapa con otro cupo confirmado para el "
                        "mismo hotel y producto. Introduce los tramos de fechas "
                        "por separado."
                    )
                )

    def _check_no_active_bookings(self):
        self.ensure_one()
        active_bookings = self.env["sale.order.line"].search_count(
            [
                ("allotment_id", "=", self.id),
                ("hotel_blocked", "=", True),
            ]
        )
        if active_bookings:
            raise UserError(
                self.env._(
                    "No se puede cancelar este cupo porque ya existen reservas "
                    "confirmadas."
                )
            )

    def _generate_availability(self):
        """Genera (o regenera) los registros de disponibilidad diaria por noche."""
        self.ensure_one()
        availability = self.env["ganafote.hotel.availability"]
        self.availability_ids.unlink()
        values = []
        for line in self.line_ids:
            for night in availability._get_nights(line.date_start, line.date_end):
                values.append(
                    {
                        "allotment_id": self.id,
                        "allotment_line_id": line.id,
                        "hotel_id": self.hotel_id.id,
                        "product_id": line.product_id.id,
                        "date": night,
                        "total_qty": line.quota_qty,
                        "company_id": self.company_id.id,
                    }
                )
        if values:
            availability.create(values)

    def action_view_availability(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Disponibilidad"),
            "res_model": "ganafote.hotel.availability",
            "view_mode": "list,form",
            "domain": [("allotment_id", "=", self.id)],
            "context": {"search_default_group_by_product": 1},
        }

    def action_view_bookings(self):
        self.ensure_one()
        sale_lines = self.env["sale.order.line"].search(
            [("allotment_id", "=", self.id)]
        )
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Reservas"),
            "res_model": "sale.order",
            "view_mode": "list,form",
            "domain": [("id", "in", sale_lines.order_id.ids)],
        }
