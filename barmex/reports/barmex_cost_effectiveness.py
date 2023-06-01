import logging
from datetime import datetime, timedelta

from odoo import models, api, fields, _

_logger = logging.getLogger(__name__)


class CostEffectiveness(models.TransientModel):
    _name = "barmex.cost.effectiveness"
    _description = "Cost Effectiveness Report"

    name = fields.Char(default="Barmex Cost Effectiveness")

    brand_ids = fields.Many2many('barmex.product.brand',
                                 string="Brand")

    date = fields.Date(string="Date")

    journal_ids = fields.Many2many('account.journal',
                                   string="Journal",
                                   domain="[('type','=','sale')]")

    partner_ids = fields.Many2many('res.partner',
                                   string="Customer")

    product_ids = fields.Many2many('product.product',
                                   string="Product")

    line_ids = fields.One2many('barmex.cost.effectiveness.line',
                               'header_id')

    from_date = fields.Date(string="From Date")

    to_date = fields.Date(string="To Date",
                          default=fields.Date.context_today)

    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.company)

    currency_id = fields.Many2one('res.currency',
                                  string="Currency",
                                  default=lambda self: self.env.company.currency_id)

    sale_amount = fields.Monetary(string="Sale Amount")

    cost = fields.Monetary(string="Cost")

    profit = fields.Monetary(string="Profit")

    def create_report(self):
        domain = [('move_id.state', '=', 'posted'), ('move_id.type', 'in', ('out_invoice', 'out_refund'))]

        if self.date:
            domain.append(('move_id.invoice_date', '=', self.date))
            self.from_date = self.date
            self.to_date = self.date

        if self.journal_ids:
            domain.append(('move_id.journal_id', 'in', self.journal_ids.ids))

        if self.partner_ids:
            domain.append(('move_id.partner_id', 'in', self.partner_ids.ids))

        if self.brand_ids:
            domain.append(('product_id.brand_id', 'in', self.brand_ids.ids))

        if self.product_ids:
            domain.append(('product_id', 'in', self.product_ids.ids))
        else:
            domain.append(('product_id', '!=', False))

        if not self.from_date:
            self.from_date = self.env['account.move.line'].search(domain, order='date asc', limit=1).date

        _logger.warning(domain)
        invoices = self.env['account.move.line'].search(domain)

        self.line_ids = False

        total_sale = 0
        total_cost = 0
        sign = 0
        for record in invoices:
            if record.move_id.type == 'out_invoice':
                sign = 1
            else:
                sign = -1

            amount = record.currency_id._convert(record.price_subtotal, self.env.company.currency_id, self.env.company,
                                                 record.move_id.invoice_date)
            cost = record.product_id.standard_price * record.quantity
            self.line_ids = [(0, 0, {
                'partner_id': record.move_id.partner_id.id,
                'invoice_id': record.move_id.id,
                'date': record.move_id.invoice_date,
                'product_id': record.product_id.id,
                'description': self._get_description(record.name),
                'qty': record.quantity * sign,
                'sale_amount': amount * sign,
                'cost': cost * sign,
                'profit': (amount - cost) * sign,
            })]
            total_sale += amount * sign
            total_cost += cost * sign

        self.sale_amount = total_sale
        self.cost = total_cost
        self.profit = total_sale - total_cost

    def brands(self):
        res = []
        for record in self.brand_ids:
            res.append(record.name)

        res = sorted(set(res), key=res.index)

        return ', '.join(res)

    def offices(self):
        res = []
        for record in self.journal_ids:
            res.append(record.name)

        res = sorted(set(res), key=res.index)

        return ', '.join(res)

    def customers(self):
        res = []
        for record in self.partner_ids:
            res.append(record.name)

        res = sorted(set(res), key=res.index)

        return ', '.join(res)

    def products(self):
        res = []
        for record in self.product_ids:
            res.append(record.name)

        res = sorted(set(res), key=res.index)

        return ', '.join(res)

    def _get_description(self, description):

        if len(description) > 20:
            return description[:20]
        else:
            return description

    def print_report(self):
        return self.env.ref('barmex.barmex_sale_profit_report').report_action(self)


class CostEffectivenessLine(models.TransientModel):
    _name = "barmex.cost.effectiveness.line"
    _description = "Cost Effectiveness Line Report"

    header_id = fields.Many2one('barmex.cost.effectiveness')

    partner_id = fields.Many2one('res.partner',
                                 string="Customer")

    partner_num = fields.Char(string="Customer ID",
                              related="partner_id.barmex_id_cust")

    invoice_id = fields.Many2one('account.move',
                                 string="Invoice")

    date = fields.Date(string="Date")

    product_id = fields.Many2one('product.product',
                                 string="Product")

    description = fields.Char(string="Description")

    brand_id = fields.Many2one('barmex.product.brand',
                               string="Brand",
                               related="product_id.brand_id")

    qty = fields.Float(string="Quantity")

    currency_id = fields.Many2one('res.currency',
                                  string="Currency",
                                  default=lambda self: self.env.company.currency_id)

    sale_amount = fields.Monetary(string="Sale Amount")

    cost = fields.Monetary(string="Cost")

    profit = fields.Monetary(string="Profit")