from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _get_mail_template(self):
        """Use the company-specific Gañafote invoice template when available.

        Overriding the standard hook keeps the Odoo 19 send flow intact
        (``account.move.send.wizard``) and only swaps the mail template.
        """
        if len(self) == 1 and self.move_type == "out_invoice":
            template_name = (
                "Ganafote Factura ropa"
                if self.company_id.name == "Gañafote SLU"
                else "Ganafote Factura eventos"
            )
            template = self.env["mail.template"].search(
                [("name", "=", template_name)], limit=1
            )
            if template:
                return template
        return super()._get_mail_template()
