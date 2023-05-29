from odoo import models, fields, api

class accountBankStatement(models.Model):
    _inherit = 'account.move'

    st_name= fields.Char('Calle', related='partner_id.street_name', store=True)
    st_number= fields.Char('Numero', related='partner_id.street_number', store=True)
    st_number2= fields.Char('Numero2', related='partner_id.street_number2', store=True)
    colony_ac= fields.Char('Colonia', related='partner_id.l10n_mx_edi_colony', store=True)
    city_ac= fields.Char('Ciudad', related='partner_id.city', store=True)
    # cityid_ac= fields.Char('Ciudad id', related='partner_id.city_id', store=True)
    stateid_ac= fields.Char('Estado', related='partner_id.state_id.name', store=True)
    zip_ac= fields.Char('CP', related='partner_id.zip', store=True)
    country_ac= fields.Char('País', related='partner_id.country_id.name', store=True)

    @api.depends('debit', 'credit', 'account_id', 'amount_currency', 'currency_id', 'matched_debit_ids', 'matched_credit_ids', 'matched_debit_ids.amount', 'matched_credit_ids.amount', 'move_id.state', 'company_id')
    def _amount_residual(self):
        #FIX de decimales en aplicacion de pagos que dejan saldos a favor de centavos y no sale el complemento de pago.
        super(accountBankStatement, self)._amount_residual()
        for line in self:
            if line.line_type == 'out_invoice' and line.amount_residual < 0:
                line.amount_residual = 0