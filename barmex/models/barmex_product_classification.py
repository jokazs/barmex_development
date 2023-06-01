from odoo import models, fields, api, _
from datetime import datetime, date, timedelta

class Classification(models.Model):
    _name = 'barmex.product.classification'
    _description = 'Product classification'
    _order = 'id desc'
    _check_company_auto = True

    product_id = fields.Many2one('product.product')

    template_id = fields.Many2one('product.template')

    classification_id = fields.Many2one('barmex.classification',
                                        default=lambda self: self.default_classification())

    classification_date = fields.Date(string='Classification date',
                                      default=fields.Datetime.now)

    days = fields.Integer(string='Days',
                          default=0)

    location_id = fields.Many2one('stock.location')

    initial = fields.Float(default=0)

    purchases = fields.Float(default=0)

    sales = fields.Float(default=0)

    final = fields.Float(default=0)

    cost = fields.Float(default=0)

    factor = fields.Float(default=0)

    average = fields.Float(default=0)

    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.company)

    def default_classification(self):
        classification = self.env['barmex.classification'].search([('default', '=', True)], limit=1)
        return classification.id

    def initial_cost(self):
        available = self.env['stock.quant'].search(
            [('product_id', '=', self.product_id.id), ('location_id', '=', self.location_id.id)], limit=1)

        if available:
            self.initial = available.quantity * self.product_id.standard_price
        else:
            self.initial = 0

    def get_sales(self):
        cr = self.env.cr

        today = datetime.now().date() - timedelta(days=1)

        query = """(SELECT id FROM stock_move WHERE date::date = '{}' and location_id = {} and product_id = {})""".format(
            today, self.location_id.id, self.product_id.id)

        cr.execute(query)

        moves = cr.dictfetchall()

        moves_ids = [move['id'] for move in moves]

        moves = self.env['stock.move'].browse(moves_ids)

        for sale in moves:
            self.sales += (sale.product_uom_qty * self.product_id.standard_price)

    def get_purchases(self):
        cr = self.env.cr

        today = datetime.now().date() - timedelta(days=1)

        query = """(SELECT id FROM stock_move WHERE date::date = '{}' and location_dest_id = {} and product_id = {})""".format(
            today, self.location_id.id, self.product_id.id)

        cr.execute(query)

        moves = cr.dictfetchall()

        moves_ids = [move['id'] for move in moves]

        moves = self.env['stock.move'].browse(moves_ids)

        for purchase in moves:
            self.purchases += (purchase.product_uom_qty * self.product_id.standard_price)

    def get_final(self):
        self.final = self.initial + self.purchases - self.sales

    def get_cost(self):
        self.cost = self.initial + self.purchases - self.final

    def get_average(self):
        try:
            self.average = (self.average + self.final) / 2
        except:
            0

    def get_factor(self):
        try:
            self.factor = self.cost / self.average
        except:
            0

    def update_classification(self):
        today = datetime.now().date()
        self.days = (today - self.classification_date).days

        if self.can_update():
            classification = self.env['barmex.classification'].search(
                [('min_factor', '<=', self.factor), ('max_factor', '>=', self.factor)], limit=1)

            if classification.id == self.classification_id.id:
                self.no_movement()
            else:
                self.classification_id = classification.id
                self.classification_date = datetime.today()
                self.days = 0

    def can_update(self):
        ret = False
        if self.classification_id.default:
            if self.days >= self.classification_id.days:
                ret = True
        else:
            ret = True

        return ret

    def no_movement(self):
        if self.days > self.classification_id.days:
            classification = None
            if self.classification_id.classification == 'A':
                classification = self.env['barmex.classification'].search([('classification', '=', 'B')], limit=1)
            elif self.classification_id.classification == 'B':
                classification = self.env['barmex.classification'].search([('classification', '=', 'C')], limit=1)
            elif self.classification_id.classification == 'C':
                classification = self.env['barmex.classification'].search([('classification', '=', 'D')], limit=1)
            elif self.classification_id.classification == 'D':
                classification = self.env['barmex.classification'].search([('classification', '=', 'E')], limit=1)
            elif self.classification_id.classification == 'E':
                classification = self.env['barmex.classification'].search([('classification', '=', 'F')], limit=1)
            elif self.classification_id.classification == 'F':
                classification = self.env['barmex.classification'].search([('classification', '=', 'G')], limit=1)
                self.classification_id = classification.id