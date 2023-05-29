from email.policy import default
from odoo import models, fields, api, _
from datetime import date
from odoo.exceptions import AccessError, ValidationError

class mantenimiento(models.Model):
    _name = 'barmex.mantenimiento'
    _description = 'barmex.mantenimiento'
    _inherit = 'mail.thread', 'mail.activity.mixin', 'utm.mixin'

    name = fields.Char('Folio')
    kilometraje = fields.Float('Kilometraje')
    realizada = fields.Date('Fecha realizada')
    comentarios = fields.Text('Comentarios/Detalles')
    descripcion = fields.Char('Descripcion')
    costo = fields.Float('Costo de mantenimiento')
    fuera_servicio = fields.Float('Dias fuera de servicio')
    concepto_mantenimiento = fields.Many2many('barmex.catalogo_mto',  string='Descripcion mantenimiento')
    Concepto = fields.Char('Concepto')
    unidad_id = fields.Many2one('barmex.unidades', 'Unidad')
    refacciones = fields.Text('Refacciones')

    @api.model
    def create(self, vals):
        x = self.env['ir.sequence'].next_by_code('barmex.mantenimiento') or '/'
        vals['name'] = x
        return super(mantenimiento, self).create(vals)