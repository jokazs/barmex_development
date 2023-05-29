# from dataclasses import field
import string
from odoo import models,fields

class SaleOrder(models.Model):
    _name = "sale.order"
    _inherit = 'sale.order'
    _description = 'Sale order'

    def _compute_sucursal_credito(self):
        for line in self:
            print('###line.partner_id.id###')
            print(line.partner_id.id)
            print('line.partner_invoice_id.id')
            print(line.partner_invoice_id.id)
            if line.partner_id.id != line.partner_invoice_id.id:
                print('IF 17')
                facturas_pendientes = self.env['account.move'].search([('partner_id', '=', line.partner_id.id),
                                                ('sucursal_id', '=', line.partner_invoice_id.id),
                                                ('amount_residual', '>', 0)])
                print('facturas_pendientes')
                print(facturas_pendientes)
                saldo = 0
                for facturas in facturas_pendientes:
                    saldo += facturas.amount_residual
                print('self.partner_invoice_id.general_limit')
                print(self.partner_invoice_id.general_limit)


                if self.partner_invoice_id.general_limit > 0:
                    line.sucursal_credit_available = self.partner_invoice_id.general_limit - saldo
                else:
                    line.sucursal_credit_available = 1000000
                print('line.sucursal_credit_available')
                print(line.sucursal_credit_available)
            else:
                print('Else 28')
                line.sucursal_credit_available = self.partner_id.general_limit
        
    sucursal_credit_available = fields.Float('Cantidad pagada', compute='_compute_sucursal_credito')