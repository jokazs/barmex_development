from odoo import models, fields, api


class modelos_perifericos(models.Model):       
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _name = 'barmex_sistemas.modelos_perifericos'    
    _description = 'barmex_sistemas.modelos_perifericos'
    _rec_name='nombre_modelo'

    nombre_modelo = fields.Char(tracking=True, string="Modelo de periferico", required=True)
