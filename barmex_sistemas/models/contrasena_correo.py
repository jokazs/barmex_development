# -*- coding: utf-8 -*-

from odoo import models, fields, api


class contrasena_correo(models.Model):
    # Para que aparezca el chatter
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _name = 'barmex_sistemas.contrasena_correo'
    _description = 'barmex_sistemas.contrasena_correo'
    _rec_name = 'empleado_id'

    # Encabezado
    empleado_id = fields.Many2one("hr.employee", string="Empleado")
    nombre_perfil = fields.Char(String="Perfil de lotus", tracking=True)
    contrasena = fields.Char(String="Contraseña", tracking=True)    