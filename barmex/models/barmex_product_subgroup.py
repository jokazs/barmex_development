from odoo import models, fields, api, _
from datetime import datetime, date

class Subgroup(models.Model):
    _name = 'barmex.product.subgroup'
    _description = 'Product sub group'
    _order = 'id desc'
    _check_company_auto = True

    code = fields.Integer(string='Code',
                          required=True)

    name = fields.Char(string='Sub Group',
                       required=True)

    group_id = fields.Many2one('barmex.product.group',
                               required=True)

    brand_ids = fields.One2many('barmex.product.brand',
                                'subgroup_id')

    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.company)