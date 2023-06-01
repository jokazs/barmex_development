from odoo import api, fields, models

class MailComposeMessage(models.TransientModel):
    _inherit = ['mail.compose.message']
    
    email_recepient = fields.Char('Destinatario')
    
    @api.onchange('partner_ids')
    def print(self):
        print('partners print')
        print(self.partner_ids)