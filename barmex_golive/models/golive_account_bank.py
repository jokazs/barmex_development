
from odoo import models, fields, api

class goliveAccountBank(models.Model):
    _inherit = 'account.bank.statement.line'

    statement_ids = fields.Many2one ('account.bank.statement')
    name_account = fields.Char('Referencia', related='statement_ids.name', store=True)

    # line_account_ids = fields.One2many('account.bank.statement.line', 
    #                                     'statement_id', 
    #                                     string='Statement lines')

    