# -*- coding: utf-8 -*-

from odoo import models, fields, api

class duplicar_semana(models.TransientModel):
    _name = 'barmex.move.products'
    _description = 'barmex.move.products'

    def action_barmex_move_products_apply(self):
        for record in self.order_line_ids:
            record.order_id = self.name.id
    
    @api.onchange('name')
    def calculate_purchase_id(self):
        leads = self.env['purchase.order'].browse(self.env.context.get('active_ids'))
        self.purchase_id = leads

    @api.onchange('purchase_id')
    def order_line_ids_onchange(self):
        return {'domain': {'order_line_ids': [('order_id', '=', self.purchase_id.id)]}}

    name = fields.Many2one('purchase.order', 'Pedido de compra')
    purchase_id = fields.Many2one('purchase.order', 'Origen')
    order_line_ids = fields.Many2many('purchase.order.line', string='Productos')