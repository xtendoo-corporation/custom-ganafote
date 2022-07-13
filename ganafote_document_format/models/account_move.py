from odoo import _, models
from odoo.tools.misc import get_lang


class AccountMove(models.Model):
    _inherit = "account.move"

    def action_invoice_sent(self):
        """Open a window to compose an email, with the edi invoice template
        message loaded by default
        """
        self.ensure_one()
        template_id = (
            self.env["mail.template"].search([("name", "=", "Factura")], limit=1).id
        )
        template = self.env["mail.template"].browse(template_id)
        lang = False
        if template:
            lang = template._render_lang(self.ids)[self.id]
        if not lang:
            lang = get_lang(self.env).code
        compose_form = self.env.ref(
            "account.account_invoice_send_wizard_form", raise_if_not_found=False
        )
        ctx = dict(
            default_model="account.move",
            default_res_id=self.id,
            # For the sake of consistency we need a default_res_model if
            # default_res_id is set. Not renaming default_model as it can
            # create many side-effects.
            default_res_model="account.move",
            default_use_template=bool(template),
            default_template_id=template and template.id or False,
            default_composition_mode="comment",
            mark_invoice_as_sent=True,
            custom_layout="mail.mail_notification_paynow",
            model_description=self.with_context(lang=lang).type_name,
            force_email=True,
        )
        return {
            "name": _("Send Invoice"),
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form",
            "res_model": "account.invoice.send",
            "views": [(compose_form.id, "form")],
            "view_id": compose_form.id,
            "target": "new",
            "context": ctx,
        }
