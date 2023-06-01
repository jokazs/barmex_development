from odoo import models, fields, api, _

class ForeignTrade(models.Model):
    _name = 'barmex.foreign.trade.customs'
    _description = 'Foreign trade customs'
    _order = 'id desc'
    _check_company_auto = True
    _sql_constraints = [
        ('unique_custom', 'unique(code)', _('Custom is not unique'))]

    name = fields.Char(string="Name",
                       required=True)

    code = fields.Char(string="Code",
                       required=True)