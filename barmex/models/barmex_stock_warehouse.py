from odoo import models, fields, api, _

class StockWarehouse(models.Model):
    _inherit = ['stock.warehouse']

    stock_account = fields.Many2one('account.account',
                                    domain="[('user_type_id.include_initial_balance','=',True),('user_type_id.type','=','other'),('user_type_id.internal_group','=','asset')]")