from datetime import datetime, timedelta
from odoo import models, fields, api, _

class Product(models.Model):
    _inherit = ['product.product']

    sale_offer = fields.Boolean(string='Sale Offer')

    offer = fields.Boolean(string='Offer')

    last_currency = fields.Many2one('res.currency',
                                    string='Last purchase currency')

    last_price = fields.Monetary(string='Last purchase price',
                                 currency_field='last_currency')

    product_classification = fields.One2many('barmex.product.classification',
                                             'product_id')

    customer_reference = fields.One2many('barmex.customer.codes',
                                         'product_id',
                                         string="Customer reference")

    group_id = fields.Many2one('barmex.product.group')

    subgroup_id = fields.Many2one('barmex.product.subgroup')

    brand_id = fields.Many2one('barmex.product.brand')

    speciallity_id = fields.Many2one('barmex.product.speciallity')

    subline_id = fields.Many2one('barmex.product.subline')

    to_deliver = fields.Float(string='To deliver',
                              compute='_to_deliver')

    qty_available_barmex = fields.Float(string='Available',
                                        compute='available_barmex')

    # @api.onchange('brand_id')
    # def _set_brand(self):
    #     self.categ_id = self.brand_id.category_id.id

    def classification(self):
        cr = self.env.cr

        today = datetime.now().date() - timedelta(days=1)

        query = """(SELECT DISTINCT product_id FROM stock_move WHERE date::date = '{}')""".format(today)

        cr.execute(query)

        moves = cr.dictfetchall()

        product_ids = [move['product_id'] for move in moves]

        for product in product_ids:
            self.env['product.product'].search(product).set_classification()

    def set_classification(self):
        for record in self:
            if record.type == 'product':
                locations = self.env['stock.location'].search([('usage', '=', 'internal')])
                for location in locations:
                    classification = self.env['barmex.product.classification'].search(
                        [('product_id', '=', record.id), ('location_id', '=', location.id)], limit=1)

                    if not classification:
                        classification = self.env['barmex.product.classification'].create({
                            'product_id': record.id,
                            'location_id': location.id,
                            'template_id': record.product_tmpl_id.id,
                        })

                    classification.__class__.initial_cost(classification)
                    classification.__class__.get_sales(classification)
                    classification.__class__.get_purchases(classification)
                    classification.__class__.get_final(classification)
                    classification.__class__.get_cost(classification)
                    classification.__class__.get_average(classification)
                    classification.__class__.get_factor(classification)
                    classification.__class__.update_classification(classification)

    def _validate_offer(self, product, location):
        if location:
            classifications = self.env['barmex.product.classification'].search(
                [('product_id', '=', product.id), ('location_id', '=', location)])
        else:
            classifications = self.env['barmex.product.classification'].search(
                [('product_id', '=', product.id)])

        if product.offer:
            return 1

        elif classifications:
            for classification in classifications:
                if classification.classification_id.approbation:
                    return 2

    def _to_deliver(self):

        deliver_id = self.env['stock.picking.type'].search([('code', '=', 'outgoing')], limit=1)

        orders = self.env['stock.picking'].search([('picking_type_id', '=', deliver_id.id), ('state', '=', 'assigned')])

        for record in self:
            count = 0.0

            for order in orders:

                moves = self.env['stock.move.line'].search(
                    [('product_id', '=', record.id), ('picking_id', '=', order.id)])

                for move in moves:
                    count += move.product_uom_qty

            record.update({
                'to_deliver': count
            })

    def available_barmex(self):
        for record in self:
            record.update({
                'qty_available_barmex': record.qty_available - record.to_deliver
            })