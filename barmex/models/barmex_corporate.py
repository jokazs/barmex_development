from odoo import models, fields, api, _

class Corporate(models.Model):
    _name = 'barmex.corporate'
    _description = 'Corporate'

    name = fields.Char('Corporativo')
