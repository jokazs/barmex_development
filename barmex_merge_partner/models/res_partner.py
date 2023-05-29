from odoo import fields, models, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def action_merge_partner(self):
        action = self.env.ref('barmex_merge_partner.wizard_merge_partner_act_window').read()[0]
        action['target'] = 'new'
        action['context'] = {
            'active_ids': self.env.context['active_ids'] if 'active_ids' in self.env.context else self.ids,
            'active_model': self.env.context['active_model'] if 'active_model' in self.env.context else 'res.partner'}
        return action
