from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class WizardMergePartner(models.TransientModel):
    _name = 'wizard.merge.partner'
    _description = 'Merge res Partner'

    partner_id = fields.Many2one('res.partner', string='Partner')
    partner_ids = fields.Many2many('res.partner', string='Partners', ondelete="cascade",
                               default=lambda self: self.env.context.get('active_ids'))
    display_alert = fields.Boolean('Alert', compute='_compute_display_alert')

    def _compute_display_alert(self):
        for wizard in self:
            wizard.display_alert = bool(
                any(partner.parent_id.id is not False for partner in wizard.partner_ids))

    @api.model
    def default_get(self, fields):
        res = super(WizardMergePartner, self).default_get(fields)
        partners = self.env['res.partner'].search([('id', 'in', self.env.context.get('active_ids'))])
        display_alert = bool(
            any(partner.parent_id.id is not False for partner in partners))
        res.update({
            'display_alert': display_alert
        })
        return res

    def merge_partner(self):
        if self.partner_id in self.partner_ids:
            raise ValidationError(_('Por favor verifique que la empresa no este seleccionada como contacto'))
        elif not self.partner_id.vat:
            self.partner_id.sudo().update({
                'vat': self.partner_ids[0].vat
            })
        for partner in self.partner_ids:
            partner.write({
                'parent_id': self.partner_id.id,
                'company_type': 'person',
            })

        message = _('Task successfully completed')
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Warning'),
                'type': 'warning',
                'message': message,
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'}
            }
        }
