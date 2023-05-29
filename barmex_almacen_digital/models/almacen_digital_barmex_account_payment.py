import base64
from uuid import uuid1

from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _
from odoo.tools import date_utils
from odoo.tools.float_utils import float_compare
from odoo.exceptions import UserError, ValidationError, Warning

from datetime import datetime

class ad_AccountPayment(models.Model):
    _inherit = ['account.payment']

    status_pago = fields.Selection([('no_asignado', 'No Asignado'),('parcialmente', 'Asignado Parcialmente'),('pagado', 'Pagado')],string='Status')

    folios_ap_ids = fields.Many2many('almacen.digital','account_payment_id_almacen_digital_id','account_payment_id','almacen_digital_id',string='pagos')

    folio_ids = fields.Char('Folio que no se ocupa')
    journal_currency = fields.Char('Moneda pago', related='journal_id.currency_id.name', default='MXN')

    @api.onchange('folios_ap_ids')
    def agrega_folio(self):
        total = 0
        for factura in self.folios_ap_ids:
            total += factura.total
        if total > self.amount:
            #raise Warning('Monto de las facturas aplicadas superior al pago')
            print('Monto de las facturas aplicadas superior al pago')
    
    def cancel(self):
        for line in self.folios_ap_ids:
            line.cantidad_pagada = 0
            line.status_folio = 'no_asignado'
            line.pagos_ad_ids = False
        self.write({'state': 'cancelled'})