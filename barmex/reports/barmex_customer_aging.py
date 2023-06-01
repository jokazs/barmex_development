import logging
from datetime import datetime, timedelta

from odoo import models, api, fields, _

_logger = logging.getLogger(__name__)


class CustomerAging(models.TransientModel):
    _name = "barmex.customer.aging"
    _description = "Customer Aging Report"
    _check_company_auto = True

    name = fields.Char(default="Barmex Customer Aging")

    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.company)

    date = fields.Date(string="Date",
                       default=fields.Datetime.today)

    # Partner
    sale_zone_ids = fields.Many2many('barmex.sale.zone',
                                     string="Sale Zone")

    partner_ids = fields.Many2many('res.partner',
                                   string="Customer")

    user_ids = fields.Many2many('hr.employee',
                                string="Saleman")

    # Invoice
    collector_ids = fields.Many2many('res.users',
                                     string="Collector")

    # Account move
    journal_ids = fields.Many2many('account.journal',
                                   string="Journal",
                                   domain="[('type','=','sale')]")

    currency_id = fields.Many2one('res.currency',
                                  string="Currency")

    line_ids = fields.One2many('barmex.customer.aging.line',
                               'header_id')

    def _sale_zones(self):
        res = []
        for record in self.sale_zone_ids:
            res.append(record.name)

        res = sorted(set(res), key=res.index)

        return ', '.join(res)

    def _partners(self):
        res = []
        for record in self.partner_ids:
            res.append(record.name)

        res = sorted(set(res), key=res.index)

        return ', '.join(res)

    def _users(self):
        res = []
        for record in self.user_ids:
            res.append(record.name)

        res = sorted(set(res), key=res.index)

        return ', '.join(res)

    def _collectors(self):
        res = []
        for record in self.collector_ids:
            res.append(record.name)

        res = sorted(set(res), key=res.index)

        return ', '.join(res)

    def _journals(self):
        res = []
        for record in self.journal_ids:
            res.append(record.name)

        res = sorted(set(res), key=res.index)

        return ', '.join(res)

    def create_report(self):
        domain = []

        if self.partner_ids:
            domain.append(('id', 'in', self.partner_ids.ids))

        if self.sale_zone_ids:
            domain.append(('lco_sale_zone', 'in', self.sale_zone_ids.ids))

        partners = self.env['res.partner'].search(domain)

        account = []

        for record in partners:
            account.append(record.property_account_receivable_id.id)

        domain = [('reconciled', '=', False), ('amount_residual', '!=', 0), ('account_id', 'in', account)]

        if self.partner_ids:
            domain.append(('partner_id', 'in', self.partner_ids.ids))

        if self.user_ids:
            user = []
            for record in self.user_ids:
                user.append(record.user_id.id)

            domain.append(('move_id.invoice_user_id', 'in', user))

        if self.currency_id:
            domain.append(('move_id.currency_id', '=', self.currency_id.id))

        if self.collector_ids:
            domain.append(('move_id.collector_id.user_id', 'in', self.collector_ids.ids))

        moves = self.env['account.move.line'].search(domain, order="partner_id,amount_residual asc")

        self.line_ids = False
        for record in moves:
            a = False
            b = False
            c = False
            d = False
            e = False
            f = False
            diff = (self.date - record.date_maturity)

            if diff <= timedelta(days=0):
                a = record.amount_residual
            elif diff >= timedelta(days=1) and diff <= timedelta(days=30):
                b = record.amount_residual
            elif diff >= timedelta(days=31) and diff <= timedelta(days=60):
                c = record.amount_residual
            elif diff >= timedelta(days=61) and diff <= timedelta(days=90):
                d = record.amount_residual
            elif diff >= timedelta(days=91) and diff <= timedelta(days=120):
                e = record.amount_residual
            elif diff > timedelta(days=120):
                f = record.amount_residual

            self.line_ids = [(0, 0, {
                'move_id': record.move_id.id,
                'partner_id': record.partner_id.id,
                'due_date': record.date_maturity,
                'real_payment_date': record.real_date,
                'journal_id': record.move_id.journal_id.id,
                'account_id': record.account_id.id,
                'expected_date': record.expected_pay_date,
                'currency_id': record.move_id.currency_id.id,
                'to_date': a,
                'range_1': b,
                'range_2': c,
                'range_3': d,
                'range_4': e,
                'older': f,
            })]

    def print_report(self):
        return self.env.ref('barmex.barmex_customer_aging_report').report_action(self)


class CustomerAgingLine(models.TransientModel):
    _name = "barmex.customer.aging.line"
    _description = "Customer Aging Report"

    move_id = fields.Many2one('account.move',
                              string="Origin")

    header_id = fields.Many2one('barmex.customer.aging')

    partner_id = fields.Many2one('res.partner',
                                 string="Customer")

    sale_id = fields.Many2one('sale.order',
                              string="Sale Order")

    due_date = fields.Date(string="Due Date")

    real_payment_date = fields.Date(string="Real Payment Date")

    journal_id = fields.Many2one('account.journal',
                                 string="Journal")

    account_id = fields.Many2one('account.account',
                                 string="Account")

    expected_date = fields.Date(string="Expected Payment Date")

    currency_id = fields.Many2one('res.currency',
                                  string="Currency")

    to_date = fields.Monetary(string="To Date")

    range_1 = fields.Monetary(string="1 - 30")

    range_2 = fields.Monetary(string="31 - 60")

    range_3 = fields.Monetary(string="61 - 90")

    range_4 = fields.Monetary(string="91 - 120")

    older = fields.Monetary(string="Older")


