from datetime import datetime
from email.policy import default
import requests
from odoo import models, fields, api, _
from odoo.exceptions import Warning
from odoo.tools.misc import get_lang


class AccountMove(models.Model):
    _inherit = ['account.move']

    zona_venta_cliente = fields.Many2one(string='Zona de Venta del Cliente',
                                related="partner_id.lco_sale_zone", store=True)

    agente_venta_cliente = fields.Many2one(string='Agente de Venta del Cliente',
                                related="partner_id.proveedor_employee", store=True)
    
    tipo_de_cliente = fields.Many2one(string='Tipo de Cliente',
                                related="partner_id.lco_customer_type", store=True)

    tipo_mercado_cliente = fields.Selection(string='Tipo de Mercado del Cliente',
                                related="partner_id.x_studio_tipo_de_mercado_1", store=True)
    
    corporativo_de_cliente = fields.Many2one(string='Corporativo del cliente',
                                related="partner_id.corporate_res_partner", store=True)

    decimal_cliente = fields.Integer(string='Decimal del Cliente',
                                related="partner_id.numero_decimales", store=True)

    amount_untaxed_decimal_f = fields.Float(string='Base imponible', compute='_compute_amounts', readonly=True)
    amount_total_decimal_f = fields.Float(string='Total', compute='_compute_amounts', readonly=True)
    
    @api.depends('amount_untaxed')
    def _compute_amounts(self):

        self.amount_untaxed_decimal_f = self.amount_untaxed
        self.amount_total_decimal_f = self.amount_total
    
    @api.depends('invoice_date','currency_id')
    @api.onchange('invoice_date','currency_id')
    def _update_tc(self):
        mxn = self.env.ref('base.MXN')
        ctx = dict(company_id=self.company_id.id, date=self.invoice_date)
        if self.currency_id:
            if self.invoice_date:
                self.barmex_currency_rate = ('%.6f' % (self.currency_id.with_context(**ctx)._convert(1, mxn, self.company_id, self.invoice_date, round=False))) if self.currency_id.name != 'MXN' else 1
            else:
                if self.partner_id:
                    raise Warning(_("Necesitas llenar el campo de fecha factura para seleccionar la moneda"))
        # else
            # self.barmex_currency_rate = ('%.6f' % 1)
            # self.barmex_currency_rate = ('%.6f' % (1/self.rate_exchange)) if self.currency_id.name != 'MXN' else False   