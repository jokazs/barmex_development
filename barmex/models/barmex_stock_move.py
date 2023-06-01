from odoo import models, fields, api, _

class StockMove(models.Model):
    _inherit = ['stock.move']

    transfer_to = fields.Many2one('stock.location',
                                  string='Transfer to')

    last_currency = fields.Many2one('res.currency',
                                    string='Last purchase currency')

    last_price = fields.Monetary(string='Last purchase price',
                                 currency_field='last_currency')

    petition = fields.Char(string="Petition",
                           related="picking_id.foreign_trade_id.petition_no")

    transferencia_creada = fields.Boolean('Transferencia interna creada')

    def _get_saleline(self):
        sale = self.env['purchase.order'].search([('name', '=', self.picking_id.origin)], limit=1).ids
        so = self.env['purchase.order'].browse(sale[0]) 
        for record in so.order_line:
            if record.product_id == self.product_id and record.product_uom_qty == self.product_uom_qty:
                return record
        
    def _get_subtotal(self):
        price = self._get_saleline().price_unit
        if not price:
            price = 0
        return self.quantity_done * price

    def _get_itemtax(self):
        total = self._get_saleline().price_total
        subtotal = self._get_saleline().price_subtotal
        qty = self._get_saleline().product_uom_qty

        taxes = (total - subtotal) / qty

        return self.quantity_done * taxes