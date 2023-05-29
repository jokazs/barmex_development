from odoo import models, fields, api


class programas(models.Model):       
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _name = "barmex_sistemas.programas"
    _description = "barmex_sistemas.programas"
    _rec_name='nombre_programa'

    nombre_programa = fields.Char(tracking=True, string="Programas", required=True)
    
    _sql_constraints = [
        ('nombre_programa_uniq', 'unique (nombre_programa)', "Nombre de programa ya existe!"),
    ]