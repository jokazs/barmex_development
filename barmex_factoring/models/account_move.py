from odoo import fields, models, api
import datetime
import pytz
from dateutil import tz

class AccountMove(models.Model):
    _inherit = 'account.move'

    payment_factoring = fields.Float(string='Payment Factoring', currency_field='company_currency_id', copy=False)
    partial_payment = fields.Float(string='Partial Payment', currency_field='company_currency_id', copy=False)
    currency_rate = fields.Float(string='Currency rate', digits=(12, 6), default=0.000000, copy=False)
    currency_name = fields.Char(related='currency_id.name', string='Currency', copy=False)
    currency_rate_id = fields.Many2one('res.currency', string='Currency convert', copy=False)
    amount_currency_rate = fields.Float(string='Amount Currency Rate', copy=False)
    profit_loss = fields.Float('Profit or Loss', copy=False)
    balance = fields.Float('Balance', copy=False)
    to_pay = fields.Float('To pay', copy=False)
    balance_pay_mxn = fields.Float('Balance Pay MXN', copy=False)

    

    @api.onchange('to_pay')
    def onchange_to_pay(self):
        date = pytz.utc.localize(datetime.datetime.now()).astimezone(
            pytz.timezone('America/Mexico_City')).strftime("%Y-%m-%d")
        date_time = datetime.datetime.strptime(date, '%Y-%m-%d')
        if date_time and self.currency_id.name == 'MXN':
            currency_rate_id = self.env['res.currency.rate'].search(
                [('name', '=', date_time.date()), ('currency_id', '=', self.currency_rate_id.id)])
            if currency_rate_id.rate > 0:
                self.currency_rate = 1 / currency_rate_id.rate
        elif date_time and self.currency_id.name != 'MXN':
            currency_rate_id = self.env['res.currency.rate'].search(
                    [('name', '=', date_time.date()), ('currency_id', '=', self.currency_id.id)])
            if currency_rate_id.rate > 0:
                self.currency_rate = 1 / currency_rate_id.rate
        if self.barmex_currency_rate == 1:
            self.barmex_currency_rate = self.amount_total_signed / self.amount_total
        self.balance_pay_mxn = self.to_pay / (1/self.barmex_currency_rate)
        if self.currency_rate:
            self.amount_currency_rate = self.to_pay / (1/self.currency_rate)
            self.profit_loss = self.balance_pay_mxn - self.amount_currency_rate
        self.balance = self.amount_residual - self.to_pay

    @api.onchange('currency_rate_id')
    def onchange_currency_date_id(self):
        for invoice in self:
            date = pytz.utc.localize(datetime.datetime.now()).astimezone(
                pytz.timezone('America/Mexico_City')).strftime("%Y-%m-%d")
            date_time = datetime.datetime.strptime(date, '%Y-%m-%d')
            if date_time and invoice.currency_id.name == 'MXN':
                currency_rate_id = self.env['res.currency.rate'].search([('name', '=', date_time.date()), ('currency_id', '=', invoice.currency_rate_id.id)])
                invoice.currency_rate = currency_rate_id.rate
                invoice.amount_currency_rate = invoice.amount_total * currency_rate_id.rate
                invoice.profit_loss = invoice.amount_total_signed * self.env['res.currency.rate'].search([('name', '=', invoice.invoice_date), ('currency_id', '=', invoice.currency_rate_id.id)]).rate  - invoice.amount_currency_rate
            elif date_time and invoice.currency_id.name != 'MXN':
                currency_rate_id = self.env['res.currency.rate'].search(
                    [('name', '=', date_time.date()), ('currency_id', '=', invoice.currency_id.id)])
                invoice.currency_rate = currency_rate_id.rate
                invoice.amount_currency_rate = invoice.amount_total * currency_rate_id.rate
                invoice.profit_loss = invoice.amount_total_signed - invoice.amount_currency_rate * invoice.currency_rate

    def account_move_tax(self,ids):
        tax = self.env["account.tax"].search([('tax_group_id', '=', ids),('type_tax_use', '=', 'sale')], limit=1)        
        return tax
    def account_move_values(self,ids):
        account = self.env["account.move"].search([('id', '=', ids)], limit=1)        
        return account

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    to_pay = fields.Float(related='move_id.to_pay', string='A Pagar')

    def auto_reconcile_lines(self):
        # Create list of debit and list of credit move ordered by date-currency
        if self.filtered(lambda r: r.to_pay > 0) and self[0].name.split(':')[0] == 'Pago a proveedor':
            debit_moves = self.filtered(lambda r: r.debit > 0 or r.amount_currency > 0)
            credit_moves = self.filtered(lambda r: r.to_pay != 0 or r.amount_currency < 0)
            void_moves = self.filtered(lambda r: not r.credit and not r.debit and not r.amount_currency)
            debit_moves = debit_moves.sorted(key=lambda a: (a.date_maturity or a.date, a.currency_id))
            credit_moves = credit_moves.sorted(key=lambda a: (a.date_maturity or a.date, a.currency_id))
        elif self.filtered(lambda r: r.to_pay > 0) and self[0].name.split(':')[0] != 'Pago a proveedor':
            debit_moves = self.filtered(lambda r: r.debit > 0 or r.amount_currency > 0)
            credit_moves = self.filtered(lambda r: r.to_pay != 0 or r.amount_currency < 0)
            void_moves = self.filtered(lambda r: not r.credit and not r.debit and not r.amount_currency)
            debit_moves = debit_moves.sorted(key=lambda a: (a.date_maturity or a.date, a.currency_id))
            credit_moves = credit_moves.sorted(key=lambda a: (a.date_maturity or a.date, a.currency_id))
        else:
            debit_moves = self.filtered(lambda r: r.debit != 0 or r.amount_currency > 0)
            credit_moves = self.filtered(lambda r: r.credit != 0 or r.amount_currency < 0)
            void_moves = self.filtered(lambda r: not r.credit and not r.debit and not r.amount_currency)
            debit_moves = debit_moves.sorted(key=lambda a: (a.date_maturity or a.date, a.currency_id))
            credit_moves = credit_moves.sorted(key=lambda a: (a.date_maturity or a.date, a.currency_id))
        # Compute on which field reconciliation should be based upon:
        if self[0].account_id.currency_id and self[0].account_id.currency_id != self[0].account_id.company_id.currency_id:
            field = 'amount_residual_currency'
        else:
            field = 'amount_residual'
        #if all lines share the same currency, use amount_residual_currency to avoid currency rounding error
        if self[0].currency_id and all([x.amount_currency and x.currency_id == self[0].currency_id for x in self]):
            field = 'amount_residual_currency'
        # Reconcile lines
        if debit_moves:
            ret = self._reconcile_lines(debit_moves, void_moves + credit_moves, field)
        elif credit_moves:
            ret = self._reconcile_lines(void_moves + debit_moves, credit_moves, field)
        else:
            ret = self._reconcile_lines(void_moves[:len(void_moves) // 2], void_moves[len(void_moves) // 2:], field)
        return ret

    def _reconcile_lines(self, debit_moves, credit_moves, field):
        """ This function loops on the 2 recordsets given as parameter as long as it
            can find a debit and a credit to reconcile together. It returns the recordset of the
            account move lines that were not reconciled during the process.
        """
        (debit_moves + credit_moves).read([field])
        to_create = []
        cash_basis = debit_moves and debit_moves[0].account_id.internal_type in ('receivable', 'payable') or False
        cash_basis_percentage_before_rec = {}
        dc_vals ={}
        while (debit_moves and credit_moves):
            debit_move = debit_moves[0]
            credit_move = credit_moves[0]
            company_currency = debit_move.company_id.currency_id
            # We need those temporary value otherwise the computation might be wrong below
            if debit_move.to_pay > 0:

                credit_move['amount_residual'] = credit_move.to_pay * abs(
                            debit_move.amount_residual / debit_move.amount_currency) if credit_move.move_id.currency_id.name != 'MXN' else credit_move.to_pay
                debit_move['amount_residual'] = debit_move.to_pay * abs(
                            debit_move.amount_residual / debit_move.amount_currency) if debit_move.move_id.currency_id.name != 'MXN' else debit_move.to_pay
                debit_move['amount_residual_currency'] = debit_move.to_pay  if debit_move.move_id.currency_id.name != 'MXN' else 0.00
                temp_amount_residual = min(debit_move.amount_residual, -credit_move.amount_residual)
                temp_amount_residual_currency = min(debit_move.amount_residual_currency, -credit_move.amount_residual_currency)
                dc_vals[(debit_move.id, credit_move.id)] = (debit_move, credit_move, temp_amount_residual_currency)
                amount_reconcile = min(debit_move[field], -credit_move[field])
            if credit_move.to_pay > 0:

                credit_move['amount_residual'] = credit_move.to_pay * abs(
                            credit_move.amount_residual / credit_move.amount_currency) if credit_move.move_id.currency_id.name != 'MXN' else credit_move.to_pay * -1
                debit_move['amount_residual'] = debit_move.amount_residual * abs(
                            debit_move.amount_residual / debit_move.amount_currency) if debit_move.move_id.currency_id.name != 'MXN' else debit_move.amount_residual
                credit_move['amount_residual_currency'] = -credit_move.to_pay if credit_move.move_id.currency_id.name != 'MXN' else 0.00
                temp_amount_residual = min(debit_move.amount_residual, -credit_move.amount_residual)
                temp_amount_residual_currency = min(debit_move.amount_residual_currency , -credit_move.amount_residual_currency)
                dc_vals[(debit_move.id, credit_move.id)] = (debit_move, credit_move, temp_amount_residual_currency)
                amount_reconcile = min(debit_move[field], -credit_move[field])
            else:
                temp_amount_residual = min(debit_move.amount_residual, -credit_move.amount_residual)
                temp_amount_residual_currency = min(debit_move.amount_residual_currency,
                                                    -credit_move.amount_residual_currency)
                dc_vals[(debit_move.id, credit_move.id)] = (debit_move, credit_move, temp_amount_residual_currency)
                amount_reconcile = min(debit_move[field], -credit_move[field])
            #Remove from recordset the one(s) that will be totally reconciled
            # For optimization purpose, the creation of the partial_reconcile are done at the end,
            # therefore during the process of reconciling several move lines, there are actually no recompute performed by the orm
            # and thus the amount_residual are not recomputed, hence we have to do it manually.
            if amount_reconcile == debit_move[field]:
                debit_moves -= debit_move
            else:
                if debit_move.to_pay > 0:
                    debit_moves[0].amount_residual -= temp_amount_residual if debit_moves[0].move_id.currency_id.name != 'MXN' else temp_amount_residual
                    debit_moves[0].amount_residual_currency -= temp_amount_residual  if debit_moves[0].move_id.currency_id.name != 'MXN' else 0.00
                else:
                    debit_moves[0].amount_residual -= temp_amount_residual
                    debit_moves[0].amount_residual_currency -= temp_amount_residual_currency

            if amount_reconcile == -credit_move[field]:
                credit_moves -= credit_move
            else:
                credit_moves[0].amount_residual += temp_amount_residual
                credit_moves[0].amount_residual_currency += temp_amount_residual_currency
            #Check for the currency and amount_currency we can set
            currency = False
            amount_reconcile_currency = 0
            if field == 'amount_residual_currency':
                currency = credit_move.currency_id.id
                amount_reconcile_currency = temp_amount_residual_currency
                amount_reconcile = temp_amount_residual
            elif bool(debit_move.currency_id) != bool(credit_move.currency_id):
                # If only one of debit_move or credit_move has a secondary currency, also record the converted amount
                # in that secondary currency in the partial reconciliation. That allows the exchange difference entry
                # to be created, in case it is needed. It also allows to compute the amount residual in foreign currency.
                currency = debit_move.currency_id or credit_move.currency_id
                currency_date = debit_move.currency_id and credit_move.date or debit_move.date
                amount_reconcile_currency = company_currency._convert(amount_reconcile, currency, debit_move.company_id, currency_date)
                currency = currency.id

            if cash_basis:
                tmp_set = debit_move | credit_move
                cash_basis_percentage_before_rec.update(tmp_set._get_matched_percentage())

            to_create.append({
                'debit_move_id': debit_move.id,
                'credit_move_id': credit_move.id,
                'amount': amount_reconcile,
                'amount_currency': amount_reconcile_currency,
                'currency_id': currency,
            })

        cash_basis_subjected = []
        part_rec = self.env['account.partial.reconcile']
        for partial_rec_dict in to_create:
            debit_move, credit_move, amount_residual_currency = dc_vals[partial_rec_dict['debit_move_id'], partial_rec_dict['credit_move_id']]
            # /!\ NOTE: Exchange rate differences shouldn't create cash basis entries
            # i. e: we don't really receive/give money in a customer/provider fashion
            # Since those are not subjected to cash basis computation we process them first
            if not amount_residual_currency and debit_move.currency_id and credit_move.currency_id:
                part_rec.create(partial_rec_dict)
            else:
                cash_basis_subjected.append(partial_rec_dict)

        for after_rec_dict in cash_basis_subjected:
            new_rec = part_rec.create(after_rec_dict)
            # if the pair belongs to move being reverted, do not create CABA entry
            if cash_basis and not (
                    new_rec.debit_move_id.move_id == new_rec.credit_move_id.move_id.reversed_entry_id
                    or
                    new_rec.credit_move_id.move_id == new_rec.debit_move_id.move_id.reversed_entry_id
            ):
                new_rec.create_tax_cash_basis_entry(cash_basis_percentage_before_rec)
        return debit_moves+credit_moves


