# -*- coding: utf-8 -*-

from odoo import models, fields, api


class custom_employee(models.Model):
    _inherit = 'hr.employee'
      
    personal_phone = fields.Char()
    authorizes_travel = fields.Many2one('hr.employee', 'Coach', domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    beneficiario_1 = fields.Char()
    beneficiario_2 = fields.Char()
    beneficiario_3 = fields.Char()
#     _name = 'custom_employee.custom_employee'
#     _description = 'custom_employee.custom_employee'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
