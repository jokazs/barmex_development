from odoo import models, fields, api, _

class Collector(models.Model):
    _name = 'barmex.collector'
    _description = 'Partner Collector'
    _order = 'sequence,id'
    _check_company_auto = True

    partner_id = fields.Many2one('res.partner',
                                 string='Customer',
                                 required=True)

    user_id = fields.Many2one('res.users',
                              string='Collector',
                              required=True)

    sequence = fields.Integer(default=1)

    name = fields.Char(string='Name',
                       compute='_set_name')

    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.company)

    cobrador_employee = fields.Many2one('hr.employee', string='Cobrador')

    @api.depends('user_id')
    def _set_name(self):
        for record in self:
            record.update({
                'name': record.user_id.name,
            })