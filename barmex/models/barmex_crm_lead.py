from odoo import models, fields, api, _

class Lead(models.Model):
    _inherit = 'crm.lead'
    #
    
    lco_participant_ids = fields.Many2many('hr.employee',
                                           'crm_lead_hr_employee_rel',
                                           'crm_lead_id',
                                           'hr_employee_id',
                                           string='Participants',
                                           stored=True)
