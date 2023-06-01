from odoo import models, fields, api, _

class ProductReference(models.Model):
    _name = 'barmex.customer.codes'
    _description = 'Product codes table'
    _check_company_auto = True

    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.company)

    product_id = fields.Many2one('product.product',
                                 required=True)

    partner_id = fields.Many2one('res.partner')

    reference = fields.Char('Internal reference')

    name = fields.Char('Name')

    uom = fields.Many2one('uom.uom')

    invoice = fields.Boolean('Electronic invoice',
                             default=False)