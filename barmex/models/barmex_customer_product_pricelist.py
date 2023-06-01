from odoo import models, fields, api, _

class CustomerPriceList(models.Model):
    _name = 'barmex.customer.product.pricelist'
    _description = 'Price List Customer table'
    _check_company_auto = True
    _sql_constraints = [('unique_customer_pricelist', 'unique(partner_id,pricelist_id)',
                         _('The Customer on Price List is not unique!'))]

    partner_id = fields.Many2one('res.partner',
                                 string='Customer')

    customer_product_pricelist_ids = fields.One2many('res.partner',
                                   'id',
                                   string='Pricelist Customer',
                                   copy=False)

    pricelist_id = fields.Many2one('product.pricelist',
                                   string='Pricelist',
                                   readonly=True,
                                   index=True)

    pricelist_usd_id = fields.Many2one('product.pricelist',
                                   string='Pricelist USD',
                                   readonly=True,
                                   index=True)

    pricelist_extra_id = fields.Many2one('product.pricelist',
                                   string='Pricelist extra',
                                   readonly=True,
                                   index=True)

    reference = fields.Char(string='Note/Reference')

    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.company)