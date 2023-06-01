from ast import Store
from odoo import models, fields, api, _

class Extractos(models.Model):
    _inherit = 'account.bank.statement.line'

    @api.depends('amount')
    def _get_ie(self):
        for record in self:
            if record.amount > 0:
                record.validador_ei = True
                record.transaction_type = 'ingreso'
            else:
                record.validador_ei = False
                record.transaction_type = 'egreso'
    
    #Cambios para Extracto bancario en golive
    @api.onchange('amount')
    def type_trans(self):
        for record in self:
            if record.transaction_type == 'ingreso':
                if record.amount > 0:
                    record.amount = record.amount
                else:
                    record.amount = record.amount * (-1)
            else:
                if record.amount > 0:
                    record.amount = record.amount * (-1)
                else:
                    record.amount = record.amount 

    validador_ei = fields.Boolean('Validador', compute=_get_ie)
    transaction_type = fields.Selection([('ingreso', 'Ingreso'),('egreso', 'Egreso')], compute=_get_ie)     
  
    # search = '_search_transaction'
    # def _search_transaction(self, operator, value):
    #     now = fields.amount.now()
    #     ids = self.env['account.bank.statement.line'].search([('transaction_type', '<', 'ingreso')])
    #     return [('id', 'in', ids)]


class Extracto(models.Model):
    _inherit = 'account.bank.statement'

    @api.depends('line_ids')
    def _compute_transaction_types(self):
        for res in self:
            line_ingresos_ids = res.line_ids.filtered(lambda x: x.amount > 0)
            line_egresos_ids = res.line_ids.filtered(lambda x: x.amount < 0)
            res.line_ingresos_ids = [(6, 0, [x.id for x in line_ingresos_ids])]
            res.line_egresos_ids = [(6, 0, [x.id for x in line_egresos_ids])]

    line_ingresos_ids = fields.One2many('account.bank.statement.line', 'statement_id', string='Statement lines', states={'confirm': [('readonly', True)]}, copy=True, compute='_compute_transaction_types')

    line_egresos_ids = fields.One2many('account.bank.statement.line', 'statement_id', string='Statement lines', states={'confirm': [('readonly', True)]}, copy=True, compute='_compute_transaction_types')
