from odoo import models, fields, api, _
from datetime import datetime, date

class Speciallity(models.Model):
    _name = 'barmex.product.speciallity'
    _description = 'Product speciallity'
    _order = 'id desc'
    _check_company_auto = True

    code = fields.Integer(string='Code',
                          required=True)

    name = fields.Char(string='Speciallity',
                       required=True)

    brand_id = fields.Many2one('barmex.product.brand')

    subline_ids = fields.One2many('barmex.product.subline',
                                  'speciallity_id')

    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.company)