# -*- coding: utf-8 -*-

from odoo import models, fields, api


class perifericos(models.Model):
    # Para que aparezca el chatter
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _name = 'barmex_sistemas.perifericos'
    _description = 'barmex_sistemas.perifericos'
    _rec_name = 'numero_serie'

    # Encabezado
    descripcion_periferico = fields.Char(string="Descripción del perifericos", tracking=True)
    numero_serie = fields.Char(string="Numero de serie", tracking=True)
    marca_periferico = fields.Many2one("barmex_sistemas.marcas_perifericos", string="Marca", tracking=True)
    modelo_periferico = fields.Many2one("barmex_sistemas.modelos_perifericos", string="Modelo", tracking=True)
    tipo_periferico = fields.Many2one("barmex_sistemas.tipo_perifericos", string="Tipo", tracking=True)