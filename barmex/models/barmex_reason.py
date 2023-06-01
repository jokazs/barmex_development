from odoo import models, fields, api, _
from odoo.exceptions import Warning

class Reason(models.Model):
    _name = 'barmex.reason'
    _description = 'Credit note reasons'
    _order = 'id desc'
    _check_company_auto = True

    name = fields.Char(string='Reason',
                       required=True)

    description = fields.Char(string='Description',
                              required=True)

    discount = fields.Boolean(string='For discount')

    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.company)

    def unlink(self):
        if self.discount:
            raise Warning(_("This record can not be deleted"))

        res = super(Reason, self).unlink()

        return res