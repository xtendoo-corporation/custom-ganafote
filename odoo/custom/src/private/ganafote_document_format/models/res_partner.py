# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import fields, models


class Partner(models.Model):
    _inherit = "res.partner"

    translated_display_name = fields.Char(
        compute="_compute_display_name", recursive=True, store=True, index=True
    )
