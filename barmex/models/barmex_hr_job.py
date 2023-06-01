from odoo import models, fields, _

class Job(models.Model):
    _inherit = 'hr.job'

    x_studio_field_0rCZE = fields.Many2many('x_asignaciones', string='Asignaciones', track_visibility=True)