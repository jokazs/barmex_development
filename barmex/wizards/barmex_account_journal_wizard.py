import logging

from odoo import models, api, fields, _
from odoo.exceptions import Warning

_logger = logging.getLogger(__name__)


class JournalAccountReportWizard(models.TransientModel):
    _name = "barmex.account.journal.report"
    _description = "Barmex Account Journal Report"

    from_date = fields.Date(string='From Date')

    to_date = fields.Date(string='To Date',
                          default=fields.Date.context_today,
                          required=True)

    journal_ids = fields.Many2many('account.journal',
                                   string='Journal')

    move_id = fields.Many2one('account.move',
                              string="Account Move")

    def get_report(self):
        data = {
            'model': 'barmex.account.journal.report',
            'form': self.read()[0],
        }

        journals = None

        if self.move_id:
            journals = self.env['account.move'].browse(self.move_id.id)

        else:
            domain = [('state', '=', 'posted'), ('date', '<=', self.to_date)]

            if self.from_date:
                domain.append(('date', '>=', self.from_date))

            if self.journal_ids:
                domain.append(('journal_id', 'in', self.journal_ids.ids))

            journals = self.env['account.move'].search(domain)

        if journals:
            return self.env.ref('barmex.barmex_account_journal_report').report_action(self, data=data)

        else:
            raise Warning(_('No Records can be printed'))