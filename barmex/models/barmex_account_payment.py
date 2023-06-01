import base64
from uuid import uuid1

from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _
from odoo.tools import date_utils
from odoo.tools.float_utils import float_compare
from odoo.exceptions import UserError, ValidationError, Warning

from datetime import datetime

class AccountPayment(models.Model):
    _inherit = ['account.payment']

    def _unique_id(self):
        return uuid1()

    proposal_date = fields.Date(string='Proposal date',
                                default=fields.Date.context_today,
                                states={'draft': [('readonly', False)]},
                                copy=False)

    payment_partner_id = fields.Many2one('res.partner',
                                         string='Invoice partner')

    factoraje = fields.Boolean('Factoring')

    payment_date_lco = fields.Date(string='Real Payment Date',
                                   default=fields.Date.context_today,
                                   required=True,
                                   readonly=True,
                                   states={'draft': [('readonly', False)]},
                                   copy=False)

    payment_id_lco = fields.Char(string='Payment ID',
                                 readonly=True,
                                 default=_unique_id)

    barmex_uuid = fields.Char(string='UUID',
                              store=True,
                              readonly=True)

    barmex_description = fields.Char(string='Description')

    barmex_office_id = fields.Many2one('barmex.bank.office',
                                       string='Bank office')

    barmex_writeoff_reason = fields.Many2one('barmex.writeoff.reason',
                                             string='Write-off Reason')

    barmex_writeoff_account_id = fields.Many2one(string='Account',
                                                 related='barmex_writeoff_reason.account_id',
                                                 store=True)

    barmex_currency_id = fields.Many2one('res.currency',
                                         string='Company Currency',
                                         default=lambda self: self.env.company.currency_id,
                                         readonly=True)

    barmex_used_amount = fields.Monetary(string='Conciled Amount (Company Currency)',
                                         compute='_used_amount',
                                         currency_field='barmex_currency_id')

    barmex_used_amount_cur = fields.Monetary(string='Conciled Amount (Payment Currency)',
                                             compute='_used_amount_cur',
                                             currency_field='barmex_currency_id')

    barmex_payment_value = fields.Monetary(string='Payment Amount (Company Currency)',
                                           compute='_payment_value',
                                           currency_field='barmex_currency_id')

    barmex_unused_amount = fields.Monetary(string='Unconciled Amount (Company Currency)',
                                           compute='_unused_amount',
                                           currency_field='barmex_currency_id')

    barmex_unused_amount_orig = fields.Monetary(string='Unconciled Amount (Payment Currency)',
                                                compute='_unused_amount_value',
                                                currency_field='currency_id')

    barmex_related_invoices = fields.Char(string='Related Invoices',
                                          compute='_related_invoices_barmex')

    barmex_collector = fields.Many2one('barmex.collector',
                                       domain="[('partner_id','=',partner_id)]")

    barmex_operation_number = fields.Char(string='Operation Number')

    barmex_currency_rate = fields.Monetary(string='Tasa de cambio', default='1.0')

    @api.onchange('partner_id')
    def _update_collector(self):
        for record in self:
            record.update({
                'barmex_collector': self.env['barmex.collector'].search([('partner_id', '=', record.partner_id.id)],
                                                                        order='sequence', limit=1).id,
            })

    @api.model
    def l10n_mx_edi_get_receptor_cfdi(self, cfdi):
        self.ensure_one()
        if not hasattr(cfdi, 'Receptor'):
            return None
        xml = cfdi['Receptor'].attrib
        usoCFDI = xml['UsoCFDI']
        return usoCFDI

    def l10n_mx_edi_get_payment_pago10_etree(self, cfdi):
        '''Get the Complement node from the cfdi.

        :param cfdi: The cfdi as etree
        :return: the Payment node
        '''
        if not hasattr(cfdi, 'Complemento'):
            return None
        attribute = '//pago10:Pago'
        namespace = {'pago10': 'http://www.sat.gob.mx/Pagos'}
        node = cfdi.Complemento.xpath(attribute, namespaces=namespace)
        return node[0].attrib['FormaDePagoP']

    def _l10n_mx_edi_create_cfdi_values(self):
        """Create the values to fill the CFDI template with complement to
        payments."""
        self.ensure_one()
        cust = None
        if self.factoraje:
            cust = self.payment_partner_id
        else:
            cust = self.partner_id.commercial_partner_id
        invoice_obj = self.env['account.move']
        precision_digits = self.env['decimal.precision'].precision_get(
            self.currency_id.name)
        values = {
            'record': self,
            'supplier': self.company_id.partner_id.commercial_partner_id,
            'issued': self.journal_id.l10n_mx_address_issued_id,
            'customer': cust,
            'fiscal_regime': self.company_id.l10n_mx_edi_fiscal_regime,
            'invoice': invoice_obj,
        }

        values.update(invoice_obj._l10n_mx_get_serie_and_folio(self.name))

        values['decimal_precision'] = precision_digits
        values.update(self.l10n_mx_edi_payment_data())
        return values

    def l10n_mx_edi_payment_data(self):
        self.ensure_one()
        # Based on "En caso de no contar con la hora se debe registrar 12:00:00"
        mxn = self.env.ref('base.MXN')
        date = datetime.combine(
            fields.Datetime.from_string(self.payment_date),
            datetime.strptime('12:00:00', '%H:%M:%S').time()).strftime('%Y-%m-%dT%H:%M:%S')
        res = self._l10n_mx_edi_invoice_payment_data()
        total_paid = res.get('total_paid', 0)
        total_curr = res.get('total_curr', 0)
        total_currency = res.get('total_currency', 0)
        precision = self.env['decimal.precision'].precision_get('Account')
        if not self.move_reconciled and float_compare(
                self.amount, total_curr, precision_digits=precision) > 0:
            return {'error': _(
                '<b>The amount paid is bigger than the sum of the invoices.'
                '</b><br/><br/>'
                'Which actions can you take?\n'
                '<ul>'
                '<ol>If the customer has more invoices, go to those invoices '
                'and reconcile them with this payment.</ol>'
                '<ol>If the customer <b>has not</b> more invoices to be paid '
                'You need to create a new invoice with a product that will '
                'represent the payment in advance and reconcile such invoice '
                'with this payment.</ol>'
                '</ul>'
                '<p>If you follow this steps once you finish them and the '
                'paid amount is bellow the sum of invoices the payment '
                'will be automatically signed'
                '</p><blockquote>For more information please read '
                '<a href="http://omawww.sat.gob.mx/informacion_fiscal/factura_electronica/Documents/Complementoscfdi/Guia_comple_pagos.pdf">'
                ' this SAT reference </a>, Pag. 22</blockquote>')
            }
        ctx = dict(company_id=self.company_id.id, date=self.payment_date)
        rate = ('%.6f' % (self.currency_id.with_context(**ctx)._convert(
            1, mxn, self.company_id, self.payment_date, round=False))) if self.currency_id.name != 'MXN' else False
        partner_bank = self.l10n_mx_edi_partner_bank_id.bank_id
        company_bank = self.journal_id.bank_account_id
        payment_code = self.l10n_mx_edi_payment_method_id.code
        acc_emitter_ok = payment_code in [
            '02', '03', '04', '05', '06', '28', '29', '99']
        acc_receiver_ok = payment_code in [
            '02', '03', '04', '05', '28', '29', '99']
        bank_name_ok = payment_code in ['02', '03', '04', '28', '29', '99']
        vat = 'XEXX010101000'
        if self.factoraje and self.payment_partner_id.country_id.code == 'MX' and self.payment_partner_id.vat:
            vat = self.payment_partner_id.vat
        else:
            vat = 'XEXX010101000' if partner_bank.country and partner_bank.country != self.env.ref(
                'base.mx') else partner_bank.l10n_mx_edi_vat
        return {
            'mxn': mxn,
            'payment_date': date,
            'payment_rate': rate,
            'pay_vat_ord': False,
            'pay_account_ord': False,
            'pay_vat_receiver': False,
            'pay_account_receiver': False,
            'pay_ent_type': False,
            'pay_certificate': False,
            'pay_string': False,
            'pay_stamp': False,
            'total_paid': total_paid,
            'total_currency': total_currency,
            'pay_vat_ord': vat if acc_emitter_ok else None,
            'pay_name_ord': partner_bank.name if bank_name_ok else None,
            'pay_account_ord': (self.l10n_mx_edi_partner_bank_id.acc_number or '').replace(
                ' ', '') if acc_emitter_ok else None,
            'pay_vat_receiver': company_bank.bank_id.l10n_mx_edi_vat if acc_receiver_ok else None,
            'pay_account_receiver': (company_bank.acc_number or '').replace(
                ' ', '') if acc_receiver_ok else None,
        }

    def action_register_payment(self):
        active_ids = self.env.context.get('active_ids')
        if not active_ids:
            return ''

        return {
            'name': _('Register Payment'),
            'res_model': len(active_ids) == 1 and 'account.payment' or 'account.payment.register',
            'view_mode': 'form',
            'view_id': len(active_ids) != 1 and self.env.ref(
                'account.view_account_payment_form_multi').id or self.env.ref(
                'barmex.barmex_view_account_payment_invoice_form').id,
            'context': self.env.context,
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    def action_create_payment_proposal(self):
        active_ids = self.env.context.get('active_ids')
        if not active_ids:
            return ''

        return {
            'name': _('Payment proposal'),
            'res_model': 'account.payment',
            'view_mode': 'form',
            'view_id': self.env.ref('barmex.view_account_payment_invoice_proposal_form').id,
            'context': self.env.context,
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    def create_proposal(self):
        """ Create the journal items for the payment and update the payment's state to 'draft'.
            A journal entry is created containing an item in the source liquidity account (selected journal's default_debit or default_credit)
            and another in the destination reconcilable account (see _compute_destination_account_id).
            If invoice_ids is not empty, there will be one reconcilable move line per invoice to reconcile with.
            If the payment is a transfer, a second journal entry is created in the destination journal to receive money from the transfer account.
        """
        AccountMove = self.env['account.move'].with_context(default_type='entry')
        for rec in self:

            if rec.state != 'draft':
                raise UserError(_("Only a draft payment can be posted."))

            if any(inv.state != 'posted' for inv in rec.invoice_ids):
                raise ValidationError(_("The payment cannot be processed because the invoice is not open!"))

            # keep the name in case of a payment reset to draft
            if not rec.name:
                # Use the right sequence to set the name
                if rec.payment_type == 'transfer':
                    sequence_code = 'account.payment.transfer'
                else:
                    if rec.partner_type == 'customer':
                        if rec.payment_type == 'inbound':
                            sequence_code = 'account.payment.customer.invoice'
                        if rec.payment_type == 'outbound':
                            sequence_code = 'account.payment.customer.refund'
                    if rec.partner_type == 'supplier':
                        if rec.payment_type == 'inbound':
                            sequence_code = 'account.payment.supplier.refund'
                        if rec.payment_type == 'outbound':
                            sequence_code = 'account.payment.supplier.invoice'
                rec.name = self.env['ir.sequence'].next_by_code(sequence_code, sequence_date=rec.payment_date)
                if not rec.name and rec.payment_type != 'transfer':
                    raise UserError(_("You have to define a sequence for %s in your company.") % (sequence_code,))

            moves = AccountMove.create(rec._prepare_payment_moves())
            moves.filtered(lambda move: move.journal_id.post_at != 'bank_rec').post()

            # Update the state / move before performing any reconciliation.
            move_name = self._get_move_name_transfer_separator().join(moves.mapped('name'))
            rec.write({'state': 'draft', 'move_name': move_name})

            if rec.payment_type in ('inbound', 'outbound'):
                # ==== 'inbound' / 'outbound' ====
                if rec.invoice_ids:
                    (moves[0] + rec.invoice_ids).line_ids \
                        .filtered(
                        lambda line: not line.reconciled and line.account_id == rec.destination_account_id and not (
                                line.account_id == line.payment_id.writeoff_account_id and line.name == line.payment_id.writeoff_label)) \
                        .reconcile()
            elif rec.payment_type == 'transfer':
                # ==== 'transfer' ====
                moves.mapped('line_ids') \
                    .filtered(lambda line: line.account_id == rec.company_id.transfer_account_id) \
                    .reconcile()

            calendar = self.env['calendar.event'].create({
                'name': _('Due date for {}').format(move_name),
                'partner_ids': self.env.user.partner_id,
                'start_date': rec.proposal_date,
                'stop_date': date_utils.add(rec.proposal_date, days=1),
                'start': rec.proposal_date,
                'stop': date_utils.add(rec.proposal_date, days=1),
                'allday': True,
                'privacy': 'private'
            })

        return True

    def action_send_notification(self):        
        # mail = self.env['mail.template'].browse(template_id)
        lang = self.env.context.get('lang')

        if self.payment_type == 'outbound':
            template_id = 29
            mail = self.env['mail.template'].browse(template_id)
            tipo = 'Integración de pago Proveedor'
            reply_to = 'cuentasporpagar@barmex.com.mx'
            mail_cc = 'cuentasporpagar@barmex.com.mx'
            if self.partner_id.email_pago_proveedores:
                mail_destino = f'{self.partner_id.email_pago_proveedores}'
            else:
                mail_destino = f'{self.partner_id.email}'

        if self.payment_type == "inbound":
            template_id = 9
            mail = self.env['mail.template'].browse(template_id)
            tipo = 'Complemto de pago Cliente'
            reply_to = 'cuentasporcobrar@barmex.com.mx'
            mail_cc = 'cuentasporcobrar@barmex.com.mx'
            if self.partner_id.email.email_complementos_pago:   
                mail_destino = f'{self.partner_id.email_complementos_pago}'
            else:
                mail_destino = f'{self.partner_id.email}'

        if mail_destino != '':
            self.message_post(
                    subject=_('Email de complemento de pago enviado'),
                    message_type='comment',
                    body=f'Email de complemento de pago enviado a direccion:{mail_destino} ')
            mail.send_mail(self.id,email_values={
                'auto_delete': False,
                'subject':f'BARMEX | {tipo} {self.name}',
                'reply_to': reply_to,
                'email_to': mail_destino,
                'email_cc':mail_cc
            }, notif_layout = 'mail.mail_notification_light')

        else:
            self.message_post(
                    subject=_('Cliente sin email para notificacion'),
                    message_type='comment',
                    body=_(f'Email registrado: {self.partner_id.email_pago_proveedores}. {mail_destino}'))
        
        # ''' Opens a wizard to compose an email, with relevant mail template loaded by default '''
        # self.ensure_one()
        # template_id = int(
        #     self.env['ir.config_parameter'].sudo().get_param('account.default_vendor_notification_template'))
        # template_id = self.env['mail.template'].search([('id', '=', template_id)]).id
        # lang = self.env.context.get('lang')
        # template = self.env['mail.template'].browse(template_id)
        # ctx = {
        #     'email_to':  self.partner_id.email_complementos_pago if self.partner_id.email_complementos_pago else self.partner_id.email,
        #     'default_email_recepient': self.partner_id.email_complementos_pago if self.partner_id.email_complementos_pago else self.partner_id.email,
        #     'default_model': 'account.payment',
        #     'default_res_id': self.ids[0],
        #     'default_use_template': True,
        #     'default_template_id': template_id,
        #     'default_composition_mode': 'comment',
        #     'mark_so_as_sent': True,
        #     'force_email': True
        # }
        # return {
        #     'type': 'ir.actions.act_window',
        #     'view_mode': 'form',
        #     'res_model': 'mail.compose.message',
        #     'views': [(False, 'form')],
        #     'view_id': False,
        #     'target': 'new',
        #     'context': ctx,
        # }

    @api.onchange('barmex_writeoff_reason')
    def _writeoff_reason(self):
        for record in self:
            record.update({
                'writeoff_account_id': record.barmex_writeoff_reason.account_id.id,
                'writeoff_label': record.barmex_writeoff_reason.name,
            })

    @api.depends('invoice_ids')
    def _used_amount(self):
        for record in self:
            sum = 0
            for invoice in record.invoice_ids:
                if invoice.currency_id == record.currency_id:
                    sum += record.currency_id._convert(record._get_invoice_payment_amount(invoice),
                                                       record.barmex_currency_id,
                                                       self.env.company, record.payment_date)
                else:
                    sum += record._get_invoice_payment_amount(invoice)

            record.update({
                'barmex_used_amount': sum,
            })

    @api.depends('barmex_used_amount')
    def _used_amount_cur(self):
        for record in self:
            res = record.barmex_currency_id._convert(record.barmex_used_amount, record.currency_id, self.env.company,
                                                     record.payment_date)
            record.update({
                'barmex_used_amount_cur': res,
            })

    @api.depends('amount')
    def _payment_value(self):
        for record in self:
            res = record.currency_id._convert(record.amount, record.barmex_currency_id, self.env.company,
                                              record.payment_date)
            record.update({
                'barmex_payment_value': res,
            })

    @api.depends('barmex_used_amount')
    def _unused_amount(self):
        for record in self:
            record.update({
                'barmex_unused_amount': record.barmex_payment_value - record.barmex_used_amount,
            })

    @api.depends('barmex_used_amount')
    def _unused_amount_value(self):
        for record in self:
            used = record.barmex_currency_id._convert(record.barmex_used_amount, record.currency_id, self.env.company,
                                                      record.payment_date)
            record.update({
                'barmex_unused_amount_orig': record.amount - used,
            })

    @api.depends('invoice_ids')
    def _related_invoices_barmex(self):
        for record in self:
            invoices = ''
            for invoice in record.invoice_ids:
                invoices += ' {},'.format(invoice.name)
            record.update({
                'barmex_related_invoices': invoices[:-1]
            })

    def action_draft(self):
        lock_date = datetime.now().date()

        if self.l10n_mx_edi_expedition_date:
            lock_date = self.l10n_mx_edi_expedition_date + relativedelta(days=+ 3)

        # Reset to draft on cancelled or posted without stamp
        if self.state == 'cancelled' or self.l10n_mx_edi_pac_status != 'signed':
            super(AccountPayment, self).action_draft()

        # Cancel before 72 hours
        elif self.l10n_mx_edi_pac_status == 'signed':
        #and datetime.now().date() <= lock_date:
            super(AccountPayment, self).action_draft()
            self.state = 'cancelled'
            self.l10n_mx_edi_pac_status = False

        # Lock after 72 hours
        # elif self.l10n_mx_edi_pac_status == 'signed' and datetime.now().date() > lock_date:
        #     raise Warning(_("This payment can't be cancelled, 72 hours passed since posted"))

    def action_replace(self):
        lock_date = datetime.now().date()

        if self.l10n_mx_edi_expedition_date:
            lock_date = self.l10n_mx_edi_expedition_date + relativedelta(days=+ 3)

        if self.l10n_mx_edi_pac_status == 'signed':
        #and datetime.now().date() <= lock_date:
            super(AccountPayment, self).action_draft()
            self.state = 'cancelled'

            new = self.copy()
            new.state = 'draft'
            new.l10n_mx_edi_origin = '04|{}'.format(self.l10n_mx_edi_cfdi_uuid)
            new.l10n_mx_edi_payment_method_id = self.l10n_mx_edi_payment_method_id
            new.communication = _('Replace payment: {}'.format(self.name))

            form = self.env.ref('account.view_account_payment_form', False).id

            return {
                'name': _('Payment'),
                'type': 'ir.actions.act_window',
                'res_model': 'account.payment',
                'res_id': new.id,
                'view_id': form,
                'view_type': 'form',
                'view_mode': 'form',
                'target': 'current'
            }
        # Lock after 72 hours
        # elif self.l10n_mx_edi_pac_status == 'signed' and datetime.now().date() > lock_date:
        #     raise Warning(_("This payment can't be replaced, 72 hours passed since posted"))

    @api.depends('l10n_mx_edi_cfdi_name')
    def _compute_cfdi_values(self):
        super(AccountPayment, self)._compute_cfdi_values()
        for record in self:
            record.barmex_uuid = record.l10n_mx_edi_cfdi_uuid

    @api.model
    def default_get(self, default_fields):
        rec = super(AccountPayment, self).default_get(default_fields)

        active_ids = self._context.get('active_ids')
        active_id = self._context.get('active_id')
        if not active_ids and active_id:
            account_move = self.env['account.move'].browse(active_ids)

            paymnt = account_move.l10n_mx_edi_payment_method_id.id

            rec.update({
                'l10n_mx_edi_payment_method_id': paymnt,
            })

        return rec

    def post(self):
        for pay in self:
            if pay.env.company.collection_lock_date:
                if pay.payment_date <= self.env.company.collection_lock_date:
                    if not pay.user_has_groups('barmex.group_account_user_barmex'):
                        raise Warning(_("User can't post due Collections lock"))

        super(AccountPayment, self).post()

    @api.onchange('journal_id')
    def _onchange_journal(self):
        if self.journal_id:
            if self.journal_id.currency_id:
                self.currency_id = self.journal_id.currency_id

            # Set default payment method (we consider the first to be the default one)
            payment_methods = self.payment_type == 'inbound' and self.journal_id.inbound_payment_method_ids or self.journal_id.outbound_payment_method_ids
            payment_methods_list = payment_methods.ids

            default_payment_method_id = self.env.context.get('default_payment_method_id')
            if default_payment_method_id:
                # Ensure the domain will accept the provided default value
                payment_methods_list.append(default_payment_method_id)
            else:
                self.payment_method_id = payment_methods and payment_methods[0] or False

            # Set payment method domain (restrict to methods enabled for the journal and to selected payment type)
            payment_type = self.payment_type in ('outbound', 'transfer') and 'outbound' or 'inbound'

            domain = {'payment_method_id': [('payment_type', '=', payment_type), ('id', 'in', payment_methods_list)]}

            # Tasa de cambio en pago
            tasa_cambio = 1 / (self.env['res.currency'].search([('id','=',int(self.currency_id))],limit=1).rate)
            self.barmex_currency_rate = tasa_cambio

            if self.currency_id==33:
                self.barmex_currency_rate= 1.0

            if self.env.context.get('active_model') == 'account.move':
                active_ids = self._context.get('active_ids')
                invoices = self.env['account.move'].browse(active_ids)
                self.amount = abs(self._compute_payment_amount(invoices, self.currency_id, self.journal_id, self.payment_date))

            return {'domain': domain}
        return {}