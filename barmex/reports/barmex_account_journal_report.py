import logging
from datetime import datetime, timedelta

from odoo import models, api, fields, _

_logger = logging.getLogger(__name__)

class JournalAccountReportHeader(models.TransientModel):
    _name = "barmex.account.journal.report.header"
    _description = "Barmex Account Journal Report"

    company_id = fields.Many2one('res.company')

    from_date = fields.Date()

    to_date = fields.Date()

    journal_ids = fields.Many2many('account.journal')

    move_id = fields.Many2one('account.move')

    currency_id = fields.Many2one('res.currency',
                                  default=lambda self: self.env.company.currency_id)

    day_ids = fields.One2many('barmex.account.journal.report.day',
                              'header_id')

    journals = fields.Integer()

    lines = fields.Integer()

    debit = fields.Monetary()

    credit = fields.Monetary()

    def create_report(self):
        if self.move_id:
            self.unique_move()

        self.create_days()
        self.get_journals()
        self.get_daily_total()

    def unique_move(self):
        move = self.env['account.move'].browse(self.move_id.id)

        self.from_date = move.date
        self.to_date = move.date

    def create_days(self):

        if not self.from_date:
            self.from_date = self.env['account.move'].search(
                [('state', '=', 'posted')], order='date asc', limit=1).date

        start_date = self.from_date

        while start_date <= self.to_date:
            self.day_ids = [(0, 0, {
                'date': start_date,
            })]

            start_date += timedelta(days=1)

    def get_journals(self):
        for day in self.day_ids:
            moves = None
            if self.move_id:
                id = self.move_id.id
                moves = self.env['account.move'].browse(id)

            else:
                domain = [('state', '=', 'posted'), ('date', '=', day.date)]

                if self.journal_ids:
                    domain.append(('journal_id', 'in', self.journal_ids.ids))

                moves = self.env['account.move'].search(domain, order='name,journal_id asc')

            for record in moves:
                related = self.env['account.move'].search(
                    [('l10n_mx_edi_origin', 'like', record.l10n_mx_edi_cfdi_uuid)])
                payments = self.env['account.payment'].search([('barmex_related_invoices', 'like', record.name)])

                day.update({
                    'journal_ids': [(0, 0, {
                        'move_id': record.id,
                        'currency_id': record.currency_id.id,
                        'debit': record.total_debit(),
                        'credit': record.total_credit(),
                        'lines': record.total_lines(),
                        'related_ids': related.ids,
                        'related_payments': payments.ids,
                    })]
                })

    def get_daily_total(self):
        total_debit = 0
        total_credit = 0
        total_journals = 0
        total_lines = 0
        for day in self.day_ids:
            debit = 0
            credit = 0
            count = 0
            lines = 0
            journals = []
            tags = []
            accounts = []
            for journal in day.journal_ids:
                debit += journal.debit
                credit += journal.credit
                lines += journal.lines
                count += 1
                journals.append(journal.move_id.journal_id.name)
                tags = tags + journal.get_tags()
                accounts = accounts + journal.get_account()

            journals = sorted(set(journals), key=journals.index)

            tags = sorted(set(tags), key=tags.index)
            if len(tags) > 0:
                tags = ', '.join(tags)
            else:
                tags = ''

            accounts = sorted(set(accounts), key=accounts.index)
            if len(accounts) > 0:
                accounts = ', '.join(accounts)
            else:
                accounts = ''

            day.update({
                'debit': debit,
                'credit': credit,
                'journals': count,
                'lines': lines,
                'names': ', '.join(journals),
                'tags': tags,
                'accounts': accounts,
            })

            total_debit += debit
            total_credit += credit
            total_journals += count
            total_lines += lines

        self.journals = total_journals
        self.lines = total_lines
        self.debit = total_debit
        self.credit = total_credit


class JournalAccountReportDay(models.TransientModel):
    _name = "barmex.account.journal.report.day"
    _description = "Barmex Account Journal Report"

    header_id = fields.Many2one('barmex.account.journal.report.header')

    journal_ids = fields.One2many('barmex.account.journal.report.line',
                                  'day_id')

    currency_id = fields.Many2one('res.currency',
                                  default=lambda self: self.env.company.currency_id)

    date = fields.Date()

    debit = fields.Monetary()

    credit = fields.Monetary()

    journals = fields.Integer()

    lines = fields.Integer()

    names = fields.Char()

    tags = fields.Char()

    accounts = fields.Char()


class JournalAccountReportLine(models.TransientModel):
    _name = "barmex.account.journal.report.line"
    _description = "Barmex Account Journal Report"

    day_id = fields.Many2one('barmex.account.journal.report.day')

    move_id = fields.Many2one('account.move')

    related_ids = fields.Many2many('account.move')

    related_payments = fields.Many2many('account.payment')

    debit = fields.Monetary()

    credit = fields.Monetary()

    currency_id = fields.Many2one('res.currency')

    lines = fields.Integer()

    def get_tags(self):
        tags = []
        for line in self.move_id.line_ids:
            for tag in line.analytic_tag_ids:
                tags.append(tag.name)

        return tags

    def get_account(self):
        account = []
        for line in self.move_id.line_ids:
            if line.analytic_account_id:
                account.append(line.analytic_account_id.display_name)
        return account

