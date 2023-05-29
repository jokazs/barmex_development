# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class asignaciones(models.Model):    
    #Para que aparezca el chatter    
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _name = 'barmex_sistemas.asignaciones'    
    _description = 'barmex_sistemas.asignaciones'
    _rec_name = 'folio'
    
    # Encabezado
    usuario_asignacion = fields.Many2one("hr.employee", string="Usuario", tracking=True)
    fecha_asignacion = fields.Date(string="Fecha de asignación", default=fields.Date.today, tracking=True)
    #Equipo
    equipos_asignacion_id = fields.Many2many('barmex_sistemas.equipos', "barmex_sistemas_asignacion_equipos_rel","barmex_sistemas_equipos_id","hr_employee_id", string='Equipos')
    #Periferico
    perifericos_asignacion_id = fields.Many2many('barmex_sistemas.perifericos', "barmex_sistemas_asignacion_perifericos_rel","barmex_sistemas_perifericos_id","hr_employee_id", string='Perifericos')    
    folio = fields.Char(string='Folio', required=True, copy=False, readonly=True, index=True, default=lambda self: _('New'))

    @api.model
    def create(self, vals):
        if vals.get('folio', _('New')) == _('New'):            
            vals['folio'] = self.env['ir.sequence'].next_by_code('barmex_sistemas.asignaciones.sequence') or _('New')
        result = super(asignaciones, self).create(vals)
        return result
