# -*- coding: utf-8 -*-

from email.policy import default
from odoo import models, fields, api, _
from datetime import date
from odoo.exceptions import AccessError, ValidationError

class catalogo_mto(models.Model):
    _name = 'barmex.catalogo_mto'
    _description = 'barmex.catalogo_mto'

    name = fields.Char('Nombre Concepto')

class cursos(models.Model):
    _name = 'barmex.cursos'
    _description = 'barmex.cursos'

    name = fields.Char('Nombre del curso')
    folio = fields.Char('Folio')
    fecha_realizacion = fields.Char('Fecha de Realización')
    fecha_vigencia = fields.Char('Fecha de Vigencia')
    empresa_emisora = fields.Char('Empresa Emisora')
    curso_id = fields.Many2one('barmex.operadores', 'Cursos')

class gasolinerias(models.Model):
    _name = 'barmex.gasolinerias'
    _description = 'barmex.gasolinerias'

    name = fields.Char('Folio')
    nombre = fields.Char('Nombre: ')