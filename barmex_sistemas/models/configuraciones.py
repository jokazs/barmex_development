from odoo import models, fields, api


class configuraciones(models.Model):       
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _name = "barmex_sistemas.configuraciones"
    _description = "barmex_sistemas.configuraciones"
    _rec_name = 'nombre_configuracion'

    nombre_configuracion = fields.Char(tracking=True, string="Configuración", required=True)
    
    _sql_constraints = [
        ('nombre_configuracion_uniq', 'unique (nombre_configuracion)', "Nombre de configuración ya existe !"),
    ]