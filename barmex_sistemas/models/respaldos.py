from odoo import models, fields, api


class respaldos(models.Model):       
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _name = "barmex_sistemas.respaldos"
    _description = "barmex_sistemas.respaldos"
    _rec_name='nombre_respaldo'

    nombre_respaldo = fields.Char(tracking=True, string="Respaldos", required=True)
    fecha_respaldo = fields.Date(string="Fecha de respaldo", default=fields.Date.today, tracking=True)
    comentarios = fields.Text(string="Comentarios", tracking=True)
    
    _sql_constraints = [
        ('nombre_respaldo_uniq', 'unique (nombre_respaldo)', "Nombre de respaldo ya existe!"),
    ]