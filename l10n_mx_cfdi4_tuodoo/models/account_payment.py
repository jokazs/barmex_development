from odoo import _, api, fields, models

import base64
from datetime import datetime
from itertools import groupby
import logging
import requests

from lxml import etree
from lxml.objectify import fromstring
from zeep import Client
from zeep.transports import Transport
from odoo import _, api, fields, models
from odoo.tools import DEFAULT_SERVER_TIME_FORMAT, float_is_zero
from odoo.tools.float_utils import float_compare
from odoo.tools.misc import html_escape
from odoo.exceptions import UserError
from . import account_move

_logger = logging.getLogger(__name__)

CFDI_TEMPLATE40 = 'l10n_mx_cfdi4_tuodoo.payment20'
CFDI_XSLT_CADENA40 = 'l10n_mx_cfdi4_tuodoo/data/4.0/cadenaoriginal.xslt'
CFDI_XSLT_CADENA_TFD40 = 'l10n_mx_cfdi4_tuodoo/data/xslt/4.0/cadenaoriginal_TFD_1_1.xslt'

CFDI_TEMPLATE = 'l10n_mx_edi.payment10'
CFDI_XSLT_CADENA = 'l10n_mx_edi/data/3.3/cadenaoriginal.xslt'
CFDI_XSLT_CADENA_TFD = 'l10n_mx_edi/data/xslt/3.3/cadenaoriginal_TFD_1_1.xslt'

class AccountPayment(models.Model):
    _inherit = "account.payment"


    def post(self):
        res = super(AccountPayment, self).post()
        self.update_values_tax()
        return res

    @api.model
    def _get_l10n_mx_edi_cadena(self):
        self.ensure_one()
        # get the xslt path
        if self.journal_id.type_cfdi == '33':
            print("_get_l10n_mx_edi_cadena 3.3")
            xslt_path = CFDI_XSLT_CADENA_TFD
        else:
            xslt_path = CFDI_XSLT_CADENA_TFD40
        # get the cfdi as eTree
        cfdi = base64.decodebytes(self.l10n_mx_edi_cfdi)
        cfdi = self.l10n_mx_edi_get_xml_etree(cfdi)
        cfdi = self.l10n_mx_edi_get_tfd_etree(cfdi)
        # return the cadena
        return self.env['account.move'].l10n_mx_edi_generate_cadena(xslt_path, cfdi)

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
            return {'error': _('Please check your configuration: ') + account_move.create_list_html(error_log)}

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
        if self.journal_id.type_cfdi == '33':
            print("xxxx 3.3 cfdi = qweb.render(CFDI_TEMPLATE_33, values=values)",CFDI_TEMPLATE,values)
            cfdi = qweb.render(CFDI_TEMPLATE, values=values)
        else:
            cfdi = qweb.render(CFDI_TEMPLATE40, values=values)

        # -Compute cadena
        tree = self.l10n_mx_edi_get_xml_etree(cfdi)
        if self.journal_id.type_cfdi == '33':
            print("xxxx 3.3 adena = self.env['account.move'].l10n_mx_edi_generate_cadena(CFDI_XSLT_CADENA, tree)",)
            cadena = self.env['account.move'].l10n_mx_edi_generate_cadena(
                CFDI_XSLT_CADENA, tree)
        else:
            cadena = self.env['account.move'].l10n_mx_edi_generate_cadena(
                CFDI_XSLT_CADENA40, tree)

        # Post append cadena
        tree.attrib['Sello'] = certificate_id.sudo().get_encrypted_cadena(cadena)

        # TODO - Check with XSD
        return {'cfdi': etree.tostring(tree, pretty_print=True, xml_declaration=True, encoding='UTF-8')}
    
    account_payment_taxes_ids = fields.One2many(
        'account.payment.taxes',
        'account_payment_id',
        string='Linea impuestos',
        ondelete="cascade"
    )

    @staticmethod
    def _get_string_cfdi(text, size=100):
        """Replace from text received the characters that are not found in the
        regex. This regex is taken from SAT documentation
        https://goo.gl/C9sKH6
        text: Text to remove extra characters
        size: Cut the string in size len
        Ex. 'Product ABC (small size)' - 'Product ABC small size'"""
        if not text:
            return None
        text = text.replace('|', ' ')
        return text.strip()[:size]

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
            if self.journal_id.type_cfdi == '33':
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



    def update_values_tax(self):
        for rec in self:
            if rec.journal_id.type_cfdi == '40':
                tax = self.env['account.payment.taxes']
                rec.account_payment_taxes_ids.unlink()
                if rec.reconciled_invoice_ids:
                    for r in rec.reconciled_invoice_ids:
                        for l in r.amount_by_group:
                            tax = self.env["account.tax"].search([('tax_group_id', '=', l[6]),('type_tax_use', '=', 'sale')], limit=1)
                            if l[1] > 0:
                                if int(l[2]) > 0:
                                    vals = {
                                        'type_impuestos': 'trasladodr',
                                        'base': l[2],
                                        'impuesto': '002',
                                        'tipofactor': tax.l10n_mx_cfdi_tax_type,
                                        'tasacuota': tax.amount,
                                        'importe': l[1],
                                        'invoice_id': r.id,
                                        'account_payment_id': rec.id,
                                    }
                                    self.env['account.payment.taxes'].create(vals)
                            if l[1] < 0:
                                if int(l[2]) > 0:
                                    vals = {
                                        'type_impuestos': 'retencionesdr',
                                        'base': l[2],
                                        'impuesto': '002',
                                        'tipofactor': tax.l10n_mx_cfdi_tax_type,
                                        'tasacuota': tax.amount,
                                        'importe': l[1],
                                        'invoice_id': r.id,
                                        'account_payment_id': rec.id,
                                    }
                                    self.env['account.payment.taxes'].create(vals)



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

            vals = {
                'ivabase08':ivabase08,
                'ivatra08':ivatra08,
                'ivabase16':ivabase16,
                'ivatra16':ivatra16,
                'retiva': retiva,
                'retisr': retisr,
            }
        else:
            vals = {
                'ivabase08': round(float(ivabase08) / float(currency),2),
                'ivatra08':round(float(ivatra08) / float(currency),2),
                'ivabase16': round(float(ivabase16) / float(currency),2),
                'ivatra16':round(float(ivatra16) / float(currency),2),
                'retiva': round(float(retiva) / float(currency),2),
                'retisr': round(float(retisr) / float(currency),2),
            }
                                        
        return vals