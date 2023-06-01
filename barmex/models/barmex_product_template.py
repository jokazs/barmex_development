from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class Product(models.Model):
    _inherit = ['product.template']

    sale_offer = fields.Boolean(string='Sale Offer')

    product_classification = fields.One2many('barmex.product.classification',
                                             'template_id')

    vendor_price_ids = fields.One2many('barmex.vendor.price',
                                       'template_id')

    lco_is_prospect_prod = fields.Boolean('Prospect product')

    is_discount = fields.Boolean('Product for Credit Note',
                                 default=False)

    offer = fields.Boolean('Offer',
                           default=False)

    group_id = fields.Many2one('barmex.product.group')

    subgroup_id = fields.Many2one('barmex.product.subgroup')

    brand_id = fields.Many2one('barmex.product.brand')

    speciallity_id = fields.Many2one('barmex.product.speciallity')

    subline_id = fields.Many2one('barmex.product.subline')

    to_deliver = fields.Float(string='To deliver',
                              compute='_to_deliver')

    qty_available_barmex = fields.Float(string='Available',
                                        compute='available_barmex')

    tasa_advalorem_igi = fields.Float(related='l10n_mx_edi_tariff_fraction_id.imp', string="TASA ADVALOREM (IGI)", readonly=True) 

    # free_qty_related = fields.Float(related='')

    @api.onchange('offer', 'sale_offer')
    def _set_offer(self):

        products = self.env['product.product'].search([('product_tmpl_id', '=', self._origin.id)])

        for record in products:
            record.update({
                'sale_offer': self.sale_offer,
                'offer': self.offer,
            })

    @api.onchange('group_id')
    def _set_group(self):

        for record in self.product_variant_ids:
            product = self.env['product.product'].browse(record._origin.id)
            product.group_id = self.group_id

    @api.onchange('subgroup_id')
    def _set_subgroup(self):

        for record in self.product_variant_ids:
            product = self.env['product.product'].browse(record._origin.id)
            product.subgroup_id = self.subgroup_id

    # @api.onchange('brand_id')
    # def _set_brand(self):

    #     for record in self.product_variant_ids:
    #         product = self.env['product.product'].browse(record._origin.id)
    #         product.brand_id = self.brand_id
    #         self.categ_id = self.brand_id.category_id.id

    @api.onchange('categ_id')
    def _set_brand(self):

        for record in self.product_variant_ids:
            product = self.env['product.product'].browse(record._origin.id)
            product.categ_id = self.categ_id
            products_brand = self.env['barmex.product.brand'].search([('category_id', '=', product.categ_id.id)])
            self.brand_id = products_brand.id

    @api.onchange('speciallity_id')
    def _set_speciallity(self):

        for record in self.product_variant_ids:
            product = self.env['product.product'].browse(record._origin.id)
            product.speciallity_id = self.speciallity_id

    @api.onchange('subline_id')
    def _set_subline(self):

        for record in self.product_variant_ids:
            product = self.env['product.product'].browse(record._origin.id)
            product.subline_id = self.subline_id

    @api.constrains('is_discount')
    def unique_discount(self):
        count = 0

        discounts = self.env['product.template'].search([('is_discount', '=', True)])

        for record in discounts:
            count += 1

        if count > 1:
            raise ValidationError(_('Only one product can be set as discount'))

    def _to_deliver(self):

        for record in self:
            sum = 0.0

            for variant in record.product_variant_ids:
                sum += variant.to_deliver

            record.update({
                'to_deliver': sum
            })

    def available_barmex(self):
        for record in self:
            sum = 0.0

            for variant in record.product_variant_ids:
                sum += variant.qty_available_barmex

            record.update({
                'qty_available_barmex': sum
            })