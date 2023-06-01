from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import re
class ForeignTrade(models.Model):
    _name = 'barmex.foreign.trade'
    _description = 'Foreign trade'
    _order = 'id desc'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _check_company_auto = True
    _sql_constraints = [
        ('unique_petition', 'unique(year, customs,agent,petition,partner_id)', _('Petition number is not unique!'))]

    name = fields.Char(string="Name",
                       compute='set_name')

    petition_no = fields.Char(string="Petition Number")

    partner_id = fields.Many2one('res.partner',
                                 string='Vendor')

    move_id = fields.Many2one('stock.picking')

    tax_id = fields.Char(string='Tax ID',
                         store=True)

    year = fields.Char(string='Year', size=2,
                          required=True)

    customs = fields.Many2one('barmex.foreign.trade.customs',
                              string='Customs',
                              required=True)

    agent = fields.Integer(string='Agent',
                           required=True)

    petition = fields.Char('Petition',
        help='Optional field for entering the customs information in the case '
        'of first-hand sales of imported goods or in the case of foreign trade'
        ' operations with goods or services.\n'
        'The format must be:\n'
        ' - 2 digits of the year of validation followed by two spaces.\n'
        ' - 2 digits of customs clearance followed by two spaces.\n'
        ' - 4 digits of the serial number followed by two spaces.\n'
        ' - 1 digit corresponding to the last digit of the current year, '
        'except in case of a consolidated customs initiated in the previous '
        'year of the original request for a rectification.\n'
        ' - 6 digits of the progressive numbering of the custom.',
        copy=False,
                           required=True)

    petition_date = fields.Datetime('Petition date')

    exchange_rate = fields.Float('Exchange rate')

    usd_amount = fields.Float('USD Amount')

    insurance_amount = fields.Float('Insurance Amount')

    insurance = fields.Float('Insurance')

    freight = fields.Float('Freight')

    packaging = fields.Float('Packaging')

    other = fields.Float('Others')

    dta = fields.Float('DTA')

    vat = fields.Float('VAT')

    prv = fields.Float('PRV')

    igi = fields.Float('IGI')

    iva = fields.Float('IVA')

    additional_1 = fields.Float('Aditional 1')

    additional_2 = fields.Float('Aditional 2')

    val_mon_fac = fields.Float('Val. Mon. Fac.')

    val_dls_fac = fields.Float('Val. Dls. Fac.')

    customs_value = fields.Float('Customs Value')

    rate_invoice_cur = fields.Float('Rate Invoice Currency')

    brand = fields.Char('Brand')

    invoice_num = fields.Char('Invoice Number')

    invoice_date = fields.Date('Invoice Date')

    invoice_val_mxn = fields.Float('Invoice Value MXN')

    qty = fields.Integer('Petitions Qty',
                         default=1,
                         readonly=True)

    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.company)

    @api.constrains('tax_id')
    def _tax_id(self):
        if self.tax_id == '':
            raise ValidationError(_('Tax Id required'))

    @api.constrains('customs')
    def _customs(self):
        if self.customs == 0:
            raise ValidationError(_('Customs invalid'))

    @api.constrains('agent')
    def _agent(self):
        if self.agent == 0:
            raise ValidationError(_('Agent invalid'))

    @api.constrains('year')
    def _year(self):
        if self.year == 0:
            raise ValidationError(_('Year invalid'))

    @api.depends('petition', 'customs', 'agent', 'year')
    def set_name(self):
        for record in self:
            record.update({
                'name': f"{record.petition}"
            })

    #@api.depends('petition', 'customs', 'agent', 'year')
    #def set_petition(self):
    #    for record in self:
    #        record.update({
    #            'petition_no': f"{record.petition}"
    #        })

    #TOMADO DEL ARCHIVO l10n_mx_edi\models\account_move.py
    @api.constrains('petition')
    @api.onchange('petition')
    def _check_petition(self):
        """Check the validity of the 'petition' field."""
        if self.petition:
            pattern = re.compile(r'[0-9]{2}  [0-9]{2}  [0-9]{4}  [0-9]{7}')
            invalid_product_names = []
            if not pattern.match(self.petition):
                raise ValidationError(f"Error en el formato de pedimento. {self.petition} no es un formato válido. La separación entre digitos es con 2 espacios.")