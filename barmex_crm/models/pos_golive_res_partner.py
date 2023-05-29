from odoo import models, fields, api

class resPartner(models.Model):
    _name = "res.partner"
    _inherit = "res.partner"

    nombre_fiscal = fields.Char('Nombre Fiscal Completo')
    iva_desglosado = fields.Boolean('Iva desglosado', default=False)
    numero_decimales = fields.Integer('Numero de Decimales', default=2)