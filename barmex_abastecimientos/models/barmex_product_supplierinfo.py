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
import logging
_logger = logging.getLogger(__name__)

class ProductSupplierInfo(models.Model):
    _inherit = 'product.supplierinfo'

    principal = fields.Boolean(string='Proveedor principal')

    def create(self,vals):
        try:
            proveedor = self.env['res.partner'].browse(vals[0]['name'])
            if proveedor.proveedor:
                return super(ProductSupplierInfo, self).create(vals)
        except:
            return super(ProductSupplierInfo, self).create(vals)
        
    def secuencia_principal(self):
        print('Entro a secuencia_principal')
        self.sequence = 0
        self.principal = True
        if self.product_tmpl_id:
            otros_productos = self.env['product.supplierinfo'].search([('product_tmpl_id','=',self.product_tmpl_id.id)])
            i = 2
            print(otros_productos)
            for producto in otros_productos:
                print(producto.id)
                print(self.id)
                if producto.id != self.id:
                    producto.sequence = i
                    i += 1
                    producto.principal = False

                