from odoo import models, fields, api, _

class CrmTeam(models.Model):
    _inherit = "crm.team"

    member_ids = fields.Many2many('res.users',string="Team Members")