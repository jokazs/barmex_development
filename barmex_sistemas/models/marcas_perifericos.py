from odoo import models, fields, api


class marcas_perifericos(models.Model):       
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _name = 'barmex_sistemas.marcas_perifericos'    
    _description = 'barmex_sistemas.marcas_perifericos'
    _rec_name='nombre_marca'

    nombre_marca = fields.Char(tracking=True, string="Tipo de equipo", required=True)
