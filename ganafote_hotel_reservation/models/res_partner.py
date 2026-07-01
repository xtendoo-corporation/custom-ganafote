# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    is_hotel = fields.Boolean(
        string="Es un Hotel",
        default=False,
        help="Check this box if this contact is a hotel.",
    )

