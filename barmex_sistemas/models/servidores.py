# -*- coding: utf-8 -*-

from odoo import models, fields, api


class servidores(models.Model):
    # Para que aparezca el chatter
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _name = 'barmex_sistemas.servidores'
    _description = 'barmex_sistemas.servidores'
    _rec_name = 'ubicacion_servidor'

    # Encabezado
    ubicacion_servidor = fields.Char(string="Ubicación del servidor", tracking=True)
    ip_servidor = fields.Char(string="IP del servidor", tracking=True)
    dominio_servidor = fields.Char(string="Dominio", tracking=True)
    password_servidor = fields.Char(string="Contraseña", tracking=True)
    so_servidor = fields.Many2one("barmex_sistemas.sistemas_operativos", string="S.O.", tracking=True)
    recuperacion_servidor = fields.Char(string="Contraseña recuperación", tracking=True)
    teamviewer_servidor = fields.Char(string="Teamviewer", tracking=True)
    pass_teamviewer_servidor = fields.Char(string="Contraseña teamviewer", tracking=True)
    pass_tplink_teamviewer_servidor = fields.Char(string="Contraseña TP-LINK", tracking=True)
    tplink_servidor = fields.Char(string="IP TP-LINK", tracking=True)
    usuario_tplink_teamviewer_servidor = fields.Char(string="Usuario TP-LINK", tracking=True)