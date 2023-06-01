import re
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ResUser(models.Model):
    _inherit = ['res.users']
    _sql_constraints = [('unique_user_barmex_id', 'unique(barmex_id)',
                         _('ID number is not unique!'))]

    barmex_id = fields.Char(string='ID number',
                            size=6)

    @api.onchange('barmex_id')
    def change_id(self):
        self.partner_id.barmex_id = self.barmex_id

    @api.constrains('barmex_id')
    def _is_ID(self):
        if self.barmex_id:
            if not re.match(r"^[0-9]{1,6}$", self.barmex_id):
                raise ValidationError(_("ID number contains invalid values!"))