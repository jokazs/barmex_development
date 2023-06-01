from odoo import models, fields, _
from odoo.exceptions import UserError

class AccountChangeLockDate(models.TransientModel):
    _inherit = ['account.change.lock.date']

    def _collection_date(self):
        try:
            return self.env.company.collection_lock_date
        except:
            return False

    collection_lock_date = fields.Date(string='Collections Lock Date',
                                       default=_collection_date)

    def change_lock_date(self):
        if self.user_has_groups('account.group_account_manager'):
            self.env.company.sudo().write({
                'period_lock_date': self.period_lock_date,
                'fiscalyear_lock_date': self.fiscalyear_lock_date,
                'tax_lock_date': self.tax_lock_date,
                'collection_lock_date': self.collection_lock_date,
            })
        else:
            raise UserError(_('Only Billing Administrators are allowed to change lock dates!'))
        return {'type': 'ir.actions.act_window_close'}