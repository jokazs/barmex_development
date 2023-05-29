import base64
from uuid import uuid1

from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _
from odoo.tools import date_utils
from odoo.tools.float_utils import float_compare
from odoo.exceptions import UserError, ValidationError, Warning

from datetime import datetime

class AccountMove(models.Model):
    _inherit = ['account.move']

    folios_ap_ids = fields.Many2many('almacen.digital','account_move_id_almacen_digital_id','account_move_id','almacen_digital_id',string='Almacen Digital')
    journal_currency = fields.Char('Moneda pago', related='journal_id.currency_id.name', default='MXN')
