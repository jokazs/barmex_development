from lxml import etree

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime
from odoo.addons.l10n_mx_edi.models import account_invoice
from odoo.tools import DEFAULT_SERVER_TIME_FORMAT
import math
import logging
import base64

_logger = logging.getLogger(__name__)

CFDI_TEMPLATE = 'barmex_factoring.payment10'
CFDI_TEMPLATE_ = 'l10n_mx_edi.payment10'
CFDI_XSLT_CADENA = 'l10n_mx_edi/data/3.3/cadenaoriginal.xslt'


CFDI_TEMPLATE40 = 'barmex_factoring.payment20'
CFDI_XSLT_CADENA40 = 'barmex_factoring/data/4.0/cadenaoriginal.xslt'
CFDI_XSLT_CADENA_TFD40 = 'barmex_factoring/data/xslt/4.0/cadenaoriginal_TFD_1_1.xslt'

class AccountPayment(models.Model):
    _inherit = ['account.payment']

    payment_partner_id = fields.Many2one('res.partner',
                                         string='Invoice partner')

    factoraje = fields.Boolean('Factoring')
    group_payment = fields.Boolean(help="Only one payment will be created by partner (bank)/ currency.")
    exchange_rate = fields.Boolean('Exchange rate')
    partial_payment = fields.Boolean('Partial Payment')
    invoice_ids = fields.Many2many('account.move', 'account_invoice_payment_rel', 'payment_id', 'invoice_id',
                                   string="Invoices", copy=False, readonly=False)
    payment_factoring = fields.Float(string='Payment Factoring', currency_field='company_currency_id', copy=False)
    currency_rate = fields.Float(string='Currency rate', digits=(12, 6), default=0.000000)

    no_timbrar = fields.Boolean('No timbrar')
    tc_complemento = fields.Float(string='Currency rate', digits=(12, 10), default=0.000000)

    redondeo = fields.Selection([
        ('3', 'No redondear (truncar)'),
        ('5', 'Redondear')
    ], string='Metodo redondeo complemento', default='5')
    digitos_descuadre_monto = fields.Float(string='Digitos descuadre monto', digits=(12, 10), default=0.000000)

    @api.onchange('currency_rate')
    def _onchange_currency_rate(self):
        if self.currency_rate > 0:
            for inv in self.invoice_ids:
                inv.currency_rate = self.currency_rate
                inv.amount_currency_rate = inv.to_pay * self.currency_rate
                inv.profit_loss = inv.balance_pay_mxn - inv.amount_currency_rate

    @api.onchange('factoraje')
    def onchange_factoring(self):
        active_ids = self._context.get('active_ids')
        invoices = self.env['account.move'].browse(active_ids)
        if invoices and self.factoraje:
            self.payment_partner_id = invoices[0].partner_id.payment_partner_id.id if self.invoice_ids[
                0].partner_id.payment_partner_id else self.invoice_ids[0].partner_id.parent_id.payment_partner_id.id

    @api.onchange('payment_factoring')
    def onchange_payment_factoring(self):
        active_ids = self._context.get('active_ids')
        invoices = self.env['account.move'].browse(active_ids)
        for inv in invoices:
            if self.payment_factoring > 0:
                inv.payment_factoring = self.payment_factoring

    def _prepare_payment_moves(self):
        vals = super(AccountPayment, self)._prepare_payment_moves()
        if self._context.get('factoraje') or self.factoraje:
            line = vals[0]['line_ids'][1][2]
            factoraje = 0
            if self._context.get('group_payment'):
                for inv in self.invoice_ids:
                    if inv.amount_residual < inv.payment_factoring:
                        raise ValidationError(_('The factoring amount cannot be greater than the invoice amount'))
                    else:
                        factoraje += inv.payment_factoring
            else:
                if self.invoice_ids.payment_factoring > 0:
                    for inv in self.invoice_ids:
                        if inv.amount_residual < inv.payment_factoring:
                            raise ValidationError(_('The factoring amount cannot be greater than the invoice amount'))
                        else:
                            factoraje = inv.payment_factoring
                else:
                    factoraje = self.payment_factoring
                    self.invoice_ids.payment_factoring = self.payment_factoring

            line['debit'] = line['debit'] - factoraje
            vals[0]['line_ids'][1] = (0, 0, line)

            account_factoraje = self.env['account.account'].search([('factoraje', '=', True)])
            line1 = {'name': line['name'],
                     'amount_currency': math.ceil(line['amount_currency'] * 100) / 100,
                     'currency_id': line['currency_id'],
                     'debit': round(factoraje,2),
                     'credit': round(line['credit'],2),
                     'date_maturity': line['date_maturity'],
                     'partner_id': self._context.get('payment_partner_id').id if self._context.get('payment_partner_id') else self.payment_partner_id.id ,
                     'account_id': account_factoraje.id,
                     'payment_id': line['payment_id']}
            vals[0]['line_ids'].append((0, 0, line1))
        elif self._context.get('exchange_rate') or self.exchange_rate:#
            line = vals[0]['line_ids'][1][2]
            line1 = vals[0]['line_ids'][0][2]
            loss = 0
            loss1 = 0
            topay = 0
            check_diferencia = 0
            balance_pay_mxn = 0
            amount_currency_rate = 0
            _logger.info('## Paso 3 - account_payment - _prepare_payment_moves ###')
            _logger.info('## Paso 3 - account_payment - self._context.get(exchange_rate) ###')
            _logger.info(self._context.get('exchange_rate'))
            _logger.info(self.exchange_rate)
            _logger.info(f'currency_rate: {self.exchange_rate}')

            for inv in self.invoice_ids:
                if round(inv.amount_total, 2) < inv.to_pay:
                    raise ValidationError(_('The amount to pay cannot be greater than the invoice amount'))
                elif (self._context.get('exchange_rate') and self._context.get('group_payment')) or (self.exchange_rate and self.group_payment):
                    _logger.info('Pago agrupado entra IF 100')
                    _logger.info(f'inv.profit_loss - Monto MXN Diferencia: {inv.profit_loss}')
                    _logger.info(f'inv.balance_pay_mxn - Monto MXN al TC de pago: {inv.balance_pay_mxn}')
                    _logger.info(f'inv.amount_currency_rate - Monto MXN al TC de factura **: {inv.amount_currency_rate}')
                    _logger.info(f'inv.to_pay - Monto abonado en USD: {inv.to_pay}')
                    tipo_cambio_pago = self._context.get('currency_rate')
                    _logger.info(f'tipo_cambio_pago : {tipo_cambio_pago}')
                    tipo_cambio_pago = self.currency_rate
                    _logger.info(f'self tipo_cambio_pago : {tipo_cambio_pago}')

                    loss = loss + inv.profit_loss
                    balance_pay_mxn = balance_pay_mxn + inv.balance_pay_mxn
                    amount_currency_rate = amount_currency_rate + inv.amount_currency_rate
                    topay = topay + inv.to_pay
                else:
                    loss = inv.profit_loss
                    balance_pay_mxn = inv.balance_pay_mxn
                    amount_currency_rate = inv.amount_currency_rate
                    topay = inv.to_pay
                    tipo_cambio_pago = self.currency_rate

            #Cuenta de diferencias cambiarias
            account_loss = self.env['account.account'].search([('code', '=', '4160-001-002')])
            account_profit = self.env['account.account'].search([('code', '=', '4260-001-002')])
            line2 = {'name': line['name'],
                     'amount_currency': line['amount_currency'] if self.partner_type == 'customer' else line['amount_currency'],
                     'currency_id': line['currency_id'],
                     'debit': 0,
                     'credit': 0,
                     'date_maturity': line['date_maturity'],
                     'partner_id': self.partner_id.id,
                     'account_id': account_loss.id if loss < 1 else account_profit.id,
                     'payment_id': line['payment_id']}
            if loss > 0 and self.partner_type == 'customer':
                if round(abs(loss), 2) + round(balance_pay_mxn, 2) > round(amount_currency_rate, 2):
                    loss1 = abs(loss) - ((round(abs(loss), 2) + round(balance_pay_mxn, 2)) - round(amount_currency_rate, 2))
                line2['debit'] = round(abs(loss1), 2) if loss1 > 0 else round(abs(loss),2)
                line['debit'] = round(amount_currency_rate, 2)
                line1['credit'] = round(balance_pay_mxn, 2)
                line2['amount_currency'] = line2['debit'] / tipo_cambio_pago
                line['amount_currency'] = line['debit'] / tipo_cambio_pago
                line1['amount_currency'] = -line1['credit'] / tipo_cambio_pago
                check_diferencia = line2['debit'] + line['debit'] - line1['credit']
            elif loss < 0 and self.partner_type == 'customer':
                if round(abs(loss), 2) + round(balance_pay_mxn, 2) > round(amount_currency_rate, 2):
                    loss1 = abs(loss) - ((round(abs(loss), 2) + round(balance_pay_mxn, 2)) - round(amount_currency_rate, 2))
                line['debit'] = round(amount_currency_rate, 2)
                line1['credit'] = round(balance_pay_mxn, 2)
                if line['debit'] > line1['credit']:
                    loss1 = abs(loss) - (round(round(abs(loss), 2) + round(balance_pay_mxn, 2), 2) - round(amount_currency_rate,2))
                    line2['credit'] = round(abs(loss1), 2) if loss1 > 0 else round(abs(loss), 2)
                    line2['amount_currency'] = line['amount_currency']
                else:
                    line2['credit'] = round(abs(loss1), 2) if loss1 > 0 else round(abs(loss), 2)

                check_diferencia = line2['credit'] + line1['credit'] - line['debit']
                line2['amount_currency'] = line2['debit'] / tipo_cambio_pago
                line['amount_currency'] = line['debit'] / tipo_cambio_pago
                line1['amount_currency'] = -line1['credit'] / tipo_cambio_pago
            elif loss > 0 and self.partner_type == 'supplier':
                if round(round(abs(loss), 2) + round(amount_currency_rate, 2), 2) > round(balance_pay_mxn, 2):
                    loss1 = abs(loss) - (round(round(abs(loss), 2) + round(amount_currency_rate, 2), 2) - round(balance_pay_mxn, 2))
                line2['credit'] = round(abs(loss1), 2) if loss1 > 0 else round(abs(loss), 2)
                line['credit'] = round(amount_currency_rate, 2)
                line1['debit'] = round(balance_pay_mxn, 2)
                check_diferencia = line2['debit'] + line['debit'] - line1['credit']
            elif loss < 0 and self.partner_type == 'supplier':
                if round(round(abs(loss), 2) + round(amount_currency_rate, 2), 2) > round(balance_pay_mxn, 2):
                    loss1 = abs(loss) - (round(round(abs(loss), 2) + round(amount_currency_rate, 2), 2) - round(balance_pay_mxn, 2))
                line['credit'] = round(amount_currency_rate, 2)
                line1['debit'] = round(balance_pay_mxn, 2)
                if line['credit'] > line1['debit']:
                    loss1 = abs(loss) - (round(round(abs(loss), 2) + round(balance_pay_mxn, 2), 2) - round(amount_currency_rate,2))
                    line2['debit'] = round(abs(loss1), 2) if loss1 > 0 else round(abs(loss), 2)
                    line2['amount_currency'] = line1['amount_currency']
                else:
                    line2['credit'] = round(abs(loss1), 2) if loss1 > 0 else round(abs(loss), 2)
                check_diferencia = line2['credit'] + line1['credit'] - line['debit']
            vals[0]['line_ids'].append((0, 0, line2))
            
            _logger.info(line2['name'])
            _logger.info("line2['credit']")
            _logger.info(line2['credit'])
            _logger.info("line2['debit']")
            _logger.info(line2['debit'])
            

            _logger.info(line['name'])
            _logger.info("line['credit']")
            _logger.info(line['credit'])
            _logger.info("line['debit']")
            _logger.info(line['debit'])


            _logger.info(line1['name'])
            _logger.info("line1['debit']")
            _logger.info(line1['debit'])
            _logger.info("line1['credit']")
            _logger.info(line1['credit'])

            if (check_diferencia != 0):
                _logger.info('DIFERENCIA!!!')
                _logger.info(check_diferencia)
                if check_diferencia < 0:
                    #Credit es mas grande
                    line1['credit'] = round(line1['credit'] - abs(check_diferencia), 2)
                else:
                    line['debit'] = round(line['debit'] + abs(check_diferencia),2)

                _logger.info(line2['name'])
                _logger.info("line2['credit']")
                _logger.info(line2['credit'])
                _logger.info("line2['debit']")
                _logger.info(line2['debit'])
                

                _logger.info(line['name'])
                _logger.info("line['credit']")
                _logger.info(line['credit'])
                _logger.info("line['debit']")
                _logger.info(line['debit'])


                _logger.info(line1['name'])
                _logger.info("line1['debit']")
                _logger.info(line1['debit'])
                _logger.info("line1['credit']")
                _logger.info(line1['credit'])

                check_diferencia = line['debit'] + line2['debit'] - line1['credit']
                _logger.info('check_diferencia 2')
                _logger.info(check_diferencia)
            
            self.amount = (math.ceil(amount_currency_rate * 100) / 100)  #topay
            self.currency_id = self.journal_id.currency_id or self.journal_id.company_id.currency_id
        # elif (self._context.get('partial_payment') and self._context.get('group_payment')) or (
        #         self.partial_payment and self.group_payment):
        #     line = vals[0]['line_ids'][1][2]
        #     line1 = vals[0]['line_ids'][0][2]
        #     partial_payment = 0
        #     partial_payment_mxn = 0
        #     for inv in self.invoice_ids:
        #         if inv.amount_residual < inv.to_pay:
        #             raise ValidationError(_('The Partial payment amount cannot be greater than the invoice amount'))
        #         else:
        #             partial_payment_mxn += inv.to_pay * (abs(inv.amount_total_signed) / inv.amount_total)
        #             partial_payment += inv.to_pay
        #     line['debit'] = partial_payment_mxn
        #     line['amount_currency'] = -partial_payment if self.payment_type == 'outbound' else partial_payment
        #     line1['credit'] = partial_payment_mxn
        #     line1['amount_currency'] = partial_payment
        #     self.amount = (math.ceil(partial_payment * 100) / 100)
        return vals


    def _l10n_mx_edi_create_cfdi_values(self):
        #Redonde la cantidad pagada a 2 decimales / problemas con el SAT
        vals = super(AccountPayment, self)._l10n_mx_edi_create_cfdi_values()
        pago = vals['record']
        pago.amount = math.ceil(pago.amount * 100) / 100
        if 'total_paid' in vals:
            vals['total_paid'] = math.ceil(vals['total_paid'] * 100) / 100
        if 'total_currency' in vals:
            vals['total_currency'] = math.ceil(vals['total_currency'] * 100) / 100
        _logger.info('##Paso 4 - account_payment - _l10n_mx_edi_create_cfdi_values###')
        _logger.info(vals)
        return vals

    def _l10n_mx_edi_invoice_payment_data(self):
        vals = super(AccountPayment, self)._l10n_mx_edi_invoice_payment_data()
        _logger.info('##Paso 5 - account_payment - _l10n_mx_edi_invoice_payment_data ###')
        _logger.info(vals)
        _logger.info(f'self.amount: {self.amount}')
        vals['total_curr'] = self.amount
        return vals

    def _l10n_mx_edi_create_cfdi_payment(self):

        self.ensure_one()
        qweb = self.env['ir.qweb']
        error_log = []
        company_id = self.company_id
        pac_name = company_id.l10n_mx_edi_pac
        values = self._l10n_mx_edi_create_cfdi_values()
        if 'error' in values:
            error_log.append(values.get('error'))

        # -----------------------
        # Check the configuration
        # -----------------------
        # -Check certificate
        certificate_ids = company_id.l10n_mx_edi_certificate_ids
        certificate_id = certificate_ids.sudo().get_valid_certificate()
        if not certificate_id:
            error_log.append(_('No valid certificate found'))

        # -Check PAC
        if pac_name:
            pac_test_env = company_id.l10n_mx_edi_pac_test_env
            pac_password = company_id.l10n_mx_edi_pac_password
            if not pac_test_env and not pac_password:
                error_log.append(_('No PAC credentials specified.'))
        else:
            error_log.append(_('No PAC specified.'))

        if error_log:
            return {'error': _('Please check your configuration: ') + account_invoice.create_list_html(error_log)}

        # -Compute date and time of the invoice
        partner = self.journal_id.l10n_mx_address_issued_id or self.company_id.partner_id.commercial_partner_id
        tz = self.env['account.move']._l10n_mx_edi_get_timezone(
            partner.state_id.code)
        date_mx = datetime.now(tz)
        if not self.l10n_mx_edi_expedition_date:
            self.l10n_mx_edi_expedition_date = date_mx.date()
        if not self.l10n_mx_edi_time_payment:
            self.l10n_mx_edi_time_payment = date_mx.strftime(
                DEFAULT_SERVER_TIME_FORMAT)

        time_invoice = datetime.strptime(self.l10n_mx_edi_time_payment,
                                         DEFAULT_SERVER_TIME_FORMAT).time()

        # -----------------------
        # Create the EDI document
        # -----------------------

        # -Compute certificate data
        values['date'] = datetime.combine(
            fields.Datetime.from_string(self.l10n_mx_edi_expedition_date),
            time_invoice).strftime('%Y-%m-%dT%H:%M:%S')
        values['certificate_number'] = certificate_id.serial_number
        values['certificate'] = certificate_id.sudo().get_data()[0]


        # -Compute cfdi
        if self._context.get('factoraje') or self.factoraje or self.exchange_rate or self._context.get('partial_payment'):
            _logger.info('##values antes de generar CFDI###')
            _logger.info(values)
            _logger.info(values['record'])
            fields_dict = {}
            for key in values['record'].fields_get():
                fields_dict[key] = values['record'][key]
            _logger.info(fields_dict)
            pago = values['record']
            if self.exchange_rate:
                pago_mxn = 0

                _logger.info('VALORES ANTES DE ENVIAR DICT')
                _logger.info(values)
                for factura in pago.invoice_ids:
                    #Importe en MXN
                    pago_mxn += factura.amount_currency_rate
                    _logger.info(factura)
                    _logger.info(factura.name)
                    _logger.info(factura.payment_factoring)
                    _logger.info(factura.amount_residual)
                    _logger.info(factura.to_pay)
                    _logger.info(factura.balance)
                pago.amount = math.ceil(pago_mxn * 100) / 100
            #if self.partner_id.type_cfdi == '40':
            #    raise Warning('Factoraje no dispónible para clientes con CFDI version 4.0')
            tc = values['total_paid'] / pago.amount
            values['tc_equivalencia'] = round(tc,10)
            tc = round(tc,10)
            _logger.info('tc')
            _logger.info(tc)
            self.tc_complemento = tc
            cfdi = qweb.render(CFDI_TEMPLATE40, values=values)
        else:
            pago = values['record']
            pago_mxn = 0
            monto_moneda = 0
            monto_json = 0

            for factura in pago.invoice_ids:
                #Importe en MXN
                pago_mxn += factura.amount_currency_rate
                _logger.info(pago.amount)
                _logger.info(pago.currency_id)
                _logger.info(pago.currency_id.name)
                _logger.info(factura.currency_id.name)
                valores_factura = factura._get_reconciled_info_JSON_values()
                _logger.info(valores_factura)
                if factura.currency_id.name != pago.currency_id.name:
                    monto_moneda += factura.to_pay
                    monto_json += float(valores_factura[0]['amount'])
                    _logger.info('Suma')
                    _logger.info(valores_factura[0]['amount'])

                _logger.info(factura)
                _logger.info(factura.name)
                _logger.info(factura.payment_factoring)
                _logger.info(factura.amount_residual)
                _logger.info(factura.to_pay)
                _logger.info(factura.balance)
            tc = values['total_paid'] / pago.amount
            values['tc_equivalencia'] = tc
            _logger.info('tc')
            _logger.info(tc)
            self.tc_complemento = tc
            #Caso donde no es factoraje y el cliente es CFDI 4.0
            if self.partner_id.type_cfdi == '40':
                _logger.info('VALORES ANTES DE ENVIAR DICT')
                _logger.info(values)
                _logger.info('monto_moneda')
                _logger.info(monto_moneda)
                cfdi = qweb.render(CFDI_TEMPLATE40, values=values)
            else:
                cfdi = qweb.render('l10n_mx_edi.payment10', values=values)

        # -Compute cadena
        tree = self.l10n_mx_edi_get_xml_etree(cfdi)
        if self.partner_id.type_cfdi == '40':
            cadena = self.env['account.move'].l10n_mx_edi_generate_cadena(
            CFDI_XSLT_CADENA40, tree)
        else:
            cadena = self.env['account.move'].l10n_mx_edi_generate_cadena(
            CFDI_XSLT_CADENA40, tree)

        # Post append cadena
        tree.attrib['Sello'] = certificate_id.sudo().get_encrypted_cadena(cadena)

        # TODO - Check with XSD
        return {'cfdi': etree.tostring(tree, pretty_print=True, xml_declaration=True, encoding='UTF-8')}

    # def post(self):
    #     """ Create the journal items for the payment and update the payment's state to 'posted'.
    #         A journal entry is created containing an item in the source liquidity account (selected journal's default_debit or default_credit)
    #         and another in the destination reconcilable account (see _compute_destination_account_id).
    #         If invoice_ids is not empty, there will be one reconcilable move line per invoice to reconcile with.
    #         If the payment is a transfer, a second journal entry is created in the destination journal to receive money from the transfer account.
    #     """
    #     res = super(AccountPayment, self).post()
    #     for rec in self:
    #         if 'factoraje' not in self.env.context:
    #             rec.invoice_ids.update({'payment_factoring': self.payment_factoring})
    #     return True
    def l10n_mx_edi_is_required(self):
        if self.no_timbrar:
            return False
        else:
            return super(AccountPayment, self).l10n_mx_edi_is_required()

    def l10n_mx_edi_retry(self):
        self._l10n_mx_edi_retry()

    def _l10n_mx_edi_retry(self):
        rep_is_required = self.filtered(lambda r: r.l10n_mx_edi_is_required())
        for rec in rep_is_required:
            cfdi_values = rec._l10n_mx_edi_create_cfdi_payment()
            error = cfdi_values.pop('error', None)
            cfdi = cfdi_values.pop('cfdi', None)
            if error:
                # cfdi failed to be generated
                rec.l10n_mx_edi_pac_status = 'retry'
                rec.message_post(body=error)
                continue
            # cfdi has been successfully generated
            rec.l10n_mx_edi_pac_status = 'to_sign'
            if self.partner_id.type_cfdi == '33':
                filename = ('%s-%s-MX-Payment-10.xml' % (
                    rec.journal_id.code, rec.name))
            else:
                filename = ('%s-%s-MX-Payment-20.xml' % (
                    rec.journal_id.code, rec.name))
            ctx = self.env.context.copy()
            ctx.pop('default_type', False)
            rec.l10n_mx_edi_cfdi_name = filename
            attachment_id = self.env['ir.attachment'].with_context(ctx).create({
                'name': filename,
                'res_id': rec.id,
                'res_model': rec._name,
                'datas': base64.encodebytes(cfdi),
                'description': _('Mexican CFDI to payment'),
                })
            rec.message_post(
                body=_('CFDI document generated (may be not signed)'),
                attachment_ids=[attachment_id.id])
            rec._l10n_mx_edi_sign()
        (self - rep_is_required).write({
            'l10n_mx_edi_pac_status': 'none',
        })

    def account_move_values(self,ids):
        account = self.env["account.move"].search([('id', '=', ids)], limit=1)        
        return account

    def account_move_tax(self,ids):
        tax = self.env["account.tax"].search([('tax_group_id', '=', ids),('type_tax_use', '=', 'sale')], limit=1)        
        return tax

    def account_move_ObjetoImpDR(self,vals):
        imp = 0
        
        if int(vals['ivatra08']) > 0:
            imp += 1
        if int(vals['ivatra16']) > 0:
            imp += 1
        if int(vals['retiva'] * -1) > 0:
            imp += 1
        if int(vals['retisr'] * -1) > 0:
            imp += 1
        if imp >= 1:
            return '02'
        else:
            return '01'


    def account_move_tax_totals(self,invoice,currency):
        retiva = 0
        retisr = 0
        ivabase16 = 0
        ivatra16 = 0
        ivabase08 = 0
        ivatra08 = 0
        for inv in invoice:
            for tax in inv.amount_by_group:
                if tax[0].strip() == "IVA 16%":
                    ivabase16 += tax[2]
                    ivatra16 += tax[1]
                if tax[0].strip() == "IVA Retencion 10.67%":
                    retiva += tax[1]
                if tax[0].strip() == "ISR Retencion 10%":
                    retisr += tax[1]

                if tax[0].strip() == "IVA 8%":
                    ivabase08 += tax[2]
                    ivatra08 += tax[1]
        if self.currency_id.name == 'MXN':
            if (self.factoraje and self.group_payment) or (self._context.get('factoraje') and self._context.get(
                    'group_payment')):
                _logger.info('Entro Aqui Group Payment')
                _logger.info(self._context.get('group_payment'))
                _logger.info(self.group_payment)
                payment_factoring = 0.0
                amount_untaxed = 0.0
                for inv in self.invoice_ids:
                    payment_factoring += inv.payment_factoring
                    amount_untaxed += inv.amount_untaxed
                vals = {
                    'ivabase08': ivabase08,
                    'ivatra08': ivatra08,
                    'ivabase08_fac': ivabase08 - payment_factoring if ivatra08 > 0 else 0,
                    'ivatra08_fac': ivatra08 - payment_factoring * 0.08 if ivatra08 > 0 else 0,
                    'ivabase08_res': ivabase08 - (amount_untaxed - payment_factoring) if ivatra08 > 0 else 0,
                    'ivatra08_res': ivatra08 - (amount_untaxed - payment_factoring) * 0.08 if ivatra08 > 0 else 0,
                    'ivabase16': round(ivabase16, 2),
                    'ivatra16': round(ivatra16, 2),
                    'ivabase16_fac': round(ivabase16, 2) - payment_factoring if ivabase16 > 0 else 0,
                    'ivatra16_fac': round(ivatra16, 2) - payment_factoring * 0.16 if ivabase16 > 0 else 0,
                    'ivabase16_res': round(ivabase16, 2) - (amount_untaxed - payment_factoring) if ivabase16 > 0 else 0,
                    'ivatra16_res': round(ivatra16, 2) - (amount_untaxed - payment_factoring) * 0.16 if ivabase16 > 0 else 0,
                    'retiva': retiva,
                    'retisr': retisr,
                }
            elif (self.factoraje and not self.group_payment) or (self._context.get('factoraje') and not self._context.get('group_payment')):
                _logger.info('Entro Aqui NOT Group Payment MXN')
                for inv in invoice:
                    _logger.info(inv.id)
                _logger.info('Paso')
                _logger.info(self._context.get('group_payment'))
                _logger.info(self.group_payment)
                vals = {
                    'ivabase08': ivabase08,
                    'ivatra08': ivatra08,
                    'ivabase08_fac': ivabase08 - invoice.inpayment_factoring if ivatra08 > 0 else 0,
                    'ivatra08_fac': ivatra08 - invoice.payment_factoring * 0.08 if ivatra08 > 0 else 0,
                    'ivabase08_res': ivabase08 - (invoice.amount_untaxed - invoice.payment_factoring) if ivatra08 > 0 else 0,
                    'ivatra08_res': ivatra08 - (invoice.amount_untaxed - invoice.payment_factoring) * 0.08 if ivatra08 > 0 else 0,
                    'ivabase16': round(ivabase16, 2),
                    'ivatra16': round(ivatra16, 2),
                    'ivabase16_fac': round(ivabase16, 2) - invoice.payment_factoring if ivabase16 > 0 else 0,
                    'ivatra16_fac': round(ivatra16, 2) - invoice.payment_factoring * 0.16 if ivabase16 > 0 else 0,
                    'ivabase16_res': round(ivabase16, 2) - (invoice.amount_untaxed - invoice.payment_factoring) if ivabase16 > 0 else 0,
                    'ivatra16_res': round(ivatra16, 2) - (invoice.amount_untaxed - invoice.payment_factoring) * 0.16 if ivabase16 > 0 else 0,
                    'retiva': retiva,
                    'retisr': retisr,
                }
            elif (self.partial_payment and self.group_payment) or (self._context.get('partial_payment') and self._context.get(
                    'group_payment')):
                _logger.info('Entro Aqui Group Payment')
                _logger.info(self._context.get('group_payment'))
                _logger.info(self.group_payment)
                partial_payment = 0.0
                amount_untaxed = 0.0
                for inv in self.invoice_ids:
                    partial_payment += inv.to_pay
                vals = {
                    'ivabase08': ivabase08,
                    'ivatra08': ivatra08,
                    'ivabase08_part': partial_payment - (partial_payment * 0.08) if ivatra08 > 0 else 0,
                    'ivatra08_part': partial_payment * 0.08 if ivatra08 > 0 else 0,
                    'ivabase16': ivabase16,
                    'ivatra16': ivatra16,
                    'ivabase16_part': partial_payment - (partial_payment * 0.16) if ivabase16 > 0 else 0,
                    'ivatra16_part': partial_payment * 0.16 if ivabase16 > 0 else 0,
                    'retiva': retiva,
                    'retisr': retisr,
                }
            else:
                vals = {
                    'ivabase08':ivabase08,
                    'ivatra08':ivatra08,
                    'ivabase16':ivabase16,
                    'ivatra16':ivatra16,
                    'retiva': retiva,
                    'retisr': retisr,
                }
        else:
            tipo_cambio = self.currency_rate
            if tipo_cambio == 0:
                tipo_cambio = 1
            if (self.factoraje and self.group_payment) or (self._context.get('factoraje') and self._context.get('group_payment')) :
                _logger.info('Entro Aqui Group Payment')
                _logger.info(self._context.get('group_payment'))
                _logger.info(self.group_payment)
                payment_factoring = 0.0
                amount_untaxed = 0.0
                amount_untaxed_signed = 0.0
                amount_total_signed = 0.0
                suma_base = 0.0
                suma_tax = 0.0
                amount_total = 0.0
                for inv in self.invoice_ids:
                    payment_factoring += inv.payment_factoring
                    amount_untaxed += inv.amount_untaxed
                vals = {
                    'ivabase08': ivabase08,
                    'ivatra08': ivatra08,
                    'ivabase08_fac': ivabase08 - payment_factoring if ivatra08 > 0 else 0,
                    'ivatra08_fac': ivatra08 - payment_factoring * 0.08 if ivatra08 > 0 else 0,
                    'ivabase08_res': ivabase08 - (amount_untaxed - payment_factoring) if ivatra08 > 0 else 0,
                    'ivatra08_res': ivatra08 - (amount_untaxed - payment_factoring) * 0.08 if ivatra08 > 0 else 0,
                    'ivabase16': round(ivabase16, 2),
                    'ivatra16': round(ivatra16, 2),
                    'ivabase16_fac': round(ivabase16, 2) - payment_factoring if ivabase16 > 0 else 0,
                    'ivatra16_fac': round(ivatra16, 2) - payment_factoring * 0.16 if ivabase16 > 0 else 0,
                    'ivabase16_res': round(ivabase16, 2) - (amount_untaxed - payment_factoring) if ivabase16 > 0 else 0,
                    'ivatra16_res': round(ivatra16, 2) - (amount_untaxed - payment_factoring) * 0.16 if ivabase16 > 0 else 0,
                    'retiva': retiva,
                    'retisr': retisr,
                }
            elif (self.factoraje and not self.group_payment) or (self._context.get('factoraje') and not self._context.get('group_payment')):
                _logger.info('Entro Aqui NOT Group Payment USD')
                for inv in invoice:
                    _logger.info('Facturas', inv.id)
                _logger.info('Paso')
                _logger.info(self._context.get('group_payment'))
                _logger.info(self.group_payment)
                vals = {
                    'ivabase08': ivabase08,
                    'ivatra08': ivatra08,
                    'ivabase08_fac': ivabase08 - inv.payment_factoring if ivatra08 > 0 else 0,
                    'ivatra08_fac': ivatra08 - inv.payment_factoring * 0.08 if ivatra08 > 0 else 0,
                    'ivabase08_res': ivabase08 - (inv.amount_untaxed - inv.payment_factoring) if ivatra08 > 0 else 0,
                    'ivatra08_res': ivatra08 - (inv.amount_untaxed - inv.payment_factoring) * 0.08 if ivatra08 > 0 else 0,
                    'ivabase16': round(ivabase16, 2),
                    'ivatra16': round(ivatra16, 2),
                    'ivabase16_fac': round(ivabase16, 2) - inv.payment_factoring if ivabase16 > 0 else 0,
                    'ivatra16_fac': round(ivatra16, 2) - inv.payment_factoring * 0.16 if ivabase16 > 0 else 0,
                    'ivabase16_res': round(ivabase16, 2) - (inv.amount_untaxed - invoice.payment_factoring) if ivabase16 > 0 else 0,
                    'ivatra16_res': round(ivatra16, 2) - (inv.amount_untaxed - inv.payment_factoring) * 0.16 if ivabase16 > 0 else 0,
                    'retiva': retiva,
                    'retisr': retisr,
                }
            elif (self.partial_payment and self.group_payment) or (self._context.get('partial_payment') and self._context.get(
                    'group_payment')):
                _logger.info('Entro Aqui Group Payment')
                _logger.info(self._context.get('group_payment'))
                _logger.info(self.group_payment)
                partial_payment = 0.0
                amount_untaxed = 0.0
                for inv in self.invoice_ids:
                    partial_payment += inv.to_pay
                vals = {
                    'ivabase08': ivabase08,
                    'ivatra08': ivatra08,
                    'ivabase08_part': partial_payment - (partial_payment * 0.08) if ivatra08 > 0 else 0,
                    'ivatra08_part': partial_payment * 0.08 if ivatra08 > 0 else 0,
                    'ivabase16': ivabase16,
                    'ivatra16': ivatra16,
                    'ivabase16_part': partial_payment - (partial_payment * 0.16) if ivabase16 > 0 else 0,
                    'ivatra16_part': partial_payment * 0.16 if ivabase16 > 0 else 0,
                    'retiva': retiva,
                    'retisr': retisr,
                }
            else:
                vals = {
                    'ivabase08': round(float(ivabase08) / float(tipo_cambio),10),
                    'ivatra08':round(float(ivatra08) / float(tipo_cambio),10),
                    'ivabase16': round(float(ivabase16) / float(tipo_cambio),10),
                    'ivatra16':round(float(ivatra16) / float(tipo_cambio),10),
                    'retiva': round(float(retiva) / float(tipo_cambio),10),
                    'retisr': round(float(retisr) / float(tipo_cambio),10),
                }
        print('mira', vals)
        return vals


    @api.model
    def _get_l10n_mx_edi_cadena(self):
        self.ensure_one()
        #get the xslt path
        xslt_path = CFDI_XSLT_CADENA_TFD40
        #get the cfdi as eTree
        cfdi = base64.decodebytes(self.l10n_mx_edi_cfdi)
        cfdi = self.l10n_mx_edi_get_xml_etree(cfdi)
        cfdi = self.l10n_mx_edi_get_tfd_etree(cfdi)
        #return the cadena
        return self.env['account.move'].l10n_mx_edi_generate_cadena(xslt_path, cfdi)



    def l10n_mx_edi_get_payment_pago10_etree(self, cfdi):
        '''Get the Complement node from the cfdi.
        :param cfdi: The cfdi as etree
        :return: the Payment node
        '''
        if not hasattr(cfdi, 'Complemento'):
            return None
        attribute = '//pago20:Pago'
        namespace = {'pago20': 'http://www.sat.gob.mx/Pagos20'}
        node = cfdi.Complemento.xpath(attribute, namespaces=namespace)
        return node[0].attrib['FormaDePagoP']