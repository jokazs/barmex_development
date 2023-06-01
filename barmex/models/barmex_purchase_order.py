from email.policy import default
from odoo import models, fields, api, _
from odoo.tools.float_utils import float_compare
from odoo.exceptions import Warning


class PurchReq(models.Model):
    _inherit = ['purchase.order']

    state = fields.Selection(
        selection_add=[
            ('pending', 'Pending approval'),
            ('offer', 'Offer validation'),
        ])

    purch_type = fields.Selection(
        [
            ('stock', 'Stock'),
            ('special', 'Special'),
            ('delivery', 'Delivery')
        ],
        required=True,
        string='Purchase type',
        default='delivery',
        readonly=True,
        states={
            'draft': [('readonly', False)]
        }
    )

    transfer = fields.Boolean(default=False)

    offer = fields.Boolean(string='Offer',
                           default=False)

    approved = fields.Boolean(string='Approved',
                              readonly=True,
                              copy=False,
                              states={
                                  'pending': [('readonly', False)],
                                  'offer': [('readonly', False)]})

    shipping_id = fields.Many2one('barmex.shipping')

    def action_barmex_move_products(self):
        print(self.id)
        ctx = dict(
            default_purchase_id = self.id
        )
        return {
            'context': ctx,
        }

    @api.constrains('transfer')
    def _transfer_validate(self):
        if self.transfer:
            for line in self.order_line:
                if not line.location_dest:
                    raise Warning(_("Missing destination for lines"))
        # else:
        #     for line in self.order_line:
        #         line.location_dest = False

    @api.onchange('purch_type')
    def _req_type(self):
        if self.purch_type == 'stock':
            self.transfer = True
        else:
            self.transfer = False

    # Update line prices on vendor change
    @api.onchange('partner_id')
    def _update_line_prices(self):
        for line in self.order_line:
            line.__class__._onchange_quantity(line)

    # Order validation
    def action_validate_order(self):
        info = self.validate_orderpoint()
        if self.state not in ('pending', 'offer'):
            info = self.validate_inventary()

        return info

    def approve_order(self):
        self.approved = True
        if self.approved:
            self.state = 'draft'
            self.button_confirm()

    # Resupply validation
    def validate_orderpoint(self):
        title = _("Alert!")
        info = None
        msj = ""
        for line in self.order_line:
            product = line.product_id

            if product.__class__._validate_offer(self, product, line.location_dest.id) == 1:
                msj = _("Article {} is marked as offer. To continue this order has to be approved.").format(
                    line.product_id.name)
                self.state = 'offer'
                self.offer = True

            elif product.__class__._validate_offer(self, product, line.location_dest.id) == 2:
                msj = _(
                    "Article {} is on a category marked as approbation. To continue this order has to be approved.").format(
                    line.product_id.name)
                self.state = 'pending'

        info = self.env['barmex.dialog.box'].display_dialog(title, msj, None, self.id)

        return info

    # Inventory acquisition dialog box
    def validate_inventary(self):
        title = _("Inventory alert")
        message = _("Do you want to confirm this order?")
        lines = []
        for line in self.order_line:
            tmp = line

            if line.product_id.qty_available_barmex > 0:
                for stock in line.product_id.stock_quant_ids:
                    if not stock.owner_id and stock.location_id.usage == 'internal':

                        if stock.quantity > 0:
                            # transform stock to reference uom

                            if stock.product_uom_id.uom_type == 'bigger':
                                on_hand = stock.product_uom_id.factor * stock.quantity
                            elif stock.product_uom_id.uom_type == 'smaller':
                                on_hand = stock.quantity / stock.product_uom_id.factor
                            else:
                                on_hand = stock.quantity

                            # transform stock to purchae uom
                            if line.product_uom.uom_type == 'smaller':
                                on_hand = on_hand * line.product_uom.factor
                            elif line.product_uom.uom_type == 'bigger':
                                on_hand = on_hand / line.product_uom.factor_inv

                            msg = _("There are {} {} of {} in {}.").format(on_hand, line.product_uom.name,
                                                                           line.product_id.name,
                                                                           stock.location_id.complete_name)

                            lines.append((0, 0, {'name': msg}))

                if line.product_qty > line.product_id.qty_available_barmex:
                    msg = ("It's recommended to acquire {} {}".format(
                        line.product_qty - line.product_id.qty_available_barmex,
                        line.product_uom.name))

                    lines.append((0, 0, {'name': msg}))

            else:
                msg = _("Non inventary existent of: {}").format(line.product_id.name)
                lines.append((0, 0, {'name': msg}))

        info = self.env['barmex.dialog.box'].display_dialog(title, message, lines, self.id)

        return info

    # Process purchase requisitions to purchase order
    def multi_req(self):
        requisitions = sorted(self, key=lambda x: x.partner_id.id)
        vend = requisitions[0]
        lines = []
        orig = ''

        for req in requisitions:
            if req.state in ['draft', 'sent', 'to approve']:
                if req.partner_id == vend.partner_id:
                    orig = '{} {} '.format(orig, req.name)

                if req.partner_id != vend.partner_id:
                    order = self.env['purchase.order']
                    purchase = order.create({
                        'partner_id': vend.partner_id.id,
                        'currency_id': vend.currency_id.id,
                        'state': 'purchase',
                        'picking_type_id': req.picking_type_id.id,
                        'date_approve': fields.datetime.now(),
                        'origin': orig,
                        'order_line': lines})
                    vend = req
                    orig = req.name
                    lines = []

                for line in req.order_line:
                    lines.append((0, 0, {
                        'product_id': line.product_id.id,
                        'name': line.name,
                        'date_planned': line.date_planned,
                        'product_qty': line.product_qty,
                        'price_unit': line.price_unit,
                        'product_uom': line.product_id.uom_id.id,
                        'account_analytic_id': line.account_analytic_id.id,
                        'location_dest': line.location_dest.id
                    }))

        if req.state in ['draft', 'sent', 'to approve']:
            order = self.env['purchase.order']
            purchase = order.create({
                'partner_id': vend.partner_id.id,
                'currency_id': vend.currency_id.id,
                'state': 'purchase',
                'picking_type_id': req.picking_type_id.id,
                'date_approve': fields.datetime.now(),
                'origin': orig,
                'order_line': lines})
    
    def _amount_to_words(self):
    
        currency = self.currency_id
        total = self.amount_total

        amount_i, amount_d = divmod(total, 1)
        amount_d = round(amount_d, 2)
        amount_d = int(round(amount_d * 100, 2))
        words = currency.with_context(lang='es_ES').amount_to_text(amount_i).upper()
        invoice_words = '%(words)s %(amount_d)02d/100 %(curr_t)s' % dict(
            words=words, amount_d=amount_d, curr_t=currency.name.upper())
        return invoice_words

    def purchase_amount_to_text(self):
        """Method to transform a float amount to text words
        E.g. 100 - ONE HUNDRED
        :returns: Amount transformed to words mexican format for invoices
        :rtype: str
        """
        self.ensure_one()
        currency = self.currency_id.name.upper()
        # M.N. = Moneda Nacional (National Currency)
        # M.E. = Moneda Extranjera (Foreign Currency)
        currency_type = 'M.N' if currency == 'MXN' else 'M.E.'
        # Split integer and decimal part
        amount_i, amount_d = divmod(self.amount_total, 1)
        amount_d = round(amount_d, 2)
        amount_d = int(round(amount_d * 100, 2))
        words = self.currency_id.with_context(lang=self.partner_id.lang or 'es_MX').amount_to_text(amount_i).upper()
        invoice_words = '%(words)s %(amount_d)02d/100 %(curr_t)s' % dict(
            words=words, amount_d=amount_d, curr_t=currency_type)
        return invoice_words