from odoo import models, fields, api, _

class ResPartnerBank(models.Model):
    _inherit = ['res.partner.bank']

    office = fields.Char('Office')
    barmex_swift = fields.Char(string='SWIFT')
    barmex_aba = fields.Char(string='ABA')