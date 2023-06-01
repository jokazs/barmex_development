from odoo import models, fields, api, _

class VendorPrice(models.Model):
    _name = 'barmex.vendor.price'
    _description = 'Vendor price'
    _order = 'id desc'
    _check_company_auto = True

    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.company)

    product_id = fields.Many2one('product.product')

    template_id = fields.Many2one('product.template')

    vendor_id = fields.Many2one('res.partner')

    currency_id = fields.Many2one('res.currency')

    price = fields.Monetary(string='Price')
