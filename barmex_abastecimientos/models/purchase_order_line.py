# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from markupsafe import Markup
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.exceptions import UserError

from odoo.addons.purchase.models.purchase import PurchaseOrder as Purchase
import logging
_logger = logging.getLogger(__name__)

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.model
    def _prepare_purchase_order_line_from_procurement(self, product_id, product_qty, product_uom, company_id, values, po):
        print("_prepare_purchase_order_line_from_procurement")
        # line_description = ''
        # if values.get('product_description_variants'):
        #     line_description = values['product_description_variants']
        # supplier = values.get('supplier')
        # res = self._prepare_purchase_order_line(product_id, product_qty, product_uom, company_id, supplier, po)
        # # We need to keep the vendor name set in _prepare_purchase_order_line. To avoid redundancy
        # # in the line name, we add the line_description only if different from the product name.
        # # This way, we shoud not lose any valuable information.
        # if line_description and product_id.name != line_description:
        #     res['name'] += '\n' + line_description
        # res['date_planned'] = values.get('date_planned')
        # res['move_dest_ids'] = [(4, x.id) for x in values.get('move_dest_ids', [])]
        # res['orderpoint_id'] = values.get('orderpoint_id', False) and values.get('orderpoint_id').id
        # res['propagate_cancel'] = values.get('propagate_cancel')
        # res['product_description_variants'] = values.get('product_description_variants')
        res = super(SaleOrderLine, self)._prepare_purchase_order_line_from_procurement(product_id, product_qty, product_uom, company_id, values, po)
        _logger.info("_prepare_purchase_order_line_from_procurement")
        _logger.info(res)
        res['location_dest'] = po.warehouse_id.lot_stock_id
        return res