from odoo import models, fields, api


class sistemas_operativos(models.Model):       
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _name = 'barmex_sistemas.sistemas_operativos'    
    _description = 'barmex_sistemas.sistemas_operativos'
    _rec_name='nombre_so'

    nombre_so = fields.Char(tracking=True, string="Nombre del Sistema operativo", required=True)
