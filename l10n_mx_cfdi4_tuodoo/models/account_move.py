# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools.float_utils import float_repr
from io import BytesIO
import xmlrpc.client
import base64
import requests

from lxml import etree
from lxml.objectify import fromstring
from odoo.tools import DEFAULT_SERVER_TIME_FORMAT
from odoo.tools.xml_utils import _check_with_xsd
from pytz import timezone
from datetime import datetime
from dateutil.relativedelta import relativedelta

CFDI_TEMPLATE_40 = 'l10n_mx_cfdi4_tuodoo.cfdiv40'
CFDI_XSLT_CADENA40 = 'l10n_mx_cfdi4_tuodoo/data/%s/cadenaoriginal.xslt'
CFDI_XSLT_CADENA_TFD40 = 'l10n_mx_cfdi4_tuodoo/data/xslt/4.0/cadenaoriginal_TFD_1_1.xslt'

CFDI_TEMPLATE_33 = 'l10n_mx_edi.cfdiv33'
CFDI_XSLT_CADENA = 'l10n_mx_edi/data/%s/cadenaoriginal.xslt'
CFDI_XSLT_CADENA_TFD = 'l10n_mx_edi/data/xslt/3.3/cadenaoriginal_TFD_1_1.xslt'

import logging
_logger = logging.getLogger(__name__)


def create_list_html(array):
    '''Convert an array of string to a html list.
    :param array: A list of strings
    :return: an empty string if not array, an html list otherwise.
    '''
    if not array:
        return ''
    msg = ''
    for item in array:
        msg += '<li>' + item + '</li>'
    return '<ul>' + msg + '</ul>'


class AccountMove(models.Model):
    _inherit = "account.move"

    

    def _l10n_mx_edi_get_payment_policy(self):
        self.ensure_one()
        version = self.l10n_mx_edi_get_pac_version()
        term_ids = self.invoice_payment_term_id.line_ids
        if version == '3.2':
            if len(term_ids.ids) > 1:
                return 'Pago en parcialidades'
            else:
                return 'Pago en una sola exhibición'
        elif version in ('3.3', '4.0') and self.invoice_date_due and self.invoice_date:
            if self.type == 'out_refund':
                return 'PUE'
            # In CFDI 3.3 - rule 2.7.1.43 which establish that
            # invoice payment term should be PPD as soon as the due date
            # is after the last day of  the month (the month of the invoice date).
            if self.invoice_date_due.month > self.invoice_date.month or \
                    self.invoice_date_due.year > self.invoice_date.year or \
                    len(term_ids) > 1:  # to be able to force PPD
                return 'PPD'
            return 'PUE'
        return ''

    @api.model
    def l10n_mx_edi_get_pac_version(self):
        '''Returns the cfdi version to generate the CFDI.
        In December, 1, 2017 the CFDI 3.2 is deprecated, after of July 1, 2018
        the CFDI 3.3 could be used.
        '''
        version = ''
        print("version",version)
        for rec in self:
            if rec.partner_id.type_cfdi == '33':
                print("3.3")
                version = self.env['ir.config_parameter'].sudo().get_param('l10n_mx_edi_cfdi_version', '3.3')
                version = '3.3'
            else:
                print("4.0")
                version = '4.0'
        if len(version) > 0:
            return version
        else:
            move_id = self.env['account.move'].browse(self.env.context['active_ids'])
            if move_id:
                for m in move_id:
                    if m.partner_id.type_cfdi == '33':
                        version = '3.3'
                        return version
                    else:
                        print("4.0")
                        version = '4.0'
                        return version


    def _l10n_mx_edi_create_cfdi(self):
        '''Creates and returns a dictionnary containing 'cfdi' if the cfdi is well created, 'error' otherwise.
        '''
        self.ensure_one()
        qweb = self.env['ir.qweb']
        error_log = []
        company_id = self.company_id
        pac_name = company_id.l10n_mx_edi_pac
        if self.l10n_mx_edi_external_trade:
            # Call the onchange to obtain the values of l10n_mx_edi_qty_umt
            # and l10n_mx_edi_price_unit_umt, this is necessary when the
            # invoice is created from the sales order or from the picking
            self.invoice_line_ids.onchange_quantity()
            self.invoice_line_ids._set_price_unit_umt()
        values = self._l10n_mx_edi_create_cfdi_values()

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
            return {'error': _('Please check your configuration: ') + create_list_html(error_log)}

        # -Compute date and time of the invoice
        time_invoice = datetime.strptime(self.l10n_mx_edi_time_invoice,
                                         DEFAULT_SERVER_TIME_FORMAT).time()
        # -----------------------
        # Create the EDI document
        # -----------------------
        version = self.l10n_mx_edi_get_pac_version()
        print("version",version)
        # -Compute certificate data
        values['date'] = datetime.combine(
            fields.Datetime.from_string(self.invoice_date), time_invoice).strftime('%Y-%m-%dT%H:%M:%S')
        values['certificate_number'] = certificate_id.serial_number
        values['certificate'] = certificate_id.sudo().get_data()[0]

        # -Compute cfdi
        if self.partner_id.type_cfdi == '33':
            cfdi = qweb.render(CFDI_TEMPLATE_33, values=values)
            attachment = self.sudo().env.ref('l10n_mx_edi.xsd_cached_cfdv33_xsd', False)
        else:
            cfdi = qweb.render(CFDI_TEMPLATE_40, values=values)
            attachment = self.sudo().env.ref('l10n_mx_cfdi4_tuodoo.xsd_cached_cfdv40_xsd', False)
        cfdi = cfdi.replace(b'xmlns__', b'xmlns:')
        node_sello = 'Sello'
        xsd_datas = base64.b64decode(attachment.datas) if attachment else b''

        # -Compute cadena
        tree = self.l10n_mx_edi_get_xml_etree(cfdi)
        print("tree",tree)
        if self.partner_id.type_cfdi == '33':
            cadena = self.l10n_mx_edi_generate_cadena(CFDI_XSLT_CADENA % version, tree)
        else:
            cadena = self.l10n_mx_edi_generate_cadena(CFDI_XSLT_CADENA40 % version, tree)
        tree.attrib[node_sello] = certificate_id.sudo().get_encrypted_cadena(cadena)

        # Check with xsd
        if xsd_datas:
            try:
                with BytesIO(xsd_datas) as xsd:
                    _check_with_xsd(tree, xsd)
            except (IOError, ValueError):
                _logger.info(
                    _('The xsd file to validate the XML structure was not found'))
            except Exception as e:
                return {'error': (_('The cfdi generated is not valid') +
                                  create_list_html(str(e).split('\\n')))}

        return {'cfdi': etree.tostring(tree, pretty_print=True, xml_declaration=True, encoding='UTF-8')}
        

    @api.model
    def _get_l10n_mx_edi_cadena(self):
        self.ensure_one()
        # get the xslt path
        if self.partner_id.type_cfdi == '33':
            xslt_path = CFDI_XSLT_CADENA_TFD
        else:
            xslt_path = CFDI_XSLT_CADENA_TFD40
        # get the cfdi as eTree
        cfdi = base64.decodebytes(self.l10n_mx_edi_cfdi)
        cfdi = self.l10n_mx_edi_get_xml_etree(cfdi)
        cfdi = self.l10n_mx_edi_get_tfd_etree(cfdi)
        # return the cadena
        return self.l10n_mx_edi_generate_cadena(xslt_path, cfdi)

    def get_new_cfdi_fields(self, name):
        if name == 'Exportacion':
            return "01"
        if name == 'FacAtrAdquirente':
            return False

    def show(self, line):
        return 0


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
        for rec in invoice:
            for inv in rec['invoice']:
                for tax in inv.amount_by_group:
                    if tax[0] == "IVA 16%":
                        ivabase16 += tax[2]
                        ivatra16 += tax[1]
                    if tax[0] == "IVA Retencion 10.67%":
                        retiva += tax[1]
                    if tax[0] == "ISR Retencion 10%":
                        retisr += tax[1]

                    if tax[0] == "IVA 8%":
                        ivabase08 += tax[2]
                        ivatra08 += tax[1]

        if self.currency_id.name == 'MXN':

            vals = {
                'ivabase08':round(float(ivabase08),2),
                'ivatra08':round(float(ivatra08),2),
                'ivabase16':round(float(ivabase16),2),
                'ivatra16':round(float(ivatra16),2),
                'retiva': round(float(retiva),2),
                'retisr': round(float(retisr),2),
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

    l10n_mx_edi_usage = fields.Selection(
        selection_add=[
            ('S01', 'Sin efectos fiscales.'),
            ('CP01', 'Pagos'),
            ('CN01', 'Nómina'),
        ])


    type_cfdi = fields.Selection(
        [('33', '3.3'),
         ('40', '4.0'),],
         default="33",
        string="Version CFDI 3.3 o 4.0",)

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id.l10n_mx_edi_usage:
            self.l10n_mx_edi_usage = self.partner_id.l10n_mx_edi_usage
        else:
            self.l10n_mx_edi_usage = ''
        #if self.partner_id.l10n_mx_edi_payment_method_id:
        #    self.write({'l10n_mx_edi_payment_method_id':self.partner_id.l10n_mx_edi_payment_method_id.id })
        #else:
        #    self.write({'l10n_mx_edi_payment_method_id':False})
        if self.partner_id.type_cfdi:
            self.type_cfdi = self.partner_id.type_cfdi
        return super(AccountMove, self)._onchange_partner_id()

    def xxx(self,v):
        print("ddddddddd",v)
        
