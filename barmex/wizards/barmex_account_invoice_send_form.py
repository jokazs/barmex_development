from odoo import models, fields


class AccountInvoiceSend(models.TransientModel):
    _inherit = 'account.invoice.send'
    
    email_recepient = fields.Char('Destinatario')