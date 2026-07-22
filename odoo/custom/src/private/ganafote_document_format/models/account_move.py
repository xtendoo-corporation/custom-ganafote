from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _get_mail_template(self):
        if len(self) == 1 and self.move_type == "out_invoice":
            if self.company_id.name == "Gañafote SLU":
                template_name = "Ganafote Factura ropa"
            else:
                template_name = "Ganafote Factura eventos"
            template = self.env["mail.template"].search(
                [("name", "=", template_name)], limit=1
            )
            if template:
                return template
        return super()._get_mail_template()
