from odoo import models, fields, api


class marcas_equipos(models.Model):       
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _name = 'barmex_sistemas.marcas_equipos'    
    _description = 'barmex_sistemas.marcas_equipos'
    _rec_name='nombre_marca'

    nombre_marca = fields.Char(tracking=True, string="Marca de equipo", required=True)
