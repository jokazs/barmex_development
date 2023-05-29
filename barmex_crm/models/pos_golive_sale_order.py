from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit = "sale.order"

    zona_venta_cliente = fields.Many2one(string='Zona de Venta del Cliente',
                                related="partner_id.lco_sale_zone", store=True)

    agente_venta_cliente = fields.Many2one(string='Agente de Venta del Cliente',
                                related="partner_id.proveedor_employee", store=True)

    decimal_cliente = fields.Integer(string='Decimal del Cliente',
                                related="partner_id.numero_decimales", store=True)
    
    amount_untaxed_decimal = fields.Float(string='Base imponible', compute='_compute_amounts', readonly=True)
    amount_tax_decimal = fields.Monetary(string='Impuestos', compute='_compute_amounts', readonly=True)
    amount_total_decimal = fields.Float(string='Total', compute='_compute_amounts', readonly=True)
    
    @api.depends('order_line.price_subtotal', 'order_line.tax_id')
    def _compute_amounts(self):

        self.amount_untaxed_decimal = self.amount_untaxed
        self.amount_tax_decimal = self.amount_tax
        self.amount_total_decimal = self.amount_total