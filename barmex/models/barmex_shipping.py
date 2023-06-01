from odoo import models, fields, api, _

class Shipping(models.Model):
    _name = 'barmex.shipping'
    _description = 'Shipping'
    _order = 'id desc'
    _check_company_auto = True

    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.company)

    name = fields.Char(string='Code',
                       required=True)

    description = fields.Char(string='Description',
                              required=True)