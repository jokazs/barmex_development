# -*- coding: utf-8 -*-

from odoo import fields, models, api


class WizardReportCobranza(models.TransientModel):
    _name = 'wizard.report.cobranza'
    _description = 'Reporte Caobranza'


    date_from = fields.Date('Fecha Inicio')
    date_to = fields.Date('Fecha Fin')
    partner_type = fields.Selection([('customer', 'Customer'), ('supplier', 'Vendor')], string='A:')

    def export_excel_report(self):
        return {
            'type': 'ir.actions.act_url',
            'url': ('/barmex_report_cobranza/print_excel/%s' % self.id),
            'target': 'self'
        }
