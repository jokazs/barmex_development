from odoo import models, fields, api, _
from odoo.tools.float_utils import float_compare
import logging
import math
_logger = logging.getLogger(__name__)

class AccountMoveLine(models.Model):
    _inherit = ['account.move.line']

    l10n_mx_edi_customs_number = fields.Char(
        help='Optional field for entering the customs information in the case '
        'of first-hand sales of imported goods or in the case of foreign trade'
        ' operations with goods or services.\n'
        'The format must be:\n'
        ' - 2 digits of the year of validation followed by two spaces.\n'
        ' - 2 digits of customs clearance followed by two spaces.\n'
        ' - 4 digits of the serial number followed by two spaces.\n'
        ' - 1 digit corresponding to the last digit of the current year, '
        'except in case of a consolidated customs initiated in the previous '
        'year of the original request for a rectification.\n'
        ' - 6 digits of the progressive numbering of the custom.',
        string='Customs number', copy=True)
    
    
    moneda_n3 = fields.Char(string='Monedas Factura', compute='get_producto_marca')
    moneda_n2 = fields.Char(string='Moneda Factura')
    
    grupo_n3 = fields.Char(string='Grupos', compute='get_producto_marca')
    grupo_n2 = fields.Char(string='Grupo')
    
    sub_grupo_n3 = fields.Char(string='Subgrupos', compute='get_producto_marca')
    sub_grupo_n2 = fields.Char(string='Subgrupo')
    
    marca_n3 = fields.Char(string='Marcas', compute='get_producto_marca')
    marca_n2 = fields.Char(string='Marca')
    linea_factura = fields.Boolean("Partidas", default=False)

    fecha_n3 = fields.Date(string='Fechas', compute='get_producto_marca')
    fecha_n2 = fields.Date(string='Fecha Factura T')

    monto_mxn_n3 = fields.Char(string='Montos MXN', compute='get_producto_marca')
    monto_mxn_n2 = fields.Float(string='Monto MXN')

    cliente_n3 = fields.Char(string='ID Clientes', compute='get_producto_marca')
    cliente_n2 = fields.Char(string='ID Cliente')
    costo_n3 = fields.Float(string='Costos', compute='get_producto_marca')
    costo_n2 = fields.Float(string='Costo')
    margen_n3 = fields.Float(string='Margenes', compute='get_producto_marca')
    margen_n2 = fields.Float(string='Margen')

    subtotal_n3 = fields.Float(string='Subtotales', compute='get_producto_marca')
    subtotal_n2 = fields.Float(string='Subtotal')
    impuestos_n3 = fields.Float(string='Impuestoss', compute='get_producto_marca')
    impuestos_n2 = fields.Float(string='Impuestos')
    descuento_n3 = fields.Float(string='Descuentoss', compute='get_producto_marca')
    descuento_n2 = fields.Float(string='Descuentos')
    zona_venta_n3 = fields.Char(string='Zona de Ventas', compute='get_producto_marca')
    zona_venta_n2 = fields.Char(string='Zona de Venta')
    agente_venta_n3 = fields.Char(string='Agente de Ventas', compute='get_producto_marca')
    agente_venta_n2 = fields.Char(string='Agente de Venta')
    tipo_cliente_n3 = fields.Char(string='Tipo de Clientes', compute='get_producto_marca')
    tipo_cliente_n2 = fields.Char(string='Tipo de Cliente')
    tipo_mercado_n3 = fields.Char(string='Tipo de Mercados', compute='get_producto_marca')
    tipo_mercado_n2 = fields.Char(string='Tipo de Mercado')

    def get_producto_marca(self):
        for line in self:
            # if line.product_id and line.exclude_from_invoice_tab == False:
            try:
                if (line.line_type == 'out_invoice' or line.line_type == 'out_refund') and line.exclude_from_invoice_tab == False and line.account_id and line.product_id:
                    # line.marca_n3 = line.product_id.product_tmpl_id.categ_id.name
                    line.marca_n3 = line.product_id.brand_id.name
                    line.moneda_n3 = line.move_id.currency_id.name
                    line.grupo_n3 = line.product_id.product_tmpl_id.group_id.name
                    line.sub_grupo_n3 = line.product_id.product_tmpl_id.subgroup_id.name
                    line.fecha_n3 = line.move_id.invoice_date
                    line.monto_mxn_n3 = line.currency_id._convert(line.price_total, self.env.company.currency_id, self.env.company, line.move_id.invoice_date)
                    line.cliente_n3 = line.move_id.partner_id.barmex_id_cust
                    line.costo_n3 = round((line.quantity * line.product_id.standard_price),4)
                    line.margen_n3 = line.monto_mxn_n2 - line.costo_n2
                    line.subtotal_n3 = round(line.currency_id._convert(line.price_subtotal, self.env.company.currency_id, self.env.company, line.move_id.invoice_date),2)
                    line.impuestos_n3 = line.subtotal_n2 * (line.tax_ids.amount/100)
                    line.descuento_n3 = (line.quantity * round(line.currency_id._convert(line.price_unit, self.env.company.currency_id, self.env.company, line.move_id.invoice_date),2)) * (line.discount/100)
                    line.zona_venta_n3 = line.move_id.zona_venta_cliente.name
                    line.agente_venta_n3 = line.move_id.agente_venta_cliente.name
                    line.tipo_cliente_n3 = line.move_id.tipo_de_cliente.type_cust_id
                    line.tipo_mercado_n3 = line.move_id.tipo_mercado_cliente
                    # line.marca_n2 = line.product_id.product_tmpl_id.categ_id.name
                    line.marca_n2 = line.product_id.brand_id.name
                    line.moneda_n2 = line.move_id.currency_id.name
                    line.grupo_n2 = line.product_id.product_tmpl_id.group_id.name
                    line.sub_grupo_n2 = line.product_id.product_tmpl_id.subgroup_id.name
                    line.fecha_n2 = line.move_id.invoice_date
                    
                    line.cliente_n2 = line.move_id.partner_id.barmex_id_cust
                    line.zona_venta_n2 = line.move_id.zona_venta_cliente.name
                    line.agente_venta_n2 = line.move_id.agente_venta_cliente.name
                    line.tipo_cliente_n2 = line.move_id.tipo_de_cliente.type_cust_id
                    line.tipo_mercado_n2 = line.move_id.tipo_mercado_cliente
                    
                    line.costo_n2 = round((line.quantity * line.product_id.standard_price),4)
                    
                    if line.line_type == 'out_refund':
                        #Explicacion cambio subtotal_n2 a dedit para que siempre sea el monto exacto en pesos del subtotal. Al ser un campo calculado tenemos diferencias con la otra formula
                        line.subtotal_n2 = (round(line.debit,2))*-1
                        prueba = (line.subtotal_n2 / line.price_total)
                        prueba_2 = (line.price_total * .16)
                        line.impuestos_n2 = round((prueba * prueba_2),2)
                        line.monto_mxn_n2 = line.subtotal_n2 + line.impuestos_n2
                    elif line.line_type == 'out_invoice':
                        #Explicacion cambio subtotal_n2 a credit para que siempre sea el monto exacto en pesos del subtotal. Al ser un campo calculado tenemos diferencias con la otra formula
                        line.subtotal_n2 = round(line.credit,2)
                        prueba = (line.subtotal_n2 / line.price_total)
                        prueba_2 = (line.price_total * .16)
                        line.impuestos_n2 = round((prueba * prueba_2),2)
                        line.monto_mxn_n2 = line.subtotal_n2 + line.impuestos_n2
                    
                    line.margen_n2 = line.subtotal_n2 - line.costo_n2

                else:
                    line.marca_n3 = ''
                    line.marca_n2 = ''
                    line.moneda_n3 = ''
                    line.moneda_n2 = ''
                    line.grupo_n3 = ''
                    line.grupo_n2 = ''
                    line.sub_grupo_n3 = ''
                    line.sub_grupo_n2 = ''
                    line.fecha_n3 = ''
                    line.fecha_n2 = ''
                    line.monto_mxn_n3 = 0
                    line.monto_mxn_n2 = 0
                    line.cliente_n3 = ''
                    line.cliente_n2 = ''
                    line.costo_n3 = ''
                    line.costo_n2 = ''
                    line.margen_n3 = ''
                    line.margen_n2 = ''
                    line.subtotal_n3 = 0
                    line.subtotal_n2 = 0
                    line.impuestos_n3 = 0
                    line.impuestos_n2 = 0
                    line.descuento_n3 = ''
                    line.descuento_n2 = ''
                    line.zona_venta_n3 = ''
                    line.zona_venta_n2 = ''
                    line.agente_venta_n3 = ''
                    line.agente_venta_n2 = ''
                    line.tipo_cliente_n3 = ''
                    line.tipo_cliente_n2 = ''
                    line.tipo_mercado_n3 = ''
                    line.tipo_mercado_n2 = ''
            except Exception as e:
                _logger.info(e)                
                _logger.info(line.name)