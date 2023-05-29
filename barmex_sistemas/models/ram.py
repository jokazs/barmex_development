from odoo import models, fields, api


class ram(models.Model):       
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _name = 'barmex_sistemas.ram'    
    _description = 'barmex_sistemas.ram'
    _rec_name='capacidad'

    capacidad = fields.Char(tracking=True, string="Tamaño de RAM", required=True)
