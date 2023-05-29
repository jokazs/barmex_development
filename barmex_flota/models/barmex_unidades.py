from email.policy import default
from odoo import models, fields, api
from datetime import date

class unidades(models.Model):
    _name = 'barmex.unidades'
    _description = 'barmex.unidades'

    name = fields.Char('Clave')
    marca = fields.Char('Marca')
    anio = fields.Char('Año')
    serie = fields.Char('Numero de Serie')
    conductor = fields.Many2one('barmex.operadores', 'Conductor Habitual')
    placa = fields.Char('Placa Federal')
    modelo = fields.Char('Modelo')
    tipo_unidad = fields.Selection([('camioneta', 'Camioneta'),
                              ('camion', 'Camion'),
                              ('pipa', 'Pipa')],
                             'Tipo de Unidad', index=True, default='camioneta')
    no_motor = fields.Char('Numero de motor')
    no_corto = fields.Char('Numero corto')
    capacidad_kg = fields.Float('Capacidad de carga en KG')
    capacidad_lt = fields.Float('Capacidad en litros (PIPAS)')
    tipo_combustible = fields.Selection([('diesel', 'Diesel'),
                              ('gasolina', 'Gasolina'),
                              ('gas', 'Gas')],
                             'Tipo de Combustible', index=True, default='gasolina')
    tambores = fields.Float('Numero de tambores que puede cargar: ')
    capacidad_t = fields.Char('Capacidad de tanque (lleno)')
    poliza = fields.Char('Numero de Poliza')
    vigencia_poliza = fields.Date('Vigencia de Poliza')
    comentarios = fields.Text('Comentarios')
    disponibilidad = fields.Selection([('en_servicio', 'En Servicio'),
                              ('menor', 'Mantenimiento menor'),
                              ('mayor', 'Mantenimiento mayor'),
                              ('restringido', 'Uso restringido'),
                              ('fuera', 'Fuera de Servicio')],
                             'Disponibilidad', index=True, default='en_servicio')
    permisosct = fields.Char('Numero de Permiso SCT')
    tipopermisosct = fields.Char('Tipo de Permiso SCT') ##catalogo#
    conf_vehicular = fields.Char('Configuración Vehícular') ##catalogo#

    registroc_ids = fields.One2many('barmex.registroc','unidad_id','Combustible')
    mantenimiento_ids = fields.One2many('barmex.mantenimiento','unidad_id','Mantenimiento')
    polizas_ids = fields.One2many('barmex.polizass','unidad_id','Polizas')