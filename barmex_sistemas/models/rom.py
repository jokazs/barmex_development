from odoo import models, fields, api


class rom(models.Model):       
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _name = 'barmex_sistemas.rom'    
    _description = 'barmex_sistemas.rom'
    _rec_name='capacidad'

    capacidad = fields.Char(tracking=True, string="Tamaño de ROM", required=True)
