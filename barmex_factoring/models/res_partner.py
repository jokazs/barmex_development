from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'
    _description = 'Description'

    factoraje = fields.Boolean('Factoring')
    payment_partner_id = fields.Many2one('res.partner',
                                         string='Invoice partner')

    #@api.constrains('factoraje', 'percent')
    #def validation_percent(self):
        #for rec in self:
            #if rec.factoraje:
                #raise ValidationError(_('The factoring percentage must be greater than or equal to 0'))

    @api.onchange('factoraje')
    def onchange_factoring(self):
        if not self.factoraje:
            self.payment_partner_id = False
