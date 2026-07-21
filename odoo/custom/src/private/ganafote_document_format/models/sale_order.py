# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def action_quotation_send(self):
        """Opens a wizard to compose an email, with relevant mail template
        loaded by default"""
        self.ensure_one()
        if self.company_id.name == "Gañafote SLU":
            template_id = (
                self.env["mail.template"]
                .search([("name", "=", "Ganafote Presupuestos ropa")], limit=1)
                .id
            )
        else:
            template_id = (
                self.env["mail.template"]
                .search([("name", "=", "Ganafote Presupuestos eventos")], limit=1)
                .id
            )
        lang = self.env.context.get("lang")
        template = self.env["mail.template"].browse(template_id)
        if template.lang:
            lang = template._render_lang(self.ids)[self.id]
        ctx = {
            "default_model": "sale.order",
            "default_res_id": self.ids[0],
            "default_use_template": bool(template_id),
            "default_template_id": template_id,
            "default_composition_mode": "comment",
            "mark_so_as_sent": True,
            "custom_layout": "mail.mail_notification_paynow",
            "proforma": self.env.context.get("proforma", False),
            "force_email": True,
            "model_description": self.with_context(lang=lang).type_name,
        }
        return {
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "mail.compose.message",
            "views": [(False, "form")],
            "view_id": False,
            "target": "new",
            "context": ctx,
        }
