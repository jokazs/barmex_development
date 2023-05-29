from odoo import models,fields

class CRMTeam(models.Model):
    _inherit = "crm.team"
    _description = 'add currency to crm.lead'

    agente_ventas_crm = fields.Many2one('hr.employee', string='Agente de Ventas')