# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    is_hotel_product = fields.Boolean(
        string="Producto hotelero",
        help="Marca el producto como una pernoctación en un hotel. Habilita la "
        "gestión de fechas y disponibilidad en las líneas de venta.",
    )
    hotel_id = fields.Many2one(
        comodel_name="res.partner",
        string="Hotel",
        help="Proveedor/hotel que cede las habitaciones de esta pernoctación.",
    )
