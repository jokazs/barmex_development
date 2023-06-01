import base64
import pytz
import xml.etree.ElementTree as ET
from odoo import models, fields, api, _
from datetime import datetime, date
from pytz import timezone


class Invoices(models.Model):
    _name = 'barmex.invoice'
    _description = 'Vendor invoices'
    _order = 'id desc'
    _check_company_auto = True
    _sql_constraints = [('unique_xml_uuid', 'unique(uuid)',
                         _('Duplicated UUID'))]

    invoice_id = fields.Many2one('account.move',
                                 string='Invoice')

    name = fields.Char(string='File Name',
                       readonly=True)

    file = fields.Binary(string='File')

    vendor = fields.Char(string='XML Vendor')

    uuid = fields.Char(string='UUID',
                       readonly=True)

    date = fields.Datetime(string='Invoice Date',
                           readonly=True)

    amount = fields.Monetary(string='Invoice amount',
                             readonly=True)

    currency_id = fields.Many2one('res.currency',
                                  string='Currency',
                                  default=lambda self: self.env.company.currency_id,
                                  readonly=True)

    partner_id = fields.Many2one('res.partner',
                                 string='Vendor',
                                 readonly=True)

    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.company)

    @api.onchange('file')
    def _upload_file(self):
        emisor = '{http://www.sat.gob.mx/cfd/3}Emisor'
        complemento = '{http://www.sat.gob.mx/cfd/3}Complemento'
        timbre = '{http://www.sat.gob.mx/TimbreFiscalDigital}TimbreFiscalDigital'

        try:
            xml_decoded = base64.b64decode(self.file)
            root = ET.fromstring(xml_decoded)
            vendor = root.find('./{}'.format(emisor)).attrib['Nombre']
            rfc = root.find('./{}'.format(emisor)).attrib['Rfc']
            partner = self.env['res.partner'].search([('vat', '=', rfc)], limit=1)
            uuid = root.find('./{}/{}'.format(complemento, timbre)).attrib['UUID']
            dt = root.attrib['Fecha']
            cur = root.attrib['Moneda']
            currency = self.env['res.currency'].search([('name', '=', cur)], limit=1)
            total = root.attrib['Total']
            self.date = self._fix_date(dt)
            self.vendor = vendor
            self.uuid = uuid
            self.partner_id = partner.id
            self.amount = total
            self.currency_id = currency.id
        except:
            return

    def _fix_date(self, dt):
        tz = timezone('Mexico/General')
        dt = datetime.strptime(dt, '%Y-%m-%dT%H:%M:%S')
        dt2 = tz.localize(dt)
        dt2 = dt2.astimezone(pytz.utc)
        dt2 = dt2.strftime('%Y-%m-%d %H:%M:%S')
        return datetime.strptime(dt2, '%Y-%m-%d %H:%M:%S')

    def write(self, vals):
        res = super(Invoices, self).write(vals)

        if self.uuid and self.invoice_id:
            for record in self.invoice_id:
                record.update({
                    'barmex_uuid': self.uuid,
                })

        return res