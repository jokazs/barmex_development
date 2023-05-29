from odoo import models, fields, api

class accountBankStatement(models.Model):
    _inherit = 'account.bank.statement.line'

    cobrador_id = fields.Many2one('hr.employee', 'Cobrador', ondelete='cascade')