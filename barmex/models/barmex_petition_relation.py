from odoo import models, fields, api, _

class PetitionRelation(models.Model):
    _name = 'barmex.petition.relation'
    _description = 'Petition Relation'
    _order = 'id desc'
    _check_company_auto = True
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']

    company_id = fields.Many2one('res.company',
                                 string="Company",
                                 default=lambda self: self.env.company)

    product_id = fields.Many2one('product.product',
                                 string="Product")

    available = fields.Float(string="Available")

    petition = fields.Char(string="Petition",
        help='Optional field for entering the customs information in the case '
        'of first-hand sales of imported goods or in the case of foreign trade'
        ' operations with goods or services.\n'
        'The format must be:\n'
        ' - 2 digits of the year of validation followed by two spaces.\n'
        ' - 2 digits of customs clearance followed by two spaces.\n'
        ' - 4 digits of the serial number followed by two spaces.\n'
        ' - 1 digit corresponding to the last digit of the current year, '
        'except in case of a consolidated customs initiated in the previous '
        'year of the original request for a rectification.\n'
        ' - 6 digits of the progressive numbering of the custom.',
        copy=False)

    date = fields.Datetime(string="Date")

    historial = fields.Text(string="Historial")

    foreign_trade_id = fields.Many2one('barmex.foreign.trade')

    