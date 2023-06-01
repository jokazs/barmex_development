from odoo import fields, models, _

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    payment_notification_template_id = fields.Many2one('mail.template', string='Payment Notification Email',
                                                       domain="[('model', '=', 'account.payment')]",
                                                       config_parameter='account.default_vendor_notification_template',
                                                       help="Email sent to the vendor once the bill is paid.")