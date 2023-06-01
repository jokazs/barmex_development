from odoo import models, api, fields, _
from odoo.tools.misc import format_date
from dateutil.relativedelta import relativedelta

class report_account_aged(models.AbstractModel):
    _inherit = ['account.aged.partner']

    def _get_columns_name(self, options):
        columns = [
            {},
            {'name': _("Purchase Order"), 'class': '', 'style': 'text-align:center; white-space:nowrap;'},
            {'name': _("Total"), 'class': 'number sortable', 'style': 'text-align:center; white-space:nowrap;'},
            {'name': _("Orig. currency"), 'class': '', 'style': 'text-align:center; white-space:nowrap;'},
            {'name': _("Tipo Cambio"), 'class': 'number sortable', 'style': 'text-align:center; white-space:nowrap;'},
            {'name': _("Fecha factura"), 'class': 'date', 'style': 'white-space:nowrap;'},
            {'name': _("Due Date"), 'class': 'date', 'style': 'white-space:nowrap;'},
            {'name': _("Real Payment Date"), 'class': 'date', 'style': 'white-space:nowrap;'},
            {'name': _("Journal"), 'class': '', 'style': 'text-align:center; white-space:nowrap;'},
            {'name': _("Account"), 'class': '', 'style': 'text-align:center; white-space:nowrap;'},
            {'name': _("Exp. Date"), 'class': 'date', 'style': 'white-space:nowrap;'},
            {'name': _("As of: %s") % format_date(self.env, options['date']['date_to']), 'class': 'number sortable',
             'style': 'white-space:nowrap;'},
            {'name': _("1 - 30"), 'class': 'number sortable', 'style': 'white-space:nowrap;'},
            {'name': _("31 - 60"), 'class': 'number sortable', 'style': 'white-space:nowrap;'},
            {'name': _("61 - 90"), 'class': 'number sortable', 'style': 'white-space:nowrap;'},
            {'name': _("91 - 120"), 'class': 'number sortable', 'style': 'white-space:nowrap;'},
            {'name': _("Older"), 'class': 'number sortable', 'style': 'white-space:nowrap;'},
            {'name': _("Total"), 'class': 'number sortable', 'style': 'white-space:nowrap;'},
        ]
        return columns

    @api.model
    def _get_lines(self, options, line_id=None):
        sign = -1.0 if self.env.context.get('aged_balance') else 1.0
        lines = []
        account_types = [self.env.context.get('account_type')]
        context = {'include_nullified_amount': True}
        suma0 = 0
        suma1 = 0
        suma2 = 0
        suma3 = 0
        suma4 = 0
        suma5 = 0
        suma6 = 0
        if line_id and 'partner_' in line_id:
            # we only want to fetch data about this partner because we are expanding a line
            partner_id_str = line_id.split('_')[1]
            if partner_id_str.isnumeric():
                partner_id = self.env['res.partner'].browse(int(partner_id_str))
            else:
                partner_id = False
            context.update(partner_ids=partner_id)
        results, total, amls = self.env['report.account.report_agedpartnerbalance'].with_context(
            **context)._get_partner_move_lines(account_types, self._context['date_to'], 'posted', 30)

        for values in results:
            if values['partner_id']:
                vals = {
                    'id': 'partner_%s' % (values['partner_id'],),
                    'name': '{} - {}'.format(values['name'], self.env['res.partner'].browse(values['partner_id']).vat),
                    'level': 2,
                    'columns': [{'name': ''}] * 10 + [{'name': self.format_value(sign * v), 'no_format': sign * v}
                                                    for v in [values['direction'], values['4'],
                                                            values['3'], values['2'],
                                                            values['1'], values['0'], values['total']]],
                    'trust': values['trust'],
                    'unfoldable': True,
                    'unfolded': 'partner_%s' % (values['partner_id'],) in options.get('unfolded_lines'),
                    'partner_id': values['partner_id'],
                }
                suma0 = suma0 + values['0']
                suma1 = suma1 + values['1']
                suma2 = suma2 + values['2']
                suma3 = suma3 + values['3']
                suma4 = suma4 + values['4']
                suma5 = suma5 + values['direction']
                suma6 = suma6 + values['total']
                lines.append(vals)
                if 'partner_%s' % (values['partner_id'],) in options.get('unfolded_lines'):
                    for line in amls[values['partner_id']]:
                        aml = line['line']
                        if aml.move_id.is_purchase_document():
                            caret_type = 'account.invoice.in'
                        elif aml.move_id.is_sale_document():
                            caret_type = 'account.invoice.out'
                        elif aml.payment_id:
                            caret_type = 'account.payment'
                        else:
                            caret_type = 'account.move'

                        line_date = aml.date_maturity or aml.date
                        if not self._context.get('no_format'):
                            line_date = format_date(self.env, line_date)
                        vals = {
                            'id': aml.id,
                            'name': aml.move_id.name,
                            'class': 'date',
                            'caret_options': caret_type,
                            'level': 4,
                            'parent_id': 'partner_%s' % (values['partner_id'],),
                            'columns': [{'name': v} for v in [aml.move_id.invoice_origin, aml.move_id.amount_total, aml.move_id.currency_id.name, aml.move_id.barmex_currency_rate,
                                                            format_date(self.env, aml.move_id.invoice_date),
                                                            format_date(self.env, aml.date_maturity or aml.date),
                                                            format_date(self.env, aml.payment_id.payment_date_lco),
                                                            aml.journal_id.code, aml.account_id.display_name,
                                                            format_date(self.env, aml.expected_pay_date)]] +
                                    [{'name': self.format_value(sign * v, blank_if_zero=True), 'no_format': sign * v} for
                                        v in [line['period'] == 6 - i and line['amount'] or 0 for i in range(7)]],
                            'action_context': {
                                'default_type': aml.move_id.type,
                                'default_journal_id': aml.move_id.journal_id.id,
                            },
                            'title_hover': self._format_aml_name(aml.name, aml.ref, aml.move_id.name),
                        }
                        lines.append(vals)
        if total and not line_id:
            total_line = {
                'id': 0,
                'name': _('Total'),
                'class': 'total',
                'level': 2,
                'columns': [{'name': ''}] * 10 + [{'name': self.format_value(sign * v), 'no_format': sign * v} for v in
                                                 [suma5, suma4, suma3, suma2, suma1, suma0,
                                                  suma6]],
            }
            lines.append(total_line)
        return lines