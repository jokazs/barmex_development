# -*- coding: utf-8 -*-

from odoo import models, fields, api


class equipos(models.Model):
    # Para que aparezca el chatter
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _name = 'barmex_sistemas.equipos'
    _description = 'barmex_sistemas.equipos'
    _rec_name = 'numero_serie'

    # Encabezado
    nombre_equipo = fields.Char(string="Nombre del equipo", tracking=True)
    estatus_equipo = fields.Selection([
        ('1', 'Nuevo'),
        ('2', 'Reparado'),
        ('3', 'Reasignado')], default='1', string="Estatus del equipo", tracking=True)
    numero_serie = fields.Char(string="Número de serie", tracking=True)
    numero_producto = fields.Char(string="Número de producto", tracking=True)
    numero_factura = fields.Char(string="Número de factura", tracking=True)
    proveedor = fields.Char(string="Proveedor", tracking=True)
    monto_factura = fields.Float(string="Monto factura", tracking=True)
    tipo_equipo = fields.Many2one(
        "barmex_sistemas.tipo_equipos", string="Tipo de equipo", tracking=True)
    fecha_factura = fields.Date(
        string="Fecha de factura", default=fields.Date.today, tracking=True)

    # Pestaña de equipo
    modelo = fields.Many2one(
        "barmex_sistemas.modelos_equipos", string="Modelo", tracking=True)
    marca = fields.Many2one(
        "barmex_sistemas.marcas_equipos", string="Marca", tracking=True)
    ram = fields.Many2one(
        "barmex_sistemas.ram", string="RAM", tracking=True)
    rom = fields.Many2one(
        "barmex_sistemas.rom", string="ROM", tracking=True)
    procesador = fields.Char(string="Procesador", tracking=True)
    sistema_operativo = fields.Many2one(
        "barmex_sistemas.sistemas_operativos", string="Sistema operativo", tracking=True)
    product_key = fields.Many2one(
        "barmex_sistemas.licencias", string="Licencia", tracking=True)

    # Envio
    fecha_envio = fields.Date(
        string="Fecha de envío", default=fields.Date.today, tracking=True)
    fecha_llegada = fields.Date(
        string="Fecha de llegada", default=fields.Date.today, tracking=True)
    guia = fields.Char(string="Guia", tracking=True)
    # Seguimiento
    seguimiento = fields.Text(string="Seguimiento", tracking=True)
    # Comentarios
    comentarios = fields.Text(string="Comentarios", tracking=True)
    #Programas
    programas_id = fields.Many2many('barmex_sistemas.programas', "sistemas_equipos_programas_rel","sistemas_equipos_id","sistemas_programas_id", string='Programas')
    #Respaldos
    respaldos_id = fields.Many2many('barmex_sistemas.respaldos', "sistemas_equipos_respaldos_rel","sistemas_equipos_id","sistemas_respaldos_id", string='Respaldos')
    #Configuraciones
    configuraciones_id = fields.Many2many('barmex_sistemas.configuraciones', "sistemas_equipos_configuraciones_rel","sistemas_equipos_id","sistemas_configuraciones_id", string='Configuraciones')
