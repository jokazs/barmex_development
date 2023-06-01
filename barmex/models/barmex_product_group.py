from odoo import models, fields, api, _
from datetime import datetime, date

class Group(models.Model):
    _name = 'barmex.product.group'
    _description = 'Product group'
    _order = 'id desc'
    _check_company_auto = True

    code = fields.Integer(string='Code',
                          required=True)

    name = fields.Char(string='Group',
                       required=True)

    subgroup_ids = fields.One2many('barmex.product.subgroup',
                                   'group_id')

    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.company)