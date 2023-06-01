from odoo import models, fields, api, _

class Reason(models.Model):
    _name = 'barmex.writeoff.reason'
    _description = 'Write-off Reason'
    _order = 'id desc'
    _check_company_auto = True

    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.company)

    name = fields.Char(string='Description',
                       required=True)

    account_id = fields.Many2one('account.account',
                                 string='Account',
                                 required=True)