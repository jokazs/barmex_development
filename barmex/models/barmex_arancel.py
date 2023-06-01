from odoo import models, fields, _

class Arancel(models.Model):
    _inherit = 'l10n_mx_edi.tariff.fraction'

    fecha_inicio_vigencia = fields.Char("Inicio de vigencia")
    fecha_fin_vigencia = fields.Char("Inicio de vigencia")
    imp = fields.Float("IMP")
    ext = fields.Float("EXT")