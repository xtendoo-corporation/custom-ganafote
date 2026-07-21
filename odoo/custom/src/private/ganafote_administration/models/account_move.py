# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    sale_order_id = fields.Many2one(
        string="Pedido de Venta",
        comodel_name="sale.order",
        compute="_compute_sale_order_id",
        store=True,
    )
    is_delivered = fields.Boolean(string="Entregado", default=False)

    @api.depends("invoice_origin")
    def _compute_sale_order_id(self):
        for invoice in self:
            sale_order = self.env["sale.order"].search(
                [("name", "=", invoice.invoice_origin)]
            )
            if sale_order:
                invoice.sale_order_id = sale_order.id

    @api.onchange("is_delivered")
    def _send_delivered_mail(self):
        template = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("sale.default_send_invoice_email_template")
        )
        template_id = self.env["mail.template"].search([("id", "=", template)])
        if not template_id:
            return

        for invoice in self.filtered(lambda inv: inv.is_delivered):
            invoice_id = self.env["account.move"].search([("name", "=", invoice.name)])
            if invoice_id:
                template_id.send_mail(
                    invoice_id.id,
                    force_send=False,
                    raise_exception=False,
                    email_values=False,
                )
