# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _find_mail_template(self):
        """Use the company-specific Gañafote quotation template when available.

        Overriding the standard hook keeps the Odoo 19 send flow intact
        (``default_res_ids``, layout configurator, mass mail) and only swaps
        the mail template.
        """
        self.ensure_one()
        template_name = (
            "Ganafote Presupuestos ropa"
            if self.company_id.name == "Gañafote SLU"
            else "Ganafote Presupuestos eventos"
        )
        template = self.env["mail.template"].search(
            [("name", "=", template_name)], limit=1
        )
        return template or super()._find_mail_template()
