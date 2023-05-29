# -*- coding: utf-8 -*-

from odoo import models, fields, api


class licencias(models.Model):
    # Para que aparezca el chatter
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _name = 'barmex_sistemas.licencias'
    _description = 'barmex_sistemas.licencias'
    _rec_name = 'key_licencia'

    # Encabezado
    product_id_licencia = fields.Char(string="Product id", tracking=True)
    key_licencia =fields.Char(string="Key", tracking=True)
    so_licencia = fields.Many2one("barmex_sistemas.sistemas_operativos", string="Sistemas operativos", tracking=True)