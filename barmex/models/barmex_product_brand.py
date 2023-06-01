from odoo import models, fields, api, _
from datetime import datetime, date

class Brand(models.Model):
    _name = 'barmex.product.brand'
    _description = 'Product brand'
    _order = 'id desc'
    _check_company_auto = True

    code = fields.Integer(string='Code',
                          required=True)

    category_id = fields.Many2one('product.category',
                                  string='Category',
                                  required=True)

    name = fields.Char(string='Brand',
                       required=True,
                       compute='set_name')

    subgroup_id = fields.Many2one('barmex.product.subgroup',
                                  required=True)

    speciallity_ids = fields.One2many('barmex.product.speciallity',
                                      'brand_id')

    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.company)

    def get_category(self):
        category = self.env['product.category'].search([])
        sel = []

        for record in category:
            sel.append((record.name, record.name))

        return sel

    @api.depends('category_id')
    def set_name(self):
        for record in self:
            record.update({
                'name': record.category_id.name,
            })
