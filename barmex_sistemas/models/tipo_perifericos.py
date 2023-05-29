from odoo import models, fields, api


class tipo_perifericos(models.Model):           
    _name = 'barmex_sistemas.tipo_perifericos'    
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'barmex_sistemas.tipo_perifericos'
    _rec_name='nombre_tipo_perifericos'

    nombre_tipo_perifericos = fields.Char(tracking=True, string="Tipo de periferico", required=True)
