from odoo import models, fields, api, _

class StockProductionLot(models.Model):
    _inherit = ['stock.production.lot']

    lote_creation_date = fields.Datetime('Fecha de fabricación')