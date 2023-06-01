from odoo import models, fields, api, _
from odoo.tools.float_utils import float_compare

class AccountMoveLine(models.Model):
    _inherit = ['account.move.line']

    discount_amount_lco = fields.Monetary('Discount amount')

    discount_percentage_lco = fields.Float('Discount percentage')

    lco_price_dist = fields.Float('Reseller price')

    lco_price_diff = fields.Float(compute='lco_calc_diff',
                                  string='Difference',
                                  default=0)

    line_type = fields.Selection(related='move_id.type',
                                 store=True,
                                 readonly=True)

    real_date = fields.Date(compute='_real_date',
                            store=True)

    stock_move_id = fields.Many2one('stock.picking')

    @api.depends('date')
    def _real_date(self):
        for record in self:
            record.update({
                'real_date': record.payment_id.payment_date_lco,
            })
            if record.real_date:
                record.update({
                    'date_maturity': record.real_date,
                })

    @api.depends('price_unit', 'lco_price_dist')
    def lco_calc_diff(self):
        for line in self:
            if line.line_type == 'out_invoice' and line.lco_price_dist > 0:
                line.update({
                    'lco_price_diff': line.price_unit - line.lco_price_dist
                })
            else:
                line.update({
                    'lco_price_diff': 0
                })

    def _calculate_discount(self, subtotal):
        discount = 0

        if self.discount_amount_lco != 0:
            discount = self.discount_amount_lco
        elif self.discount_percentage_lco != 0:
            discount = (subtotal * self.discount_percentage_lco) / 100
        return discount

    @api.model
    def _get_price_total_and_subtotal_model(self, price_unit, quantity, discount, currency, product, partner, taxes,
                                            move_type):
        ''' This method is used to compute 'price_total' & 'price_subtotal'.

        :param price_unit:  The current price unit.
        :param quantity:    The current quantity.
        :param discount:    The current discount.
        :param currency:    The line's currency.
        :param product:     The line's product.
        :param partner:     The line's partner.
        :param taxes:       The applied taxes.
        :param move_type:   The type of the move.
        :return:            A dictionary containing 'price_subtotal' & 'price_total'.
        '''
        res = {}

        # Compute 'price_subtotal'.
        price_unit_wo_discount = price_unit * (1 - (discount / 100.0))
        subtotal = quantity * price_unit_wo_discount
        discount = self._calculate_discount(subtotal)

        # Compute 'price_total'.
        if taxes:
            force_sign = -1 if move_type in ('out_invoice', 'in_refund', 'out_receipt') else 1
            taxes_res = taxes._origin.with_context(force_sign=force_sign).compute_all(price_unit_wo_discount,
                                                                                      quantity=quantity,
                                                                                      currency=currency,
                                                                                      product=product, partner=partner,
                                                                                      is_refund=move_type in (
                                                                                          'out_refund', 'in_refund'))
            res['price_subtotal'] = taxes_res['total_excluded'] - discount
            res['price_total'] = taxes_res['total_included'] - discount
        else:
            res['price_total'] = res['price_subtotal'] = subtotal - discount
        # In case of multi currency, round before it's use for computing debit credit
        if currency:
            res = {k: currency.round(v) for k, v in res.items()}
        return res

    def get_credit_message(self, date):
        ret = ''

        currency_id = self.currency_id if self.currency_id else self.company_currency_id
        amount = currency_id._convert(self.debit, self.partner_id.credit_currency, self.env.company, date)

        if self.partner_id and not self.partner_id.exceed_limit:
            if self.partner_id.open_account_exceeded:
                ret = _('{} accounting credit limit exceeded.\n'.format(self.partner_id.name))

            elif self.partner_id.open_account_risk + amount > self.partner_id.open_account_amount and self.partner_id.open_account_include:
                ret = _(
                    '{} accounting credit limit will be exceeded with this document.\n'.format(self.partner_id.name))

            elif self.partner_id.general_limit < self.partner_id.total_risk + amount:
                ret = _('{} credit limit will be exceeded with this document.\n'.format(self.partner_id.name))

            elif self.partner_id.credit_exceeded:
                ret = _('{} credit limit exceeded.\n'.format(self.partner_id.name))

            elif self.partner_id.due_invoice_lock and self.partner_id.locked_by_due:
                ret = _('{} has due invoices.\n'.format(self.partner_id.name))

        return ret