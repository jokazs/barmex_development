from odoo import models, fields, api, _

class DialogBoxLine(models.TransientModel):
    _name ='barmex.dialog.box.line'
    _description = 'Dialog box line'

    dialog_id = fields.Many2one('barmex.dialog.box')

    name = fields.Char(string='Content')