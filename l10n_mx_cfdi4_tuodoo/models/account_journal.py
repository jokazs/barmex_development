from odoo import _, api, fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    type_cfdi = fields.Selection(
        [('33', '3.3'),
         ('40', '4.0'),],
         default="33",
        string="Facturacion",)
