from odoo import fields, models, _

class ZonaVentas(models.Model):
    _name = 'barmex.sale.zone'
    _description = 'Sale zone'
    _check_company_auto = True

    def journal_default(self):
        journal = self.env['account.journal'].search([('type', '=', 'sale')], limit=1)
        return journal.id

    name = fields.Char('Sale zone')

    active = fields.Boolean('Active',
                            default=True)

    journal_id = fields.Many2one('account.journal',
                                 default=journal_default,
                                 required=True,
                                 check_company=True,
                                 domain="[('type','=','sale')]")

    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.company)