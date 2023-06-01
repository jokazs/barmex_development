from odoo import models, api, fields, _
import logging

_logger = logging.getLogger(__name__)

class AccountJournalReport(models.AbstractModel):
    _name = "report.barmex.account_journal_report"
    _description = "Barmex Account Journal Report"

    @api.model
    def _get_report_values(self, docids, data=None):
        from_date = data['form']['from_date']
        to_date = data['form']['to_date']
        journals = data['form']['journal_ids']
        id = False
        if data['form']['move_id']:
            id = data['form']['move_id'][0]

        report = self.env['barmex.account.journal.report.header'].create({
            'from_date': from_date,
            'to_date': to_date,
            'company_id': self.env.company.id,
            'journal_ids': journals,
            'move_id': id,
        })

        report.create_report()

        return {
            'doc_model': 'barmex.account.journal.report.header',
            'docs': report,
        }
