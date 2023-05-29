from odoo import models, fields, api


class modelos_equipos(models.Model):       
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _name = 'barmex_sistemas.modelos_equipos'    
    _description = 'barmex_sistemas.modelos_equipos'
    _rec_name='nombre_modelo'

    nombre_modelo = fields.Char(tracking=True, string="Modelo de equipo", required=True)
