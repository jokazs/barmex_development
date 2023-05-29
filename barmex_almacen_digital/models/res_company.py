from datetime import datetime, timedelta
from odoo import models, fields, _

class ResCompany(models.Model):
    _inherit = "res.company"


    #Produccion
    host_produccion = fields.Char('URL Produccion')
    user_produccion = fields.Char('Token Produccion')
    database_produccion = fields.Char('Base de datos Produccion')
