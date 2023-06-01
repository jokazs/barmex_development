from datetime import datetime, timedelta
from odoo import models, fields, _

class ResCompany(models.Model):
    _inherit = "res.company"

    def _end_last_month(self):
        today = datetime.now().date()

        last_day = today.replace(day=1) - timedelta(days=1)

        return last_day

    collection_lock_date = fields.Date(string='Collections Lock Date',
                                       default=_end_last_month)