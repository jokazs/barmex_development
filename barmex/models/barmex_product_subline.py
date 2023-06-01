from odoo import models, fields, api, _
from datetime import datetime, date

class Subline(models.Model):
    _name = 'barmex.product.subline'
    _description = 'Product sub line'
    _order = 'id desc'
    _check_company_auto = True

    code = fields.Integer(string='Code',
                          required=True)

    name = fields.Char(string='Sub Line',
                       required=True)

    speciallity_id = fields.Many2one('barmex.product.speciallity')

    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.company)