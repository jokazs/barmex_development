from odoo import models, fields, api, _

class CustomerPriceList(models.Model):
    _name = 'barmex.partner.type'
    _description = 'Customer Type table'
    _rec_name = 'type_cust_id'
    _check_company_auto = True
    _sql_constraints = [('unique_customer_pricelist', 'unique(type_cust_id)',
                         _('Customer type already exists!'))]

    type_cust_id = fields.Char(string='Customer type')

    short_description = fields.Char(string='Description')

    long_description = fields.Char(string='Notes')

    _check_company_auto = True

    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.company)