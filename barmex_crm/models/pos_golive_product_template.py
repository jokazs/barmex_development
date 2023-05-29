from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)


class Product(models.Model):
    _inherit = ['product.template']


    product_variant_ids = fields.One2many('product.product', 'product_tmpl_id', 'Products', required=True)
    producto_marca = fields.Char('Marca', related="categ_id.name", readonly=True)
    fecha_ultima_compra = fields.Date('Fecha Ultima Compra', compute='_fecha_ultima_compra')
    ultima_compra = fields.Date('Fecha Ultima Compra')



    standard_price = fields.Float(
        'Cost', compute='_compute_standard_price',
        inverse='_set_standard_price', search='_search_standard_price',
        digits='Product Price', store=True,  groups="base.group_user",
        help="""In Standard Price & AVCO: value of the product (automatically computed in AVCO).
        In FIFO: value of the last unit that left the stock (automatically computed).
        Used to value the product when the purchase cost is not known (e.g. inventory adjustment).
        Used to compute margins on sale orders.""")

    @api.depends_context('force_company')
    @api.depends('product_variant_ids', 'product_variant_ids.standard_price')
    def _compute_standard_price(self):
        # Depends on force_company context because standard_price is company_dependent
        # on the product_product
        unique_variants = self.filtered(lambda template: len(template.product_variant_ids) == 1)
        for template in unique_variants:
            template.standard_price = template.product_variant_ids.standard_price
        for template in (self - unique_variants):
            template.standard_price = 0.0

    def _set_standard_price(self):
        for template in self:
            if len(template.product_variant_ids) == 1:
                template.product_variant_ids.standard_price = template.standard_price

    def _search_standard_price(self, operator, value):
        products = self.env['product.product'].search([('standard_price', operator, value)], limit=None)
        return [('id', 'in', products.mapped('product_tmpl_id').ids)]

    def _fecha_ultima_compra(self):
        try:
            id_product_tmpl = self.env['product.product'].search([('product_tmpl_id','=',self.id)], limit=1).id
            ultima_c = self.env['stock.move.line'].search([('product_id', '=', id_product_tmpl),('location_id', '=', 4),('state', '=', 'done')],order='date desc', limit=1)
            self.fecha_ultima_compra = ultima_c.date
            if self.fecha_ultima_compra:
                self.ultima_compra = self.fecha_ultima_compra
        except:
            # self.fecha_ultima_compra = None
            _logger.info("Except del producto")