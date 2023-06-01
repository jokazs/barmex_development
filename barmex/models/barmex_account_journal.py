from odoo import _, models, fields, api
from odoo.exceptions import ValidationError

class AccountJournal(models.Model):
    _inherit = "account.journal"

    debit_sequence = fields.Boolean(
        "Dedicated debit sequence")
    debit_sequence_id = fields.Many2one(
        'ir.sequence', string='Debit note entry sequence', copy=False)
    debit_sequence_number_next = fields.Integer(
        string='Debit Notes: Next Number',
        help=('The next sequence number will'
              ' be used for the next debit note.'),
        compute='_compute_debit_seq_number_next',
        inverse='_inverse_debit_seq_number_next')

    @api.depends(
        'debit_sequence_id.use_date_range',
        'debit_sequence_id.number_next_actual')
    def _compute_debit_seq_number_next(self):
        '''Compute 'sequence_number_next' according to
        the current sequence in use,
        an ir.sequence or an ir.sequence.date_range.
        '''
        for journal in self:
            if journal.debit_sequence_id and journal.debit_sequence:
                sequence = journal.debit_sequence_id._get_current_sequence()
                journal.debit_sequence_number_next = sequence.number_next_actual
            else:
                journal.debit_sequence_number_next = 1

    def _inverse_debit_seq_number_next(self):
        '''Inverse 'debit_sequence_number_next' to edit
        the current sequence next number.
        '''
        for journal in self:
            if journal.debit_sequence_id and journal.debit_sequence and journal.debit_sequence_number_next:
                sequence = journal.debit_sequence_id._get_current_sequence()
                sequence.number_next = journal.debit_sequence_number_next

    @api.model
    def create(self, vals):
        use_debit_secuence = (
            vals.get('type') in ('sale', 'purchase') and
            vals.get('debit_sequence') and
            not vals.get('debit_sequence_id'))
        if use_debit_secuence:
            vals.update({
                'debit_sequence_id': self.sudo()._create_sequence_debit(vals).id
            })
        return super().create(vals)

    def write(self, vals):
        res = super().write(vals)
        for rec in self:
            if ('code' in vals and rec.code != vals['code']):
                if rec.debit_sequence_id:
                    new_prefix = self._get_sequence_prefix_debit(
                        vals['code'])
                    rec.debit_sequence_id.write(
                        {'prefix': new_prefix})
            if not vals.get('debit_sequence'):
                continue
            journal_allow = self.filtered(
                lambda j: j.type in ('sale', 'purchase')
                and not j.debit_sequence_id)
            for journal in journal_allow:
                journal_vals = {
                    'name': journal.name,
                    'company_id': journal.company_id.id,
                    'code': journal.code,
                    'debit_sequence_number_next': vals.get(
                        'debit_sequence_number_next',
                        journal.debit_sequence_number_next),
                }
                seq = self.sudo()._create_sequence_debit(journal_vals)
                journal.debit_sequence_id = seq.id
        return res

    @api.model
    def _get_sequence_prefix_debit(self, code):
        prefix = code.upper()
        prefix = 'ND-' + prefix
        return prefix + '/%(range_year)s/'

    @api.model
    def _create_sequence_debit(self, vals):
        """ Create new no_gap entry sequence for every new Journal"""
        prefix = self._get_sequence_prefix_debit(vals['code'])
        seq = {
            'name': vals['name'] + _(': Debit'),
            'implementation': 'no_gap',
            'prefix': prefix,
            'padding': 5,
            'number_increment': 1,
            'use_date_range': True,
        }
        if 'company_id' in vals:
            seq['company_id'] = vals['company_id']
        seq = self.env['ir.sequence'].create(seq)
        seq_date_range = seq._get_current_sequence()
        seq_date_range.number_next = vals.get(
            'debit_sequence_number_next') or 1
        return seq
