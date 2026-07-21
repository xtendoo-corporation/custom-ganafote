# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    company_so_factory_template_id = fields.Many2one(
        related="company_id.sale_order_factory_template_id",
        string="Factory Default Template",
        readonly=False,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
    )

    send_invoice_mail_template_id = fields.Many2one(
        comodel_name="mail.template",
        string="Plantilla de Correo para Entregas",
        domain="[('model', '=', 'account.move')]",
        config_parameter="sale.default_send_invoice_email_template",
        default=lambda self: self.env.ref("account.email_template_edi_invoice", False),
    )
