from odoo import models, fields, api, _

class BarmexBankOffice(models.Model):
    _name = 'barmex.bank.office'
    _description = 'Barmex Bank office'
    _order = 'id desc'
    _check_company_auto = True

    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.company)

    name = fields.Char(string='Office')