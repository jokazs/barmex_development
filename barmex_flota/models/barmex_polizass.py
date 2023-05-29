from email.policy import default
from odoo import models, fields, api, _
from datetime import date
from odoo.exceptions import AccessError, ValidationError

class polizass(models.Model):
    _name = 'barmex.polizass'
    _description = 'barmex.polizass'

    name = fields.Char('No. Póliza')
    aseguradora = fields.Char('Aseguradora/Empresa')
    inicio_contrato = fields.Date('Inicio de contrato')
    vigencia = fields.Date('Vigencia')
    state = fields.Selection([('inactivo', 'Inactivo'),
                              ('activo', 'Activo')],
                             'Estado', index=True, default='activo')
    comentariosp = fields.Text('Comentarios')

    unidad_id = fields.Many2one('barmex.unidades', 'Unidad')