# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _find_mail_template(self):
        self.ensure_one()
        if self.state == "sale" or self.env.context.get("proforma"):
            return super()._find_mail_template()
        if self.company_id.name == "Gañafote SLU":
            template_name = "Ganafote Presupuestos ropa"
        else:
            template_name = "Ganafote Presupuestos eventos"
        template = self.env["mail.template"].search(
            [("name", "=", template_name)], limit=1
        )
        return template or super()._find_mail_template()
