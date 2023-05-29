from datetime import datetime
from unittest import result
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.tools.misc import formatLang, get_lang
from odoo.exceptions import ValidationError, Warning
from odoo.tools.misc import clean_context
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare, float_round, float_is_zero
from odoo.exceptions import UserError
from collections import namedtuple, OrderedDict, defaultdict
from itertools import groupby


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    abastecimiento_compra = fields.Boolean(string='¿Compra?', help='Producto debe surtirse a través de una compra a proveedor')

    def _prepare_run_values_compra(self):
        replenishment = self.env['procurement.group'].create({'name': self.order_id.name})

        values = {
            'warehouse_id': self.order_id.warehouse_id or False,
            'route_ids':  self.route_id,
            'date_planned': self.order_id.date_order,
            'group_id': replenishment,
            'location_dest': self.order_id.warehouse_id.lot_stock_id or False,
            'propagate_date': self.order_id.date_order,
        }
        return values


    def _action_launch_stock_rule(self, previous_product_uom_qty=False):
        for line in self:
            if line.abastecimiento_compra:
                try:
                    resul = self.env['product.product'].search([('id','=',line.product_id.id)]).with_context(location=line.order_id.warehouse_id.lot_stock_id.id)
                    self.env['procurement.group'].with_context(clean_context(self.env.context)).run([
                        self.env['procurement.group'].Procurement(
                            line.product_id,
                            line.product_uom_qty - resul.qty_available, #OBTENER ESTE NUMERO
                            line.product_uom,
                            line.order_id.warehouse_id.lot_stock_id,  # Location
                            _(f"{line.order_id.name} compra por stock"),  # Name
                            _(f"{line.order_id.name} compra por stock"),  # Origin
                            line.company_id,
                            line._prepare_run_values_compra()  # Values
                        )
                    ])
                except UserError as error:
                    raise UserError(error)
        res = super(SaleOrderLine, self)._action_launch_stock_rule(previous_product_uom_qty)
        print(f'Resultado{res}')
        return res