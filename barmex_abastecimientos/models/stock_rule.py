# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from collections import defaultdict
from dateutil.relativedelta import relativedelta
from itertools import groupby

from odoo import api, fields, models, _, SUPERUSER_ID
from odoo.exceptions import UserError

class StockRule(models.Model):
    _inherit = 'stock.rule'

    @api.model
    def _prepare_purchase_order_line(self, product_id, product_qty, product_uom, company_id, values, po):
        print("_prepare_purchase_order_line")

        res = super(StockRule, self)._prepare_purchase_order_line(product_id, product_qty, product_uom, company_id, values, po)
        print("_prepare_purchase_order_line")
        print(res)
        res['location_dest'] = po.picking_type_id.default_location_dest_id.id
        return res