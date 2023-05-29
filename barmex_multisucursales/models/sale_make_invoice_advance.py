# from dataclasses import field
import string
from odoo import models,fields



class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"
    #Agrega el campo sucursal en la factura final
    def _prepare_invoice_values(self, order, name, amount, so_line):
        res = super()._prepare_invoice_values(order, name, amount, so_line)
        if order.partner_id.id != order.partner_invoice_id.id:
            if order.partner_invoice_id:
                res['sucursal_id'] = order.partner_invoice_id.id
            res['partner_id'] = order.partner_id.id

        return res