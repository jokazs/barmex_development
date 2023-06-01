from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo import models, fields, api, _
from odoo.tools.float_utils import float_compare

class PurchLine(models.Model):
    _inherit = ['purchase.order.line']

    attachment = fields.Binary(string='Attachment',
                               store=True,
                               attachment=True)

    file_name = fields.Char(string="File Name")

    transfer = fields.Boolean('Transfer', related='order_id.transfer', store=True, readonly=True)

    location_dest = fields.Many2one('stock.location',
                                    string='Destination')

    discount_amount_lco = fields.Monetary('Discount amount')

    discount_percentage_lco = fields.Float('Discount percentage')

    offer = fields.Boolean('Offer',
                           compute='is_offer')

    @api.onchange('product_qty', 'product_uom')
    def _onchange_quantity(self):
        if not self.product_id:
            return
        params = {'order_id': self.order_id}
        seller = self.product_id._select_seller(
            partner_id=self.partner_id,
            quantity=self.product_qty,
            date=self.order_id.date_order and self.order_id.date_order.date(),
            uom_id=self.product_uom,
            params=params)

        if seller or not self.date_planned:
            self.date_planned = self._get_date_planned(seller).strftime(DEFAULT_SERVER_DATETIME_FORMAT)

        if not seller:
            if self.product_id.seller_ids.filtered(lambda s: s.name.id == self.partner_id.id):
                self.price_unit = 0.0
            return

        price_unit = self.env['account.tax']._fix_tax_included_price_company(seller.price,
                                                                             self.product_id.supplier_taxes_id,
                                                                             self.taxes_id,
                                                                             self.company_id) if seller else 0.0
        if price_unit and seller and self.order_id.currency_id and seller.currency_id != self.order_id.currency_id:
            price_unit = seller.currency_id._convert(
                price_unit, self.order_id.currency_id, self.order_id.company_id, self.date_order or fields.Date.today())

        if seller and self.product_uom and seller.product_uom != self.product_uom:
            price_unit = seller.product_uom._compute_price(price_unit, self.product_uom)

        product = self.env['barmex.vendor.price'].search(
            [('product_id', '=', self.product_id.id), ('vendor_id', '=', self.partner_id.id)])
        if product:
            price_unit = product.price
        self.price_unit = price_unit

    @api.depends('product_id')
    def is_offer(self):
        for record in self:
            record.update({
                'offer': record.product_id.offer,
            })

    @api.onchange('discount_percentage_lco')
    def _discount_percentage(self):
        if self.discount_amount_lco > 0 and self.discount_percentage_lco > 0:
            self.discount_amount_lco = 0

    @api.onchange('discount_amount_lco')
    def _discount_amount(self):
        if self.discount_amount_lco > 0 and self.discount_percentage_lco > 0:
            self.discount_percentage_lco = 0

    @api.depends('product_qty', 'price_unit', 'taxes_id', 'discount_amount_lco', 'discount_percentage_lco')
    def _compute_amount(self):
        for line in self:
            vals = line._prepare_compute_all_values()
            taxes = line.taxes_id.compute_all(
                vals['price_unit'],
                vals['currency_id'],
                vals['product_qty'],
                vals['product'],
                vals['partner'])
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })

            if line.discount_amount_lco > 0:
                line.price_subtotal -= line.discount_amount_lco
                line.price_total -= line.discount_amount_lco
            elif line.discount_percentage_lco > 0:
                discount = (line.price_subtotal * line.discount_percentage_lco) / 100
                line.price_subtotal -= discount
                line.price_total -= discount

    def _prepare_account_move_line(self, move):
        self.ensure_one()

        if self.product_id.purchase_method == 'purchase':
            qty = self.product_qty - self.qty_invoiced
        else:
            qty = self.qty_received - self.qty_invoiced
        if float_compare(qty, 0.0, precision_rounding=self.product_uom.rounding) <= 0:
            qty = 0.0

        return {
            'name': '%s: %s' % (self.order_id.name, self.name),
            'move_id': move.id,
            'currency_id': move.currency_id.id,
            'purchase_line_id': self.id,
            'date_maturity': move.invoice_date_due,
            'product_uom_id': self.product_uom.id,
            'product_id': self.product_id.id,
            'price_unit': self.price_unit,
            'quantity': qty,
            'partner_id': move.commercial_partner_id.id,
            'analytic_account_id': self.account_analytic_id.id,
            'analytic_tag_ids': [(6, 0, self.analytic_tag_ids.ids)],
            'tax_ids': [(6, 0, self.taxes_id.ids)],
            'display_type': self.display_type,
            'discount_percentage_lco': self.discount_percentage_lco,
            'discount_amount_lco': self.discount_amount_lco,
        }

    def _prepare_stock_moves(self, picking):
        """ Prepare the stock moves data for one order line. This function returns a list of
        dictionary ready to be used in stock.move's create()
        """
        self.ensure_one()
        res = []
        if self.product_id.type not in ['product', 'consu']:
            return res
        qty = 0.0
        price_unit = self._get_stock_move_price_unit()
        outgoing_moves, incoming_moves = self._get_outgoing_incoming_moves()
        for move in outgoing_moves:
            qty -= move.product_uom._compute_quantity(move.product_uom_qty, self.product_uom, rounding_method='HALF-UP')
        for move in incoming_moves:
            qty += move.product_uom._compute_quantity(move.product_uom_qty, self.product_uom, rounding_method='HALF-UP')
        description_picking = self.product_id.with_context(
            lang=self.order_id.dest_address_id.lang or self.env.user.lang)._get_description(
            self.order_id.picking_type_id)

        template = {
            'name': (self.name or '')[:2000],
            'product_id': self.product_id.id,
            'product_uom': self.product_uom.id,
            'date': self.order_id.date_order,
            'date_expected': self.date_planned,
            'location_id': self.order_id.partner_id.property_stock_supplier.id,
            'location_dest_id': self.order_id._get_destination_location(),
            'picking_id': picking.id,
            'partner_id': self.order_id.dest_address_id.id,
            'move_dest_ids': [(4, x) for x in self.move_dest_ids.ids],
            'state': 'draft',
            'purchase_line_id': self.id,
            'company_id': self.order_id.company_id.id,
            'price_unit': self.price_unit,
            'picking_type_id': self.order_id.picking_type_id.id,
            'group_id': self.order_id.group_id.id,
            'origin': self.order_id.name,
            'propagate_date': self.propagate_date,
            'propagate_date_minimum_delta': self.propagate_date_minimum_delta,
            'description_picking': description_picking,
            'propagate_cancel': self.propagate_cancel,
            'route_ids': self.order_id.picking_type_id.warehouse_id and [
                (6, 0, [x.id for x in self.order_id.picking_type_id.warehouse_id.route_ids])] or [],
            'warehouse_id': self.order_id.picking_type_id.warehouse_id.id,
            'transfer_to': self.location_dest.id,
            'last_price': self.price_unit,
            'last_currency': self.currency_id.id,
        }
        diff_quantity = self.product_qty - qty
        if float_compare(diff_quantity, 0.0, precision_rounding=self.product_uom.rounding) > 0:
            po_line_uom = self.product_uom
            quant_uom = self.product_id.uom_id
            product_uom_qty, product_uom = po_line_uom._adjust_uom_quantities(diff_quantity, quant_uom)
            template['product_uom_qty'] = product_uom_qty
            template['product_uom'] = product_uom.id
            res.append(template)
        return res