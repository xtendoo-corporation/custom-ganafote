# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import timedelta

from odoo import api, fields, models


class GanafoteHotelAvailability(models.Model):
    _name = "ganafote.hotel.availability"
    _description = "Disponibilidad hotelera diaria"
    _order = "date, product_id"

    allotment_id = fields.Many2one(
        comodel_name="ganafote.hotel.allotment",
        string="Cupo",
        required=True,
        ondelete="cascade",
        index=True,
    )
    allotment_line_id = fields.Many2one(
        comodel_name="ganafote.hotel.allotment.line",
        string="Línea de cupo",
        required=True,
        ondelete="cascade",
        index=True,
    )
    hotel_id = fields.Many2one(
        comodel_name="res.partner",
        string="Hotel",
        required=True,
        index=True,
    )
    product_id = fields.Many2one(
        comodel_name="product.product",
        string="Producto/Variante",
        required=True,
        index=True,
    )
    date = fields.Date(string="Noche", required=True, index=True)
    total_qty = fields.Integer(string="Cupo total", required=True)
    reserved_qty = fields.Integer(string="Reservado", default=0)
    available_qty = fields.Integer(
        string="Disponible",
        compute="_compute_available_qty",
        store=True,
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Compañía",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )

    _unique_night = models.Constraint(
        "UNIQUE(allotment_line_id, date)",
        "Solo puede existir un registro de disponibilidad por línea de cupo y noche.",
    )

    @api.depends("total_qty", "reserved_qty")
    def _compute_available_qty(self):
        for record in self:
            record.available_qty = record.total_qty - record.reserved_qty

    @api.model
    def _get_nights(self, date_start, date_end):
        """Devuelve la lista de noches ocupadas entre dos fechas.

        La fecha de salida (date_end) no consume disponibilidad.
        """
        if not date_start or not date_end or date_end <= date_start:
            return []
        nights = []
        current = date_start
        while current < date_end:
            nights.append(current)
            current += timedelta(days=1)
        return nights

    @api.model
    def _records_for(self, product_id, date_start, date_end, company_id):
        """Devuelve los registros de disponibilidad para un producto y rango."""
        nights = self._get_nights(date_start, date_end)
        if not nights:
            return self.browse()
        return self.search(
            [
                ("product_id", "=", product_id),
                ("date", "in", nights),
                ("company_id", "=", company_id),
            ]
        )

    @api.model
    def check_availability(self, product_id, date_start, date_end, qty, company_id):
        """Comprueba disponibilidad noche a noche.

        Devuelve la lista de noches (date) sin cupo suficiente. Una lista vacía
        significa que hay disponibilidad para todas las noches solicitadas.
        """
        nights = self._get_nights(date_start, date_end)
        if not nights:
            return nights
        records = self._records_for(product_id, date_start, date_end, company_id)
        availability_by_date = {record.date: record.available_qty for record in records}
        missing = []
        for night in nights:
            if availability_by_date.get(night, 0) < qty:
                missing.append(night)
        return missing

    @api.model
    def reserve(self, product_id, date_start, date_end, qty, company_id):
        """Incrementa la cantidad reservada en las noches del rango."""
        records = self._records_for(product_id, date_start, date_end, company_id)
        for record in records:
            record.reserved_qty += qty

    @api.model
    def release(self, product_id, date_start, date_end, qty, company_id):
        """Libera la cantidad reservada en las noches del rango."""
        records = self._records_for(product_id, date_start, date_end, company_id)
        for record in records:
            record.reserved_qty = max(0, record.reserved_qty - qty)
