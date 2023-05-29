# from dataclasses import field
import string
from odoo import models,fields

class ProntoPago(models.Model):
    _name = "barmex.pronto_pago_catalogo"
    _description = 'Catalogo pronto pago'
    name = fields.Char(string="Descripcion (Plazo de pago)")
    plazo_pago_id = fields.Many2one('account.payment.term','Plazo de pago autorizado')

    dias_credito = fields.Integer(string="Dias credito")
    dias_pp = fields.Integer(string="Dias 1er PP")
    dias_pp_por = fields.Integer(string="Dias 1er %PP")
    dias_pp_seg = fields.Integer(string="Dias 2do PP")
    dias_pp_seg_por = fields.Integer(string="Dias 2do %PP")