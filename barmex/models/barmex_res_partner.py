import re
import datetime

from odoo import models, fields, api, _
from odoo.exceptions import Warning, AccessError, UserError, ValidationError
from odoo.osv.expression import get_unaccent_wrapper


class ResPartner(models.Model):
    _inherit = ['res.partner']
    _sql_constraints = [('unique_partner_barmex_id_cust', 'unique(barmex_id_cust)',
                         _('ID number is not unique!')),
                        ('unique_partner_barmex_id_vend', 'unique(barmex_id_vend)',
                         _('ID number is not unique!'))
                        ]

    company_id = fields.Many2one('res.company',
                                 'Company',
                                 index=True,
                                 default=lambda self: self.env.company)

    vendor_type = fields.Selection(
        [
            ('national', 'National'),
            ('foreign', 'Foreign')
        ],
        string='Vendor type'
    )

    tax_id = fields.Char(string='Foreign vendor Tax ID',
                         copy=False)

    credit_days = fields.Integer(string='Credit days')

    type_vendor = fields.Many2one('barmex.vendor.type')

    product_reference_id = fields.One2many('barmex.customer.codes',
                                           'partner_id')

    account_moves_ids = fields.One2many('account.move',
                                        'movement_id')

    ref_payment_ids = fields.One2many('account.payment',
                                      'payment_partner_id',
                                      string="Factoring payments")

    invoice_files = fields.One2many('barmex.invoice',
                                    'invoice_id',
                                    string='Files')

    property_payment_term_id = fields.Many2one('account.payment.term', company_dependent=True,
                                               string='Customer Payment Terms',
                                               help="This payment term will be used instead of the default one for sales orders and customer invoices",
                                               required=True)

    name = fields.Char(index=True,
                       required=True)

    barmex_id_cust = fields.Char(string='Customer ID number',
                            size=6)

    barmex_id_vend = fields.Char(string='Vendor ID number',
                            size=6)

    lco_partner_modify_salesperson = fields.Boolean(string='Modify salesperson',
                                                    track_visibility=True)

    lco_property_product_pricelist = fields.Many2one('product.pricelist',
                                                     on_delete='set null',
                                                     string='Tarifa MXN')

    lco_property_product_pricelist_usd = fields.Many2one('product.pricelist',
                                                     on_delete='set null',
                                                     string='Tarifa USD')

    lco_sale_zone = fields.Many2one('barmex.sale.zone',
                                    string='Sale zone',
                                    stored=True,
                                    track_visibility=True,
                                    check_company=True)

    lco_fact_global = fields.Boolean(string='Global invoicing',
                                     default=False)

    lco_customer_type = fields.Many2one('barmex.partner.type',
                                        string='Customer type',
                                        stored=True)

    l10n_mx_edi_usage = fields.Selection([
        ('G01', 'Acquisition of merchandise'),
        ('G02', 'Returns, discounts or bonuses'),
        ('G03', 'General expenses'),
        ('I01', 'Constructions'),
        ('I02', 'Office furniture and equipment investment'),
        ('I03', 'Transportation equipment'),
        ('I04', 'Computer equipment and accessories'),
        ('I05', 'Dices, dies, molds, matrices and tooling'),
        ('I06', 'Telephone communications'),
        ('I07', 'Satellite communications'),
        ('I08', 'Other machinery and equipment'),
        ('D01', 'Medical, dental and hospital expenses.'),
        ('D02', 'Medical expenses for disability'),
        ('D03', 'Funeral expenses'),
        ('D04', 'Donations'),
        ('D05', 'Real interest effectively paid for mortgage loans (room house)'),
        ('D06', 'Voluntary contributions to SAR'),
        ('D07', 'Medical insurance premiums'),
        ('D08', 'Mandatory School Transportation Expenses'),
        ('D09', 'Deposits in savings accounts, premiums based on pension plans.'),
        ('D10', 'Payments for educational services (Colegiatura)'),
        ('P01', 'To define'),
    ], 'CFDI Usage', default='P01',
        help='Used in CFDI 3.3 to express the key to the usage that will '
             'gives the receiver to this invoice. This value is defined by the '
             'customer. \nNote: It is not cause for cancellation if the key set is '
             'not the usage that will give the receiver of the document.')

    # Include docs in risk
    sale_order_include = fields.Boolean(string='Include Sale Order')

    draft_invoice_include = fields.Boolean(string='Include Draft Invoice')

    open_invoice_include = fields.Boolean(string='Include Open Invoice')

    partially_payed_invoice_include = fields.Boolean(string='Include Partially Payed Invoice')

    open_account_include = fields.Boolean(string='Include Open Account Moves')

    partially_open_account_include = fields.Boolean(string='Include Partially Open Account Moves')

    # Risk amounts
    sale_order_risk = fields.Monetary(string='Sale Orders Included',
                                      compute='_get_amounts',
                                      currency_field='credit_currency')

    draft_invoice_risk = fields.Monetary(string='Draft Invoices Included',
                                         compute='_get_amounts',
                                         currency_field='credit_currency')

    open_invoice_risk = fields.Monetary(string='Invoices Without Payment Included',
                                        compute='_get_amounts',
                                        currency_field='credit_currency')

    partially_payed_invoice_risk = fields.Monetary(string='Partially Payed Invoices Included',
                                                   compute='_get_amounts',
                                                   currency_field='credit_currency')

    open_account_risk = fields.Monetary(string='Open Account Moves Included',
                                        compute='_get_amounts',
                                        currency_field='credit_currency')

    partially_open_account_risk = fields.Monetary(string='Partially Open Account Moves Included',
                                                  compute='_get_amounts',
                                                  currency_field='credit_currency')

    total_risk = fields.Monetary(string='Total Risk',
                                 compute='_total_risk',
                                 currency_field='credit_currency')

    # Credit limit
    sale_order_amount = fields.Monetary(string='Sale Order Amount',
                                        currency_field='credit_currency')

    draft_invoice_amount = fields.Monetary(string='Draft Invoices Amount',
                                           currency_field='credit_currency')

    open_invoice_amount = fields.Monetary(string='Open Invoices Amount',
                                          currency_field='credit_currency')

    partially_payed_invoice_amount = fields.Monetary(string='Partially Payed Invoice Amount',
                                                     currency_field='credit_currency')

    open_account_amount = fields.Monetary(string='Open Account Moves Amount',
                                          currency_field='credit_currency')

    partially_open_account_amount = fields.Monetary(string='Partially Open Account Moves Amount',
                                                    currency_field='credit_currency')

    general_limit = fields.Monetary(string='General Credit',
                                    currency_field='credit_currency')

    # Limit exceeded
    sale_order_exceeded = fields.Boolean(string='Sale Order Limit Exceeded',
                                         readonly=True,
                                         compute='_credit_limit_exceeded')

    draft_invoice_exceeded = fields.Boolean(string='Draft Invoice Limit Exceeded',
                                            readonly=True,
                                            compute='_credit_limit_exceeded')

    open_invoice_exceeded = fields.Boolean(string='Open Invoice Limit Exceeded',
                                           readonly=True,
                                           compute='_credit_limit_exceeded')

    partially_payed_invoice_exceeded = fields.Boolean(string='Partially Payed Limit Exceeded',
                                                      readonly=True,
                                                      compute='_credit_limit_exceeded')

    open_account_exceeded = fields.Boolean(string='Open Account Moves Exceeded',
                                           compute='_credit_limit_exceeded',
                                           readonly=True)

    partially_open_account_exceeded = fields.Boolean(string='Partially Open Account Moves Exceeded',
                                                     compute='_credit_limit_exceeded',
                                                     readonly=True)

    credit_exceeded = fields.Boolean(string='General Limit Exceeded',
                                     readonly=True,
                                     compute='_credit_limit_exceeded')

    credit_currency = fields.Many2one('res.currency',
                                      string='Credit Currency',
                                      default=lambda self: self.env.company.currency_id)

    due_invoice_lock = fields.Boolean(string='Lock By Due Invoice',
                                      default=True)

    exceed_limit = fields.Boolean(string='Exceed Credit Limit',
                                  default=False)

    sale_order_available = fields.Monetary(string='Sale Order Credit Available',
                                           currency_field='credit_currency',
                                           readonly=True,
                                           compute='_credit_available')

    credit_available = fields.Monetary(string='Credit Available',
                                       currency_field='credit_currency',
                                       readonly=True,
                                       compute='_credit_available')

    locked_by_due = fields.Boolean(string='Credit Lock By Due Invoice',
                                   readonly=True,
                                   compute='_due_invoice')

    collector_ids = fields.One2many('barmex.collector',
                                    'partner_id',
                                    string='Collectors')

    cobrador_employee_ids = fields.Many2one('hr.employee', string='Cobrador')

    corporate_res_partner = fields.Many2one('barmex.corporate', 'Corporativo')

    lco_property_product_pricelist_extra = fields.Many2one('product.pricelist',
                                                     on_delete='set null',
                                                     string='Tarifa extra')

    lco_property_product_pricelist_extra_usd = fields.Many2one('product.pricelist',
                                                     on_delete='set null',
                                                     string='Tarifa extra USD')

    lco_is_prospect = fields.Boolean(string='Cliente prospecto')

    x_studio_codigo_de_proveedor=fields.Integer('Código de proveedor')

    type = fields.Selection(
        selection_add=[
            ('sale', 'Sale Contact'),
            ('purchase', 'Purchase Contact')
        ])

    cxc = fields.Boolean(compute='_check_group',
                         readonly=True)

    cxp = fields.Boolean(compute='_check_group',
                         readonly=True)

    sale = fields.Boolean(compute='_check_group',
                          readonly=True)

    purchase = fields.Boolean(compute='_check_group',
                              readonly=True)

    invoicing_currency = fields.Boolean(string="Invoicing in National Currency")

    is_admin = fields.Boolean(compute='_is_admin',
                              readonly=True)

    is_new = fields.Boolean(compute='_is_admin',
                              default=True,
                              readonly=True)

    addenda_id = fields.Many2one('barmex.addenda',
                                 string="Addenda")

    l10n_mx_edi_addenda = fields.Many2one('ir.ui.view',
                                          string='Addenda view',
                                          related="addenda_id.l10n_mx_edi_addenda",
                                          help='A view representing the addenda',
                                          domain=[('l10n_mx_edi_addenda_flag', '=', True)])

    invoicing_mail = fields.Char('Invoicing Mail Address')

    payment_mail = fields.Char('Payment Mail Address')

    proveedor_employee = fields.Many2one('hr.employee', string='Agente de Ventas')

    origen_cliente = fields.Char('Origen')

    forma_pago = fields.Char('Forma Pago')

    metodo_pago = fields.Char('Metodo Pago')

    email_notas_credito = fields.Char('Email Notas de Credito')

    email_complementos_pago = fields.Char('Email Complemento de Pago')

    x_l10n_mx_edi_payment_method_id = fields.Many2one('l10n_mx_edi.payment.method', 'Forma de pago')

    def _is_admin(self):
        ret = False
        for record in self:
            if self.user_has_groups('base.group_system'):
                ret = True
            record.update({
                'is_admin': ret,
                'is_new': ret,
            })

    def _due_invoice(self):
        for record in self:
            invoices = self.env['account.move'].search(
                [('partner_id', '=', record.id), ('state', '=', 'posted'), ('invoice_payment_state', '!=', 'paid'),
                 ('invoice_date_due', '<=', datetime.datetime.now().date())])

            ret = True if invoices else False

            record.update({
                'locked_by_due': ret,
            })

    def _get_amounts(self):
        for record in self:
            sale, draft, open, partial, account, pacc = 0, 0, 0, 0, 0, 0

            sales = self.env['sale.order'].search([('partner_id', '=', record.id), ('state', '=', 'sale')])
            moves = self.env['account.move.line'].search(
                [('partner_id', '=', record.id), ('reconciled', '=', False), ('debit', '>', 0),
                 ('move_id.type', '=', 'entry'), ('payment_id', '=', False),
                 ('account_id.user_type_id.type', '=', 'receivable'),
                 ('move_id.state', '=', 'posted')])

            for order in sales:
                sale += order.currency_id._convert(order.amount_total, record.credit_currency, self.env.company,
                                                   order.date_order)

            invoices = self.env['account.move'].search([('partner_id', '=', record.id)])
            for invoice in invoices:
                invoice_date = invoice.invoice_date if invoice.invoice_date else invoice.date
                if invoice.state == 'draft' or invoice.state == 'lock':
                    draft += invoice.currency_id._convert(invoice.amount_total, record.credit_currency,
                                                          self.env.company, invoice_date)

                elif invoice.amount_total > invoice.amount_residual:
                    partial += invoice.currency_id._convert(invoice.amount_residual, record.credit_currency,
                                                            self.env.company, invoice_date)

                elif invoice.state == 'posted' and invoice.amount_total == invoice.amount_residual:
                    open += invoice.currency_id._convert(invoice.amount_total, record.credit_currency, self.env.company,
                                                         invoice_date)

            for move in moves:
                currency_id = move.currency_id if move.currency_id else move.company_currency_id

                if not move.matched_credit_ids:
                    account += currency_id._convert(move.debit, record.credit_currency, self.env.company, move.date)
                else:
                    sum = 0
                    for payment in move.matched_credit_ids:
                        payment_cur = payment.currency_id if payment.currency_id else payment.company_currency_id
                        sum += payment_cur._convert(payment.amount, currency_id, self.env.company, payment.max_date)

                    pacc += currency_id._convert(move.debit - sum, record.credit_currency, self.env.company, move.date)

            record.update({
                'sale_order_risk': sale,
                'draft_invoice_risk': draft,
                'open_invoice_risk': open,
                'partially_payed_invoice_risk': partial,
                'open_account_risk': account,
                'partially_open_account_risk': pacc,
            })

    @api.depends('sale_order_include', 'draft_invoice_include', 'open_invoice_include',
                 'partially_payed_invoice_include', 'partially_open_account_include', 'open_account_include')
    def _total_risk(self):
        for record in self:
            sum = 0
            if record.sale_order_include:
                sum += record.sale_order_risk
            if record.draft_invoice_include:
                sum += record.draft_invoice_risk
            if record.open_invoice_include:
                sum += record.open_invoice_risk
            if record.partially_payed_invoice_include:
                sum += record.partially_payed_invoice_risk
            if record.open_account_include:
                sum += record.open_account_risk
            if record.partially_open_account_include:
                sum += record.partially_open_account_risk

            record.update({
                'total_risk': sum,
            })

    @api.depends('total_risk')
    def _credit_limit_exceeded(self):
        for record in self:
            sale, draft, open, partial, general, account, pacc = False, False, False, False, False, False, False

            if record.sale_order_include and record.sale_order_amount < record.sale_order_risk:
                sale = True

            if record.draft_invoice_include and record.draft_invoice_amount < record.draft_invoice_risk:
                draft = True

            if record.open_invoice_include and record.open_invoice_amount < record.open_invoice_risk:
                open = True

            if record.partially_payed_invoice_include and record.partially_payed_invoice_amount < record.partially_payed_invoice_risk:
                partial = True

            if record.open_account_include and record.open_account_amount < record.open_account_risk:
                account = True

            if record.partially_open_account_include and record.partially_open_account_amount < record.partially_open_account_risk:
                pacc = True

            if record.total_risk > record.general_limit:
                general = True

            record.update({
                'sale_order_exceeded': sale,
                'draft_invoice_exceeded': draft,
                'open_invoice_exceeded': open,
                'partially_payed_invoice_exceeded': partial,
                'credit_exceeded': general,
                'open_account_exceeded': account,
                'partially_open_account_exceeded': pacc,
            })

    @api.depends('total_risk', 'credit_limit')
    def _credit_available(self):
        for record in self:
            sale_risk = 0
            if record.sale_order_include:
                sale_risk = record.sale_order_risk
            record.update({
                'sale_order_available': record.sale_order_amount - sale_risk,
                'credit_available': record.general_limit - record.total_risk,
            })

    def related_orders(self):
        sales = self.env['sale.order'].search([('partner_id', '=', self.id), ('state', '=', 'sale')])

        return {
            'name': _('Sale Orders'),
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_id': False,
            'view_type': 'tree',
            'view_mode': 'list,form',
            'target': 'current',
            'domain': [('id', 'in', sales.ids)]
        }

    def related_invoices_draft(self):

        invoices = self.env['account.move'].search(
            [('partner_id', '=', self.id), ('type', '=', 'out_invoice'), ('state', 'in', ('draft', 'lock'))])

        return {
            'name': _('Invoices'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_id': False,
            'view_type': 'tree',
            'view_mode': 'tree,form',
            'target': 'current',
            'domain': [('id', 'in', invoices.ids)]
        }

    def related_invoices_open(self):

        ids = []
        invoices = self.env['account.move'].search(
            [('partner_id', '=', self.id), ('type', '=', 'out_invoice'), ('state', '=', 'posted')])

        for record in invoices:
            if record.amount_total == record.amount_residual:
                ids.append(record.id)

        return {
            'name': _('Invoices'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_id': False,
            'view_type': 'tree',
            'view_mode': 'tree,form',
            'target': 'current',
            'domain': [('id', 'in', ids)]
        }

    def related_invoices_partial(self):

        ids = []
        invoices = self.env['account.move'].search(
            [('partner_id', '=', self.id), ('type', '=', 'out_invoice'), ('state', '=', 'posted'),
             ('invoice_payments_widget', '!=', '')])

        for record in invoices:
            if record.amount_total != record.amount_residual:
                ids.append(record.id)

        return {
            'name': _('Invoices'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_id': False,
            'view_type': 'tree',
            'view_mode': 'tree,form',
            'target': 'current',
            'domain': [('id', 'in', ids)]
        }

    def related_moves(self):
        moves = self.env['account.move.line'].search(
            [('partner_id', '=', self.id), ('reconciled', '=', False), ('debit', '>', 0),
             ('move_id.type', '=', 'entry'), ('payment_id', '=', False),
             ('account_id.user_type_id.type', '=', 'receivable'),
             ('matched_credit_ids', '=', False)])

        return {
            'name': _('Account Moves'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move.line',
            'view_id': False,
            'view_type': 'tree',
            'view_mode': 'tree,form',
            'target': 'current',
            'domain': [('id', 'in', moves.ids)]
        }

    def related_moves_partial(self):
        moves = self.env['account.move.line'].search(
            [('partner_id', '=', self.id), ('reconciled', '=', False), ('debit', '>', 0),
             ('move_id.type', '=', 'entry'), ('payment_id', '=', False),
             ('account_id.user_type_id.type', '=', 'receivable'),
             ('matched_credit_ids', '!=', False)])

        return {
            'name': _('Account Moves'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move.line',
            'view_id': False,
            'view_type': 'tree',
            'view_mode': 'tree,form',
            'target': 'current',
            'domain': [('id', 'in', moves.ids)]
        }

    @api.model
    def create(self, vals):
        res = super(ResPartner, self).create(vals)

        if res.lco_property_product_pricelist or res.lco_property_product_pricelist_usd:
            # Create record on barmex price list table
            cust_pl = self.env['barmex.customer.product.pricelist'].create(
                {
                    'partner_id': res.id,
                    'pricelist_id': res.lco_property_product_pricelist.id,
                    'pricelist_usd_id': res.lco_property_product_pricelist_usd.id,
                    'pricelist_extra_id': res.lco_property_product_pricelist_usd.id,
                    'reference': _('Set on customer creation')
                })

            prod_pl = self.env['product.pricelist'].browse(res.lco_property_product_pricelist.id)

            # Create relation to price list table (required as if not included customer id appears blank
            prod_pl.update(
                {
                    'customer_ids': [(4, cust_pl.id)]
                })


        ## Second price List for Barmex
        # if res.lco_property_product_pricelist_usd:

        #     # Create record on barmex price list table
        #     cust_pl = self.env['barmex.customer.product.pricelist'].create(
        #         {
        #             'partner_id': res.id,

        #             'pricelist_id': res.lco_property_product_pricelist_usd.id,
        #             'reference': _('Set on customer creation')
        #         })

        #     prod_pl = self.env['product.pricelist'].browse(res.lco_property_product_pricelist_usd.id)

        #     # Create relation to price list table (required as if not included customer id appears blank
        #     prod_pl.update(
        #         {
        #             'customer_ids': [(4, cust_pl.id)]
        #         })

        return res

    @api.depends('lco_property_product_pricelist')
    @api.onchange('lco_property_product_pricelist')
    def change_pricelist(self):
        try:
            melleva = self.env['barmex.customer.product.pricelist'].search([('partner_id.id', '=', self._origin.id)])[0]
            melleva.pricelist_id = self.lco_property_product_pricelist.id
        except: 
            return {
                'type': 'ir.actions.client',
                'tag': 'reload', #display_notification
                'params': {
                    'message': 'El cliente no tiene lista de precios definida',
                    'type': 'success',
                    'sticky': False,
                }
            }


    @api.onchange('lco_property_product_pricelist_usd')
    def change_pricelist_usd(self):
        try:
            melleva = self.env['barmex.customer.product.pricelist'].search([('partner_id.id', '=', self._origin.id)])[0]
            melleva.pricelist_usd_id = self.lco_property_product_pricelist_usd.id
        except: 
            return {
                'type': 'ir.actions.client',
                'tag': 'reload', #display_notification
                'params': {
                    'message': 'El cliente no tiene lista de precios definida',
                    'type': 'success',
                    'sticky': False,
                }
            }

    @api.onchange('lco_property_product_pricelist_extra')
    def change_pricelist_extra(self):
        try:
            melleva = self.env['barmex.customer.product.pricelist'].search([('partner_id.id', '=', self._origin.id)])[0]
            melleva.pricelist_extra_id = self.lco_property_product_pricelist_extra.id
        except: 
            return {
                'type': 'ir.actions.client',
                'tag': 'reload', #display_notification
                'params': {
                    'message': 'El cliente no tiene lista de precios definida',
                    'type': 'success',
                    'sticky': False,
                }
            }

    @api.onchange('user_id')
    def UpdateSaleZone(self):
        self.lco_sale_zone = self.user_id.employee_id.address_id.lco_sale_zone
        self.lco_partner_modify_salesperson = False

    @api.onchange('vendor_type')
    def _positive_document(self):
        if self.vendor_type == 'national':
            return {
                'warning': {
                    'title': _('Positive valuation'),
                    'message': _("Don't forget to include positive valuation for this vendor")
                }
            }

    @api.onchange('barmex_id_cust','barmex_id_vend')
    def change_id(self):
        self.user_id.barmex_id_cust = self.barmex_id_cust
        self.user_id.barmex_id_vend = self.barmex_id_vend

    @api.constrains('barmex_id_cust','barmex_id_vend')
    def _is_ID(self):
        if self.barmex_id_cust:
            if not re.match(r"^[0-9]{0,6}$", self.barmex_id_cust):
                raise ValidationError(_("ID number contains invalid values!"))

        if self.barmex_id_vend:
            if not re.match(r"^[0-9]{0,6}$", self.barmex_id_vend):
                raise ValidationError(_("ID number contains invalid values!"))

    @api.constrains('name')
    def _register_vendor(self):
        if self.user_id:
            if not self.vat:
                if self.type in ['contact', 'invoice']:
                    # if self.vendor_type == 'national':
                    raise ValidationError(_("VAT is required"))
            elif not self.validateRFC():
                raise ValidationError(_("Invalid VAT"))
            elif not self.street_name or not self.l10n_mx_edi_colony or not self.l10n_mx_edi_locality_id or not self.city \
                    or not self.state_id or not self.country_id:
                raise ValidationError(_("Address values are missing"))

    @api.constrains('tax_id')
    def _tax_id(self):
        if self.vendor_type == 'foreign':
            if not self.tax_id:
                raise ValidationError(_("Tax Id required"))
            else:
                vendor = self.env['res.partner'].search([('tax_id', '=', self.tax_id), ('id', '!=', self.id)])
                if vendor:
                    raise ValidationError(_("Tax id not unique"))

    @api.constrains('vat')
    def _rfc(self):
        for contact in self:
            if not contact.vat:
                raise ValidationError(_("VAT is required"))
            elif not contact.validateRFC():
                raise ValidationError(_("Invalid VAT"))

    def validateRFC(self):
        ret = False

        if 'XAXX' in self.vat or 'XEXX' in self.vat or 'xaxx' in self.vat or 'xexx' in self.vat:
            if re.match(r'^(XAXX|XEXX)010101000$', self.vat):
                ret = True
        else:
            if re.match(r'^[A-Z]{3,4}[0-9]{6}[A-Z0-9]{3}$', self.vat):
                ret = True

        return ret

    def _update_delivery(self, lock):
        operation = self.env['stock.picking.type'].search([('code', '=', 'outgoing')], limit=1)

        if lock:
            deliveries = self.env['stock.picking'].search(
                [('partner_id', '=', self.id), ('state', '=', 'assigned'), ('picking_type_id', '=', operation.id)])

            for record in deliveries:
                record.state = 'lock'
        else:
            deliveries = self.env['stock.picking'].search(
                [('partner_id', '=', self.id), ('state', '=', 'lock'), ('picking_type_id', '=', operation.id)])
            for record in deliveries:
                record.state = 'assigned'

    def credit_check(self):
        for record in self:
            if record.credit_exceeded:
                record._update_delivery(True)
            else:
                record._update_delivery(False)

    def credit_check_automated(self):
        self.env['res.partner'].search([('exceed_limit','=',False)]).credit_check()

    def _check_group(self):
        for record in self:
            cxc = _('Barmex Account Receivable')
            cxp = _('Barmex Account Payable')
            sale = _('Barmex Sales')
            purchase = _('Barmex Purchase')

            cxc = self.env['res.groups'].sudo().search([('name', '=', cxc)])
            cxp = self.env['res.groups'].sudo().search([('name', '=', cxp)])
            sale = self.env['res.groups'].sudo().search([('name', '=', sale)])
            purchase = self.env['res.groups'].sudo().search([('name', '=', purchase)])

            is_cxc = self.env.user.id in cxc.users.ids
            is_cxp = self.env.user.id in cxp.users.ids
            is_sale = self.env.user.id in sale.users.ids
            is_purchase = self.env.user.id in purchase.users.ids

            record.update({
                'cxc': is_cxc,
                'cxp': is_cxp,
                'sale': is_sale,
                'purchase': is_purchase,
            })

    def _contacts_domain(self):
        types = ['contact', 'invoice', 'delivery', 'other']

        if self.user_has_groups('barmex.purchase_contacts'):
            types.append('purchase')

        if self.user_has_groups('barmex.sale_contacts'):
            types.append('sale')

        if self.user_has_groups('base.group_private_addresses'):
            types.append('private')

        return [('active', '=', True), ('type', 'in', types)]

    child_ids = fields.One2many('res.partner', 'parent_id', string='Contact', domain=_contacts_domain)

    @api.constrains('vat', 'country_id')
    def check_vat(self):
        return

    #@api.multi
    def name_get(self):
        result = []
        for record in self:
            #rec_name = "%s - (%s)" % (record.barmex_id_cust, record.name)
            rec_name = record.name
            result.append((record.id,rec_name))

        return result

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        self = self.with_user(name_get_uid or self.env.uid)
        # as the implementation is in SQL, we force the recompute of fields if necessary
        self.recompute(['display_name'])
        self.flush()
        if args is None:
            args = []
        order_by_rank = self.env.context.get('res_partner_search_mode') 
        if (name or order_by_rank) and operator in ('=', 'ilike', '=ilike', 'like', '=like'):
            self.check_access_rights('read')
            where_query = self._where_calc(args)
            self._apply_ir_rules(where_query, 'read')
            from_clause, where_clause, where_clause_params = where_query.get_sql()
            from_str = from_clause if from_clause else 'res_partner'
            where_str = where_clause and (" WHERE %s AND " % where_clause) or ' WHERE '

            # search on the name of the contacts and of its company
            search_name = name
            if operator in ('ilike', 'like'):
                search_name = '%%%s%%' % name
            if operator in ('=ilike', '=like'):
                operator = operator[1:]

            unaccent = get_unaccent_wrapper(self.env.cr)

            fields = self._get_name_search_order_by_fields()

            query = """SELECT res_partner.id
                         FROM {from_str}
                      {where} ({email} {operator} {percent}
                           OR {display_name} {operator} {percent}
                           OR {reference} {operator} {percent}
                           OR {vat} {operator} {percent})
                           -- don't panic, trust postgres bitmap
                     ORDER BY {fields} {display_name} {operator} {percent} desc,
                              {display_name}
                    """.format(from_str=from_str,
                               fields=fields,
                               where=where_str,
                               operator=operator,
                               email=unaccent('res_partner.barmex_id_cust'),
                               display_name=unaccent('res_partner.display_name'),
                               reference=unaccent('res_partner.ref'),
                               percent=unaccent('%s'),
                               vat=unaccent('res_partner.vat'),)

            where_clause_params += [search_name]*3  # for email / display_name, reference
            where_clause_params += [re.sub('[^a-zA-Z0-9]+', '', search_name) or None]  # for vat
            where_clause_params += [search_name]  # for order by
            if limit:
                query += ' limit %s'
                where_clause_params.append(limit)
            self.env.cr.execute(query, where_clause_params)
            partner_ids = [row[0] for row in self.env.cr.fetchall()]

            if partner_ids:
                return models.lazy_name_get(self.browse(partner_ids))
            else:
                return []
        return super(ResPartner, self)._name_search(name, args, operator=operator, limit=limit, name_get_uid=name_get_uid)

    @api.onchange('proveedor_employee')
    @api.depends('proveedor_employee')
    def proveedor_employee_change(self):
        if not self.proveedor_employee:
            self.lco_sale_zone = ""
        else:  
            self.lco_sale_zone = self.proveedor_employee.employee_sale_zone