# Copyright 2026
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, tools


class MailMail(models.Model):
    _inherit = "mail.mail"

    def _send_prepare_values(self, partner=None):
        res = super()._send_prepare_values(partner)
        if self.mailing_id and res.get("body") and res.get("email_to"):
            emails = tools.email_split(res["email_to"][0])
            email_to = emails[0] if emails else False
            if email_to and self.res_id:
                res["body"] = self.mailing_id._replace_placeholder_urls(
                    res["body"], email_to, self.res_id
                )
        return res

