from odoo import models, fields, api


class tipo_disco(models.Model):       
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _name = 'barmex_sistemas.tipo_disco'    
    _description = 'barmex_sistemas.tipo_disco'
    _rec_name='nombre_tipo_disco'

    nombre_tipo_disco = fields.Char(tracking=True, string="Tipo de disco", required=True)
