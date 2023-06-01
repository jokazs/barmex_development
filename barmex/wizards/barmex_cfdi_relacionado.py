# -*- coding: utf-8 -*-

from odoo import models, fields, api

class duplicar_semana(models.TransientModel):
    _name = 'barmex.cfdi.relacionado'

    def action_barmex_cfdi_relacionado_apply(self):
        data = self.name
        leads = self.env['account.move'].browse(self.env.context.get('active_ids'))
        return leads.update_cfdi_relacionados(data)

    @api.depends('tipo_relacionado','account_move_id')
    @api.onchange('tipo_relacionado','account_move_id')
    def _get_name(self):
        numbers = ['uno','dos','tres','cuatro','cinco','seis','siete']
        if self.account_move_id.l10n_mx_edi_cfdi_uuid:
            factura = self.account_move_id.l10n_mx_edi_cfdi_uuid
        else:
            factura = ""
        self.name = str(numbers.index(self.tipo_relacionado) + 1) + "|" + factura

    @api.depends('tipo_relacionado','name')
    @api.onchange('tipo_relacionado','name')
    def _get_partner(self):
        leads = self.env['account.move'].browse(self.env.context.get('active_ids'))
        self.partner_id = leads.partner_id

    name = fields.Char('Nombre', compute="_get_name")
    tipo_relacionado = fields.Selection([('uno', '01 | Nota de crédito de los documentos relacionados'),
                                        ('dos', '02 | Nota de débito de los documentos relacionados'),
                                        ('tres', '03 | Devolución de mercancía sobre facturas o traslados previos'),
                                        ('cuatro', '04 | Sustitución de los CFDI previos'),
                                        ('cinco', '05 | Traslados de mercancias facturados previamente'),
                                        ('seis', '06 | Factura generada por los traslados previos'),
                                        ('siete', '07 | CFDI por aplicación de anticipo')],
                                        'Tipo de relación', default='uno')
    account_move_id = fields.Many2one('account.move', 'Factura', domain="['|', ('type','=','out_invoice'),('type','=','out_refund')]")
    partner_id = fields.Many2one('res.partner', compute="_get_partner")