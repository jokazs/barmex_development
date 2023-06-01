from odoo import models, fields, api, _

class DialogBox(models.TransientModel):
    _name = 'barmex.dialog.box'
    _description = 'Dialog box'

    name = fields.Char(string='Title',
                       default='Info')

    text = fields.Char(string='Message',
                       readonly=True)

    dialog_lines = fields.One2many('barmex.dialog.box.line',
                                   'dialog_id',
                                   readonly=True)

    record_id = fields.Integer('Related record')

    def display_dialog(self,title,message,content,record=0):
        new = self.env['barmex.dialog.box'].create({'name':title,'dialog_lines':content, 'record_id':record, 'text':message})
        ir_model_data = self.env['ir.model.data']
        dialog_form_id = ir_model_data.get_object_reference('barmex', 'barmex_dialog_box')[1]

        return {
            'type': 'ir.actions.act_window',
            'name': new.name,
            'res_model': 'barmex.dialog.box',
            'view_mode': 'form',
            'res_id': new.id,
            'view_id': dialog_form_id,
            'views': [(dialog_form_id, 'form')],
            'target': 'new'}

    def action_confirm(self):
        order = self.env['purchase.order'].browse(self.record_id)
        if order.state not in ('pending','offer'):
            order.button_confirm()

        elif order.approved:
            order.button_confirm()

    def action_cancel(self):
        order = self.env['purchase.order'].browse(self.record_id)
        order.state = 'draft'
        order.approved = False

