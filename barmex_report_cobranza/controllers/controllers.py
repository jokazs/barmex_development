# -*- coding: utf-8 -*-
import io

from odoo.http import request
from odoo.tools.misc import xlsxwriter
from odoo import http


class BarmexReportCobranza(http.Controller):

    @http.route('/barmex_report_cobranza/print_excel/<model("wizard.report.cobranza"):wizard>', type='http',
                auth='user')
    def download_report_document_tabla(self, wizard=None, **kw):
        head = {'Content-Type': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'Content-Disposition': 'attachment; filename="Reporte de Cobranza x Referencia.xlsx"',
                }
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        ws = workbook.add_worksheet('%s' % (wizard.date_from))
        style_highlight = workbook.add_format({'bold': True, 'pattern': 1, 'bg_color': '#E0E0E0', 'align': 'center'})
        carrier_format = workbook.add_format({'bg_color': '#ff8000', 'align': 'center'})
        currency_format = workbook.add_format({'num_format': '$#,##0.0000'})
        style_normal = workbook.add_format({'align': 'left'})
        row = 0

        label = [
            "Cliente",
            "Nombre Cliente",
            "Número Pago",
            "Factura",
            "F.Factura",
            "Folio",
            "Referencia",
            "$ Cobrado",
            "T.cambio Factura",
            "Mone",
            "$ Conv. M.N.",
            "IMP.USD",
            "IVA 2001 <=",
            "IVA 2002>=",
            "IVA%",
            "Responsable",
            "Banco"
        ]
        if wizard.partner_type:
            payment = http.request.env['account.payment'].search(
                [('payment_date', '>=', wizard.date_from), ('payment_date', '<=', wizard.date_to), ('state', 'in', ['posted']), ('partner_type', '=', wizard.partner_type)])
        else:
            payment = http.request.env['account.payment'].search([('payment_date', '=', wizard.date_from), ('payment_date', '<=', wizard.date_to), ('state', 'IN', ['posted'])])
        rows = []
        company = http.request.env['res.company'].search([('id', '=', 1)])
        conf = 0
        for pay in payment:
            for inv in pay.invoice_ids:
                print(pay.name)
                print(inv.line_ids.filtered(lambda l: l.tax_ids))
                conf += 1
                tasa = inv.amount_total_signed / inv.amount_total
                if pay.group_payment and not pay.partial_payment:
                    rows.append((
                        inv.partner_id.barmex_id_cust,
                        inv.partner_id.display_name,
                        pay.name,
                        inv.name,
                        inv.invoice_date,
                        inv.l10n_mx_edi_cfdi_uuid,
                        pay.communication,
                        inv.amount_total,
                        tasa if tasa > 1 else tasa * -1,
                        'MXN' if inv.currency_id.name == 'MXN' else 'USD',
                        inv.amount_untaxed_signed if inv.currency_id.name != 'MXN' else 0.00,
                        inv.amount_total,
                        inv.amount_tax_signed if inv.invoice_date.year <= 2001 else 0.00,
                        inv.amount_tax_signed if inv.invoice_date.year >= 2002 else 0.00,
                        inv.amount_by_group[0][0].split(' ')[1].split('%')[0] if len(inv.line_ids.filtered(lambda l: l.tax_ids)) > 0 else '',
                        pay.create_uid.name,
                        pay.journal_id.name
                    ))
                elif pay.group_payment and pay.partial_payment:
                    rows.append((
                        inv.partner_id.barmex_id_cust,
                        inv.partner_id.display_name,
                        pay.name,
                        inv.name,
                        inv.invoice_date,
                        inv.l10n_mx_edi_cfdi_uuid,
                        pay.communication,
                        inv.partial_payment,
                        tasa if tasa > 1 else tasa * -1,
                        'MXN' if inv.currency_id.name == 'MXN' else 'USD',
                        inv.partial_payment * tasa if inv.currency_id.name != 'MXN' else 0.00,
                        inv.partial_payment,
                        inv.amount_tax_signed if inv.invoice_date.year <= 2001 else 0.00,
                        inv.amount_tax_signed if inv.invoice_date.year >= 2002 else 0.00,
                        inv.amount_by_group[0][0].split(' ')[1].split('%')[0] if len(inv.line_ids.filtered(lambda l: l.tax_ids)) > 0 else '',
                        pay.create_uid.name,
                        pay.journal_id.name
                    ))
                elif pay.factoraje:
                    rows.append((
                        inv.partner_id.barmex_id_cust,
                        inv.partner_id.display_name,
                        pay.name,
                        inv.name,
                        inv.invoice_date,
                        inv.l10n_mx_edi_cfdi_uuid,
                        pay.communication,
                        inv.payment_factoring,
                        tasa if tasa > 1 else tasa * -1,
                        'MXN' if inv.currency_id.name == 'MXN' else 'USD',
                        inv.amount_untaxed_signed if inv.currency_id.name != 'MXN' else 0.00,
                        inv.payment_factoring,
                        inv.amount_tax_signed if inv.invoice_date.year <= 2001 else 0.00,
                        inv.amount_tax_signed if inv.invoice_date.year >= 2002 else 0.00,
                        inv.amount_by_group[0][0].split(' ')[1].split('%')[0] if len(inv.line_ids.filtered(lambda l: l.tax_ids)) > 0 else '',
                        pay.create_uid.name,
                        pay.journal_id.name
                    ))
                elif pay.exchange_rate and inv.to_pay == 0:
                    rows.append((
                        inv.partner_id.barmex_id_cust,
                        inv.partner_id.display_name,
                        pay.name,
                        inv.name,
                        inv.invoice_date,
                        inv.l10n_mx_edi_cfdi_uuid,
                        pay.communication,
                        inv.amount_total,
                        tasa if tasa > 1 else tasa * -1,
                        'MXN' if inv.currency_id.name == 'MXN' else 'USD',
                        inv.amount_untaxed_signed if inv.currency_id.name != 'MXN' else 0.00,
                        inv.amount_total,
                        inv.amount_tax_signed if inv.invoice_date.year <= 2001 else 0.00,
                        inv.amount_tax_signed if inv.invoice_date.year >= 2002 else 0.00,
                        inv.amount_by_group[0][0].split(' ')[1].split('%')[0] if len(inv.line_ids.filtered(lambda l: l.tax_ids)) > 0 else '',
                        pay.create_uid.name,
                        pay.journal_id.name
                    ))
                elif pay.exchange_rate and inv.currency_rate > 0:
                    rows.append((
                        inv.partner_id.barmex_id_cust,
                        inv.partner_id.display_name,
                        pay.name,
                        inv.name,
                        inv.invoice_date,
                        inv.l10n_mx_edi_cfdi_uuid,
                        pay.communication,
                        inv.to_pay,
                        tasa if tasa > 1 else tasa * -1,
                        'MXN' if inv.currency_id.name == 'MXN' else 'USD',
                        inv.to_pay * pay.currency_rate if inv.currency_id.name != 'MXN' else 0.00,
                        inv.to_pay,
                        inv.amount_tax_signed if inv.invoice_date.year <= 2001 else 0.00,
                        inv.amount_tax_signed if inv.invoice_date.year >= 2002 else 0.00,
                        inv.amount_by_group[0][0].split(' ')[1].split('%')[0] if len(inv.line_ids.filtered(lambda l: l.tax_ids)) > 0 else '',
                        pay.create_uid.name,
                        pay.journal_id.name
                    ))
                else:
                    rows.append((
                        inv.partner_id.barmex_id_cust,
                        inv.partner_id.display_name,
                        pay.name,
                        inv.name,
                        inv.invoice_date,
                        inv.l10n_mx_edi_cfdi_uuid,
                        pay.communication,
                        inv.amount_total,
                        inv.barmex_currency_rate if inv.currency_id.name == 'MXN' and inv.barmex_currency_rate == 1.0 else inv.amount_total_signed / inv.amount_total,
                        'MXN' if inv.currency_id.name == 'MXN' else 'USD',
                        inv.amount_untaxed_signed,
                        inv.amount_total if inv.currency_id.name != 'MXN' else 0.00,
                        inv.amount_tax_signed if inv.invoice_date.year <= 2001 else 0.00,
                        inv.amount_tax_signed if inv.invoice_date.year >= 2002 else 0.00,
                        inv.amount_by_group[0][0].split(' ')[1].split('%')[0] if len(inv.line_ids.filtered(lambda l: l.tax_ids)) > 0 else '',
                        pay.create_uid.name,
                        pay.journal_id.name
                    ))
        col = 1
        row = 5
        for et in label:
            if et == 'Nombre Cliente' or et == 'Referencia':
                ws.write(row, col, et, style_highlight)
                ws.set_column(col, col, 50)
                col += 1
            else:
                ws.write(row, col, et, style_highlight)
                ws.set_column(col, col, 15)
                col += 1
        row = 6
        groups = ''
        count = 0
        for resum in rows:
            col = 1
            count += 1
            for data in resum:
                if isinstance(data, float):
                    ws.write(row, col, data, currency_format)
                    col += 1
                elif data:
                    ws.write(row, col, str(data) if str(data) not in groups else data)
                    col += 1
                else:
                    ws.write(row, col, '')
                    col += 1
            row += 1

        ws.merge_range(row, 1, row, 7, 'Total', style_highlight)
        ws.write(row, 8, '{=SUM(I7:I%s)}' % (6+conf), currency_format)
        ws.write_formula(row, 11, '{=SUM(L7:L%s)}' % (6+conf), currency_format)
        ws.write(row, 12, '{=SUM(M7:M%s)}' % (6+conf), currency_format)
        ws.write(row, 13, '{=SUM(N7:N%s)}' % (6+conf), currency_format)
        ws.write(row, 14, '{=SUM(O7:O%s)}' % (6+conf), currency_format)
        ws.merge_range(1, 3, 1, 11, company.name, style_normal)
        ws.merge_range(2, 3, 2, 11, 'Reporte de Cobranza x Referencia', style_normal)
        ws.merge_range(3, 3, 3, 9, 'De la : %s hasta %s' % (str(wizard.date_from), str(wizard.date_to)), style_normal)
        workbook.close()
        docx_bytes = output.getvalue()
        return request.make_response(docx_bytes, head.items())

