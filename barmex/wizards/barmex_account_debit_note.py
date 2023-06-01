from odoo import models


class AccountDebitNote(models.TransientModel):
    _inherit = 'account.debit.note'

    def _prepare_default_values(self, move):
        values = super()._prepare_default_values(move)
        type_dn = {
            'in_invoice': 'in_debit_note',
            'out_invoice': 'out_debit_note'
        }
        move_type = values.get('type')
        debit_note = type_dn.get(move_type)
        l10n_mx_edi_origin = "02|{}".format(move.l10n_mx_edi_cfdi_uuid or "")
        values.update({
            debit_note: True,
            "invoice_date_due": values.get("invoice_date_due") or move.invoice_date_due,
            'l10n_mx_edi_origin': move.l10n_mx_edi_cfdi_uuid and l10n_mx_edi_origin or False
        })
        return values
