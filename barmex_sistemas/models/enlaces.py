# -*- coding: utf-8 -*-

from odoo import models, fields, api


class enlaces(models.Model):
    # Para que aparezca el chatter
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _name = 'barmex_sistemas.enlaces'
    _description = 'barmex_sistemas.enlaces'
    _rec_name = 'velocidad_enlace'

    # Encabezado
    velocidad_enlace = fields.Char(string="Velocidad de internet", tracking=True)
    cuenta_enlace = fields.Char(string="Cuenta", tracking=True)
    compania_enlace = fields.Char(string="Compania", tracking=True)
    numero_cliente_enlace = fields.Char(string="Número de cliente", tracking=True)
    numero_reportes_enlace = fields.Char(string="Número para reporte", tracking=True)
    numero_ventas_enlace = fields.Char(string="Número de asesor de ventas", tracking=True)
    sucursal_enlace = fields.Char(string="Sucursal", tracking=True)