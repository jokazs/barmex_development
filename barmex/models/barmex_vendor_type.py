from odoo import models, fields, api, _

class VendorType(models.Model):
    _name = 'barmex.vendor.type'
    _description = 'Vendor type'
    _order = 'id desc'
    _check_company_auto = True

    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.company)

    name = fields.Char(string='Name')

    description = fields.Char(string='Description')
