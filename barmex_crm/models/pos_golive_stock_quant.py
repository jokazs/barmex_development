from odoo import models, fields, api
import logging
_logger = logging.getLogger(__name__)

class StockQuant(models.Model):
    _inherit = "stock.quant"

    precio_producto_mxn = fields.Float('Precio del Producto MXN', compute="precio_lista_mxn")
    precio_producto_usd = fields.Float('Precio del Producto USD', compute="precio_lista_usd")
    grupo_producto = fields.Char('Grupo', related="product_id.group_id.name", store=True)
    subgrupo_producto = fields.Char('Subgrupo', related="product_id.subgroup_id.name", store=True)
    marca_producto = fields.Char('Marca', related="product_id.categ_id.name", store=True)
    codigo_sat_producto = fields.Char('Código SAT', related="product_id.l10n_mx_edi_code_sat_id.code")
    vendido_producto = fields.Boolean('Puede ser vendido', related="product_id.sale_ok")
    comprado_producto = fields.Boolean('Puede ser comprado', related="product_id.purchase_ok")
    oferta_producto = fields.Boolean('Oferta', related="product_id.offer")

    def precio_lista_mxn(self):
        try:
            vista_precio_mxn = self.env['product.pricelist.item'].search([('product_id','=',self.product_id.id),('pricelist_id', '=', 19146)], limit=1)
            vista_precio_usd = self.env['product.pricelist.item'].search([('product_id','=',self.product_id.id),('pricelist_id', '=', 19145)], limit=1)
            _logger.info("Imprime?")
            _logger.info(vista_precio_mxn.fixed_price)
            _logger.info(vista_precio_usd.fixed_price)
            self.precio_producto_mxn = vista_precio_mxn.fixed_price
            self.precio_producto_usd = vista_precio_usd.fixed_price
        except:
            self.precio_producto_mxn = 0
            self.precio_producto_usd = 0



