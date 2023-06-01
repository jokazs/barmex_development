from odoo import models, fields, api, _
from datetime import datetime, date
from odoo.exceptions import ValidationError

class Classification(models.Model):
    _name = 'barmex.classification'
    _description = 'Classification'
    _order = 'id desc'
    _check_company_auto = True
    _rec_name = 'classification'
    _sql_constraints = [('unique_classification_configuration', 'unique(classification)',
                         _('Classification already exist'))]

    classification = fields.Selection(
        [
            ('A', 'A'),
            ('B', 'B'),
            ('C', 'C'),
            ('D', 'D'),
            ('E', 'E'),
            ('F', 'F'),
            ('G', 'G'),
        ],
        required=True,
        string='Classification'
    )

    min_factor = fields.Float(string='Minimum factor')

    max_factor = fields.Float(string='Maximum factor')

    days = fields.Integer(string='Days')

    default = fields.Boolean(string='Default')

    approbation = fields.Boolean(string='Approbation')

    classification_ids = fields.One2many('barmex.product.classification',
                                         'classification_id',
                                         string='Products')

    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.company)

    @api.constrains('default')
    def one_default(self):
        count = 0
        classifications = self.env['barmex.classification'].search([('default', '=', True)])

        for classification in classifications:
            count += 1

        if count > 1:
            raise ValidationError(_('Only one classification can be marked as default'))