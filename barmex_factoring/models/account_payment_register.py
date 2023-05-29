from addons.account.models.account_payment import MAP_INVOICE_TYPE_PARTNER_TYPE
from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
from uuid import uuid1
from odoo.addons.account.models.account_payment import MAP_INVOICE_TYPE_PARTNER_TYPE
import logging
import math

_logger = logging.getLogger(__name__)


class AccountPaymentRegister(models.TransientModel):
    _inherit = ['account.payment.register']

    def _unique_id(self):
        return uuid1()

    factoraje = fields.Boolean('Factoring')
    partial_payment = fields.Boolean('Partial Payment')
    payment_partner_id = fields.Many2one('res.partner',
                                         string='Invoice partner', domain="[('factoraje', '=', True)]")
    enabled_factoraje_field = fields.Boolean('Enabled Factoring Field?',
                                             compute='_compute_enabled_factoraje_field', default=True)
    invoice_ids = fields.Many2many('account.move', 'account_invoice_payment_rel_transient', 'payment_id', 'invoice_id',
                                   string="Invoices", copy=False, readonly=False)
    payment_id_lco = fields.Char(string='Payment ID', readonly=True, default=_unique_id, store=True)
    payment_date_lco = fields.Date(string='Real Payment Date',
                                   default=fields.Date.context_today,
                                   required=True,
                                   readonly=True,
                                   states={'draft': [('readonly', False)]},
                                   copy=False)
    journal_currency = fields.Char('Moneda pago', related='journal_id.currency_id.name', default='MXN')
    folios_ap_ids = fields.Many2many('almacen.digital','account_payment_reegister_id_almacen_digital_id','account_payment_register_id','almacen_digital_id',string='Almacen Digital')
    currency_rate = fields.Float(string='Currency rate', digits=(12, 6), default=0.000000)
    exchange_rate = fields.Boolean('Exchange rate')

    @api.onchange('currency_rate')
    def onchange_currency_rate(self):
        if self.currency_rate > 0:
            for inv in self.invoice_ids:
                inv.currency_rate = self.currency_rate
                inv.amount_currency_rate = inv.to_pay * self.currency_rate
                inv.profit_loss = inv.balance_pay_mxn - inv.amount_currency_rate

    @api.model
    def default_get(self, fields):
        vals = super(AccountPaymentRegister, self).default_get(fields)
        invoices = self.env['account.move'].browse(vals['invoice_ids'][0][2])
        customers = []
        for invoice in invoices:
            if invoice.partner_id.parent_id:
                if invoice.partner_id.parent_id.id not in customers:
                    customers.append(invoice.partner_id.parent_id.id)
            elif invoice.partner_id:
                if invoice.partner_id.id not in customers:
                    customers.append(invoice.partner_id.id)
        account_factoraje = self.env['account.account'].search([('factoraje', '=', True)])
        if len(customers) > 1 or not (invoices[0].partner_id.factoraje or invoices[
            0].partner_id.parent_id.factoraje) or not account_factoraje:
            vals['enabled_factoraje_field'] = False
        return vals

    def _compute_enabled_factoraje_field(self):
        for rec in self:
            enabled_factoraje_field = True
            customers = []
            for invoice in self.invoice_ids:
                if invoice.partner_id.parent_id:
                    if invoice.partner_id.parent_id.id not in customers:
                        customers.append(invoice.partner_id.parent_id.id)
                elif invoice.partner_id:
                    if invoice.partner_id.id not in customers:
                        customers.append(invoice.partner_id.id)
            account_factoraje = self.env['account.account'].search([('factoraje', '=', True)])
            if len(customers) > 1 or not (self.invoice_ids[0].partner_id.factoraje or self.invoice_ids[
                0].partner_id.parent_id.factoraje) or not account_factoraje:
                enabled_factoraje_field = False
            rec.enabled_factoraje_field = enabled_factoraje_field

    @api.onchange('factoraje')
    def onchange_factoring(self):
        active_ids = self._context.get('active_ids')
        invoices = self.env['account.move'].browse(active_ids)
        if invoices and self.factoraje:
            self.payment_partner_id = invoices[0].partner_id.payment_partner_id.id if self.invoice_ids[
                0].partner_id.payment_partner_id else self.invoice_ids[0].partner_id.parent_id.payment_partner_id.id

    def _prepare_payment_vals(self, invoices):
        values = super(AccountPaymentRegister, self.with_context(exchange_rate=self.exchange_rate,
                                                                 currency_rate=self.currency_rate,
                                                                 factoraje=self.factoraje,
                                                                 payment_partner_id=self.payment_partner_id,
                                                                 group_payment=self.group_payment,
                                                                 partial_payment=self.partial_payment))._prepare_payment_vals(
            invoices)
        monto = 0.0
        if self.partial_payment and self.group_payment:
            for inv in invoices:
                if self.group_payment:
                    monto += inv.to_pay
                else:
                    monto = inv.to_pay

            values.update({
                'currency_rate': self.currency_rate,
                'factoraje': self.factoraje,
                'partial_payment': self.partial_payment,
                'group_payment': self.group_payment,
                'exchange_rate': self.exchange_rate,
                'payment_partner_id': self.payment_partner_id.id,
                'payment_id_lco': self.payment_id_lco,
                'payment_date_lco': self.payment_date_lco,
                'amount': monto if self.partial_payment else values['amount']
            })
        elif self.exchange_rate and self.group_payment:
            for inv in invoices:
                if self.group_payment:
                    monto += inv.amount_currency_rate
                else:
                    monto = inv.amount_currency_rate

            values.update({
                'currency_rate': self.currency_rate,
                'factoraje': self.factoraje,
                'partial_payment': self.partial_payment,
                'group_payment': self.group_payment,
                'exchange_rate': self.exchange_rate,
                'payment_partner_id': self.payment_partner_id.id,
                'payment_id_lco': self.payment_id_lco,
                'payment_date_lco': self.payment_date_lco,
                'amount': monto if self.exchange_rate else values['amount']
        })
        _logger.info('## Paso 2 - account_payment_register - _prepare_payment_vals###')
        _logger.info(values)
        fields_dict = {}
        for key in self.fields_get():
            fields_dict[key] = self[key]
        _logger.info('## Paso 2 - account_payment_register - AccountPaymentRegister valores###')
        _logger.info(fields_dict)
        return values
        # 13,592.43
        # 19.4667

    def create_payments(self):
        _logger.info("###Paso 1 - account_payment_register - Boton create_payments ####")
        if self.factoraje:
            for inv in self.invoice_ids:
                if inv.to_pay > 0:
                    raise ValidationError(_('Por favor revise, porque no se puede poner valor en el campo a pagar en las facturas'))
        elif self.exchange_rate:
            for inv in self.invoice_ids:
                if inv.payment_factoring > 0:
                    raise ValidationError(_('Por favor revise, porque no se puede poner valor en el campo pago por factoraje en las facturas'))
        elif self.partial_payment:
            for inv in self.invoice_ids:
                if inv.payment_factoring > 0:
                    raise ValidationError(_('Por favor revise, porque no se puede poner valor en el campo pago por factoraje en las facturas'))
        res = super(AccountPaymentRegister, self.with_context(exchange_rate=self.exchange_rate,
                                                                 currency_rate=self.currency_rate,
                                                                 factoraje=self.factoraje,
                                                                 payment_partner_id=self.payment_partner_id,
                                                                 group_payment=self.group_payment,
                                                                 partial_payment=self.partial_payment)).create_payments()
        _logger.info("###Paso 1 Boton create_payments - Output RES####")
        _logger.info(res)
        # Crea el pago con los valores originales y luego hace el cambio del monto a MXN
        # if 'res_id' in res:
        #     _logger.info(res['res_id'])
        #     _logger.info(res['domain'][0][2])
        #     pago = self.env['account.payment'].browse(res['res_id'])
        #     pago_mxn = 0
        #     for factura in self.invoice_ids:
        #         #Importe en MXN
        #         pago_mxn += factura.amount_currency_rate
        #     _logger.info(f"Monto original: {pago.amount} monto nuevo: {(math.ceil(pago_mxn * 100) / 100)}")
        #     pago.amount = math.ceil(pago_mxn * 100) / 100
        #     _logger.info(f"Moneda original: {pago.currency_id.id} journal_id nuevo: {self.journal_id.currency_id.id} compañia nuevo: {self.journal_id.company_id.currency_id}")

        # pago.currency_id = self.journal_id.currency_id or self.journal_id.company_id.currency_id
        # pago.check_rate = True
        # pago.rate_exchange = self.exchange_rate
        return res

    def _get_payment_group_key(self, invoice):
        """ Returns the grouping key to use for the given invoice when group_payment
        option has been ticked in the wizard.
        """
        if self.factoraje and self.group_payment:
            return (invoice.partner_id.parent_id, invoice.currency_id, invoice.invoice_partner_bank_id,
                    MAP_INVOICE_TYPE_PARTNER_TYPE[invoice.type])
        else:
            super(AccountPaymentRegister, self)._get_payment_group_key(invoice)
