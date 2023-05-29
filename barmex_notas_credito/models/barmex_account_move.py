from datetime import datetime
from unittest import result
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.tools.misc import formatLang, get_lang
from odoo.exceptions import ValidationError, Warning
from odoo.tools.misc import clean_context
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare, float_round, float_is_zero
from odoo.exceptions import UserError
from collections import namedtuple, OrderedDict, defaultdict
from itertools import groupby


class AccountMove(models.Model):
    _inherit = 'account.move'
    nota_credito_asociada = fields.Many2one('account.move')
    def generar_nota_credito(self):
        if self.l10n_mx_edi_sat_status != 'valid':
            #raise ValidationError('El estado en el SAT debe ser igual a Valido para generar una nota de crédito.')
            print('Hola')

        print('self.nota_credito_asociada')
        print(self.nota_credito_asociada)

        if self.nota_credito_asociada:
            raise ValidationError('Factura ya cuenta con una nota de crédito asociada')
            print(self.nota_credito_asociada)
        campos = {
            'type': 'out_refund',
            'invoice_date': str(datetime.today().date()),
            'date': str(datetime.today().date()),
            'partner_id': self.partner_id.id,
            'currency_id': self.currency_id.id,
            'ref':self.name,
            'l10n_mx_edi_origin':f'01|{self.l10n_mx_edi_cfdi_uuid}'
            }
        nota_credito = self.env['account.move'].create(campos)
        self.nota_credito_asociada = nota_credito.id
        lineas_productos = self.env['account.move.line']
        for productos in self.invoice_line_ids:
            campos = {
                'name':  productos.product_id.name,
                'product_id': productos.product_id.id,
                'price_unit': productos.lco_price_diff,
                'quantity': productos.quantity, 
                'account_id': self.journal_id.nota_credito_cuenta.id,
                'move_id':nota_credito.id
            }
            move = lineas_productos.create(campos)

        return {
            'type': 'ir.actions.client',
            'tag': 'reload', #display_notification
            'params': {
                'message': 'Nota de credito creada',
                'type': 'success',
                'sticky': False,
            }
        }
