from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class AccountAccount(models.Model):
    _inherit = 'account.account'

    factoraje = fields.Boolean('Factoring')

    @api.constrains('factoraje')
    def validation_factoraje(self):
        factoring = self.env['account.account'].search_count([('factoraje', '=', True)])
        if factoring > 1:
            raise ValidationError(_('There cannot be more than one account in the company with active factoring'))
