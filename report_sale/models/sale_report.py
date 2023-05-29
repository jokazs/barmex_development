# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ReportSale(models.Model):
    _inherit = 'sale.report'
    _description = 'Reporte de Venta'

    @api.model
    def _total_coste(self):
        for to in self:
            to.total_coste = to.product_uom_qty * to.standard_price

    @api.model
    def _total_venta(self):
        for to in self:
            to.total_venta = to.product_uom_qty * to.price

    @api.model
    def _calcular_utilidad(self):
        for to in self:
            line = self.env['sale.order.line'].search(
                [('order_id', '=', int(to.order_id.id)), ('product_id', '=', int(to.product_id.id))])
            if line:
                to.utilidad = line.price_unit - line.purchase_price

    @api.model
    def _calcular_margen(self):
        for to in self:
            line = self.env['sale.order.line'].search([('order_id', '=', int(to.order_id.id)),('product_id', '=', int(to.product_id.id))])
            if line.price_unit == 0:
                to.margen = 0
            else:
                result = to.utilidad / line.price_unit * 100
                to.margen = str(round(result, 2)) + '%'

    @api.model
    def _cumpute_albaran(self):
        origenes = self.env['stock.picking'].search([])
        for al in self:
            for ori in origenes:
                if ori.origin == al.order_id.name:
                    al.albaran = ori.name

    @api.model
    def _cumpute_fatura(self):
        for fact in self:
            factu = self.env['account.move'].search([('invoice_origin', '=', fact.order_id.name), '|',('state', '!=', 'cancel'),('type', '=', 'out_invoice')])
            if len(factu) > 1:
                fact.move_name = factu[0].name
            elif len(factu) == 0:
                fact.move_name = ''
            else:
                fact.move_name = factu.name

    @api.model
    def _cumpute_payment(self):
        for fact in self:
            factu = self.env['account.move'].search([('invoice_origin', '=', fact.order_id.name)])
            pymen = self.env['account.payment'].search([('ref', '=', factu.name)])
            if pymen:
                fact.payment_reference = pymen.name


    def _compute_coste(self):
        for to in self:
            line = self.env['sale.order.line'].search(
                [('order_id', '=', int(to.order_id.id)), ('product_id', '=', int(to.product_id.id))])
            if line:
                to.price = line.price_unit
                to.standart_price = line.purchase_price

    standart_price = fields.Float(string='Costo', compute=_compute_coste)
    price = fields.Float(string='Precio',compute=_compute_coste)
    total_coste = fields.Float(string='Total Costo', compute=_total_coste)
    total_venta = fields.Float(string='Total Venta', compute=_total_venta)
    utilidad = fields.Float('Utilidad', compute=_calcular_utilidad)
    margen = fields.Char('Margen de Utilidad', compute=_calcular_margen)
    albaran = fields.Char(string='Albarán', compute=_cumpute_albaran)
    move_name = fields.Char(string='Factura', compute=_cumpute_fatura)
    payment_reference = fields.Char(string='Pago', compute=_cumpute_payment)

    def action_list_precio(self):
        action = self.env['ir.actions.act_window']._for_xml_id('report_sale.product_pricelist_item_action')
        ctx = dict(self.env.context)
        ctx.pop('active_id', None)
        ctx['active_model'] = 'product.pricelist.item'
        ctx['domain'] = [('pricelist_id', '=', self.order_id.pricelist_id.id)]
        action['context'] = ctx,
        action.update(
            context=dict(default_pricelist_id=self.id),
            domain=[('pricelist_id', '=', self.order_id.pricelist_id.id)]
        )
        print('CTX', ctx)
        # print('ACTION', action)
        return action