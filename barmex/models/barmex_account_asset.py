from odoo import models, fields, api, _

class AccountMove(models.Model):
    _inherit = ['account.asset']

    employee_id = fields.Many2one('hr.employee',
                                  string='Responsible')