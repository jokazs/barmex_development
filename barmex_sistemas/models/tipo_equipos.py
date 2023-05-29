from odoo import models, fields, api


class tipo_equipos(models.Model):           
    _name = 'barmex_sistemas.tipo_equipos'    
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'barmex_sistemas.tipo_equipos'
    _rec_name='nombre_tipo_equipos'

    nombre_tipo_equipos = fields.Char(tracking=True, string="Nombre del tipo de equipo", required=True)
