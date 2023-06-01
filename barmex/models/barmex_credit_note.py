from odoo import api, models, fields, _
from odoo.exceptions import Warning

class CreditNote(models.TransientModel):
    _name = 'barmex.credit.note'
    _description = 'Credit note'

    name = fields.Char('Name')

    reason = fields.Many2one('barmex.reason',
                             string='Reason',
                             required=True)

    journal_id = fields.Many2one('account.journal',
                                 string='Journal')

    date = fields.Date(string='Date',
                       default=fields.Date.context_today)

    move_ids = fields.Char(string='IDs')

    def create_credit(self):
        moves = self.move_ids[:-1]
        moves = self.move_ids.split(',')
        partner = None
        product = self.env['product.template'].search([('is_discount', '=', True)], limit=1)
        lines = []
        uuid = '01|'
        journal = None

        for id in moves:
            if id.isnumeric():
                move = self.env['account.move'].search([('id', '=', id)])
                partner = move.partner_id
                lines.append((0, 0, {
                    'product_id': product.id,
                    'name': '{}-{}-{}'.format(product.name, move.name, move.date),
                    'quantity': 1,
                    'product_uom_id': product.uom_id.id,
                    'price_unit': move.discount_total,
                }))
                uuid += '{},'.format(move.l10n_mx_edi_cfdi_uuid)
        uuid = uuid[:-1]

        if self.journal_id:
            journal = self.journal_id
        else:
            journal = self.env['account.journal'].search([('type', '=', 'sale')], limit=1)

        credit = self.env['account.move'].create({
            'date': self.date,
            'invoice_date': self.date,
            'invoice_date_due': self.date,
            'journal_id': journal.id,
            'type': 'out_refund',
            'state': 'draft',
            'l10n_mx_edi_sat_status': 'undefined',
            'extract_state': 'no_extract_requested',
            'l10n_mx_edi_origin': uuid,
            'invoice_line_ids': lines,
            'company_id': self.env.company.id,
            'partner_id': partner.id,
            'barmex_reason': self.reason.id,
            'ref': self.reason.name,
        })

        form = self.env.ref('account.view_move_form', False).id

        return {
            'name': _('Credit note'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'res_id': credit.id,
            'view_id': form,
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'current'
        }