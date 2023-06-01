from odoo import models, fields, api, _

class HrExpense(models.Model):
    _inherit = ['hr.expense']

    partner_id = fields.Many2one('res.partner',
                                 string='Vendor',
                                 states={
                                     'draft': [('readonly', False)],
                                     'reported': [('readonly', False)],
                                     'refused': [('readonly', False)]})