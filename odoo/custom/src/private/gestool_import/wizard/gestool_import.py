import logging
from base64 import b64decode
from io import StringIO

from odoo import _, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

try:
    from csv import reader
except (OSError, ImportError) as err:
    _logger.error(err)


class GestoolImport(models.TransientModel):
    _name = "gestool.import"
    _description = "Importador desde Gestool"

    data_file_agentes = fields.Binary(
        string="File to Import",
        required=False,
        help="Get you data from Gestool.",
    )
    filename = fields.Char()

    data_file_partner = fields.Binary(
        string="File to Import",
        required=False,
        help="Get you data from Gestool.",
    )
    filename = fields.Char()

    data_file_category = fields.Binary(
        string="File to Import",
        required=False,
        help="Get you data from Gestool.",
    )
    filename = fields.Char()

    data_file_product = fields.Binary(
        string="File to Import",
        required=False,
        help="Get you data from Gestool.",
    )
    filename = fields.Char()

    def import_file(self):
        """Process the file chosen in the wizard, create bank statement(s)
        and go to reconciliation."""
        self.ensure_one()

        data_file_agentes = b64decode(self.data_file_agentes)
        if data_file_agentes:
            self._import_agentes(data_file_agentes)

        data_file_partner = b64decode(self.data_file_partner)
        if data_file_partner:
            self._import_partner(data_file_partner)

        data_file_category = b64decode(self.data_file_category)
        if data_file_category:
            self._import_category(data_file_category)

        data_file_product = b64decode(self.data_file_product)
        if data_file_product:
            self._import_product(data_file_product)

    def _import_partner(self, data_file_partner):
        try:
            csv_data = reader(StringIO(data_file_partner.decode("utf-8")))
        except Exception as err:
            raise UserError(_("Can not read the file")) from err

        for row in csv_data:
            _logger.debug("-------------------- CLIENTES --------------------------")
            self.parse_partner(row)
        return

    def parse_partner(self, row):
        partner = self.env["res.partner"].search(
            [
                ("ref", "=", row[0]),
            ]
        )

        # country_id = self.env["res.country"].search([("name", "=", "España", ])
        # if country_id:
        #     country_id = country_id.id

        state_id = self.env["res.country.state"].search(
            [
                ("name", "=", row[6].capitalize()),
            ]
        )
        if state_id:
            state_id = state_id.id

        # agent_id = self.env["res.partner"].search([("name", "=", row[23]), ])
        # if agent_id:
        #     agent_id = [(6, 0, [agent_id.id])]
        # else:
        #     agent_id = [(6, 0, [])]

        _logger.debug(
            "CLIENTE: partner=%s nombre=%s ref=%s street=%s city=%s zip=%s "
            "phone=%s mobile=%s website=%s email=%s display_name=%s "
            "company_name=%s comment=%s customer_rank=%s supplier_rank=%s "
            "company=%s state=%s state_id=%s dni=%s",
            partner,
            row[1],
            row[0],
            row[3],
            row[4],
            row[5],
            row[7],
            row[8],
            row[9],
            row[10],
            row[14],
            row[15],
            row[17],
            row[19],
            row[20],
            row[25],
            row[6].capitalize(),
            state_id,
            row[2],
        )

        if partner:
            partner.sudo().write(
                {
                    "name": row[1],
                    "street": row[3],
                    "city": row[4],
                    "zip": row[5],
                    "phone": row[7],
                    "mobile": row[8],
                    "website": row[9],
                    "email": row[10],
                    "display_name": row[14],
                    "company_name": row[15],
                    "comment": row[17],
                    "state_id": state_id,
                    "vat": row[2],
                    "country_id": 68,
                    # 'agent_ids': agent_id,
                }
            )
        else:
            self.env["res.partner"].sudo().create(
                {
                    "ref": row[0],
                    "name": row[1],
                    "street": row[3],
                    "city": row[4],
                    "zip": row[5],
                    "phone": row[7],
                    "mobile": row[8],
                    "website": row[9],
                    "email": row[10],
                    "display_name": row[14],
                    "company_name": row[15],
                    "is_company": 1,
                    "active": 1,
                    "comment": row[17],
                    "customer_rank": row[19],
                    "supplier_rank": row[20],
                    "company_id": 1,
                    "lang": "es_ES",
                    "state_id": state_id,
                    "vat": row[2],
                    "country_id": 68,
                    # 'agent_ids': agent_id,
                }
            )

    def _import_category(self, data_file_category):
        try:
            csv_data = reader(StringIO(data_file_category.decode("utf-8")))
        except Exception as err:
            raise UserError(_("Can not read the file")) from err

        for _row in csv_data:
            # self.parse_categories(_row)
            _logger.debug("-------------------- CATEGORY --------------------------")
        return

    def parse_categories(self, row):
        category = self.env["product.category"].search(
            [
                ("name", "=", row[0]),
            ]
        )
        if not category:
            self.env["product.category"].create(
                {
                    "name": row[0],
                    "parent_id": 1,
                }
            )

    def _import_product(self, data_file_product):
        try:
            csv_data = reader(StringIO(data_file_product.decode("utf-8")))
        except Exception as err:
            raise UserError(_("Can not read the file")) from err

        for row in csv_data:
            _logger.debug("-------------------- PRODUCT --------------------------")
            self.parse_products(row)
        return

    def parse_products(self, row):
        _logger.debug("-------------------- PRODUCT -------------------------- %s", row)

        taxes_id = self.env["account.tax"].search(
            [
                ("name", "=", row[7]),
            ]
        )
        if taxes_id:
            taxes_id = [(6, 0, [taxes_id.id])]
        else:
            taxes_id = [(6, 0, [])]

        supplier_taxes_id = self.env["account.tax"].search(
            [
                ("name", "=", row[8]),
            ]
        )
        if supplier_taxes_id:
            supplier_taxes_id = [(6, 0, [supplier_taxes_id.id])]
        else:
            supplier_taxes_id = [(6, 0, [])]

        product = self.env["product.template"].search(
            [
                ("name", "=", row[2]),
            ]
        )

        if not product:
            self.env["product.template"].create(
                {
                    "name": row[2],
                    "list_price": row[5],
                    "standard_price": row[6],
                    "available_in_pos": 1,
                    "taxes_id": taxes_id,
                    "supplier_taxes_id": supplier_taxes_id,
                }
            )
        else:
            product.sudo().write(
                {
                    "name": row[2],
                    "list_price": row[5],
                    "standard_price": row[6],
                    "available_in_pos": 1,
                    "taxes_id": taxes_id,
                    "supplier_taxes_id": supplier_taxes_id,
                }
            )

    def _import_agentes(self, data_file_agentes):
        try:
            csv_data = reader(StringIO(data_file_agentes.decode("utf-8")))
        except Exception as err:
            raise UserError(_("Can not read the file")) from err

        for _row in csv_data:
            # self.parse_agentes(_row)
            _logger.debug("-------------------- AGENTES --------------------------")
        return

    # def parse_agentes(self, row):
    #     agente = self.env["res.partner"].search([("ref", "=", row[0]), ])
    #     if agente:
    #         agente.write({
    #             "name": row[1],
    #             'email': row[10],
    #             'display_name': row[1],
    #             'is_company': 0,
    #             'active': 1,
    #             'customer_rank': 0,
    #             'supplier_rank': 0,
    #             'agent':1,
    #         })
    #     else:
    #         self.env["res.partner"].create({
    #             "ref": row[0],
    #             "name": row[1],
    #             'email': row[10],
    #             'display_name': row[1],
    #             'is_company': 0,
    #             'active': 1,
    #             'customer_rank': 0,
    #             'supplier_rank': 0,
    #             'agent':1,
    #         })
