# -*- coding: utf-8 -*-

from odoo import models, fields, api


class contrasena_correo(models.Model):
    # Para que aparezca el chatter
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _name = 'barmex_sistemas.correo'
    _description = 'barmex_sistemas.correo'
    _rec_name = 'cuenta_correo'

    # Encabezado
    empleado_id = fields.Many2one("hr.employee", string="Empleado")
    cuenta_correo = fields.Char(string="Perfil de lotus", tracking=True)
    contrasena = fields.Char(string="Contraseña", tracking=True)