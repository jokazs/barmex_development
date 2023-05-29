from datetime import datetime, timedelta
from odoo import models, fields, _

class ResCompany(models.Model):
    _inherit = "res.company"


    #Produccion
    producto_pp_id = fields.Many2one('product.product','Producto a usar en Pronto pago')
    producto_bon_id = fields.Many2one('product.product','Producto a usar en Bonificaciones')
