from email.policy import default
from odoo import models, fields, api, _
from datetime import date
from odoo.exceptions import AccessError, ValidationError

class operadores(models.Model):
    _name = 'barmex.operadores'
    _description = 'barmex.operadores'

    name = fields.Char('Nombre completo')
    fecha_ven = fields.Date('Fecha vencimiento licencia')
    rs = fields.Char('No. de Radio')
    comentarios = fields.Text('Comentarios / Detalles')
    licencia = fields.Char('Numero licencia')
    sangre = fields.Char('Tipo de sangre')
    alta = fields.Date('Fecha alta')
    cel = fields.Char('Tel. casa/celular')
    calle = fields.Char('Calle')
    numero = fields.Char('Numero exterior')
    colonia = fields.Char('Colonia')
    municipio = fields.Char('Municipio')
    estado = fields.Char('Estado')
    rfc = fields.Char('RFC')
    c_p = fields.Char('Código Postal')
    unidades_ids = fields.Many2many('barmex.unidades',string = 'Unidades')
    cursos_ids = fields.Many2many('barmex.cursos',string = 'Cursos')