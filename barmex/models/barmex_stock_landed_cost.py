from odoo import models, fields, api, _

class stock_landed_cost_custom(models.Model):
    _inherit = 'stock.landed.cost'

    pedimento_id = fields.Many2one('barmex.foreign.trade', string='Pedimento')

    factura_aduanal = fields.Char(string='Factura Aduanal')

    facturas_costes_ids = fields.One2many('facturas.costes', 'costes_id', 'Facturas')

    facturas_gastos_ids = fields.One2many('facturas.gastos', 'gastos_id', 'Facturas gastos')

    # @api.onchange('facturas_costes_ids')
    # def change_facturas_costes(self):
    #     print("Está cambiando de factura")
    #     print(self.facturas_costes_ids.name)
    #     for cos in self.cost_lines:
    #         cos.product_id = 370438
    #         cos.split_method = 'by_quantity'
    #         cos.price_unit = self.pedimento_id.freight
    #     print("-")

    def button_calculo_costo(self):
        print("Haciendo calculos de pedimentos")
        producto_flete = self.pedimento_id.freight
        producto_otros = self.pedimento_id.other
        producto_seguros = self.pedimento_id.insurance
        productos = []
        vals1 = {
                'cost_id': self.id,
                'name': 'flete',
                'product_id': 370437,
                'price_unit': producto_flete,
                'account_id': 19,
                'split_method': 'by_quantity'
            }
        productos.append(vals1)
        vals2 = {
                'cost_id': self.id,
                'name': 'otros',
                'product_id': 370440,
                'price_unit': producto_otros,
                'account_id': 19,
                'split_method': 'by_quantity'
            }
        productos.append(vals2)
        vals3 = {
                'cost_id': self.id,
                'name': 'seguros',
                'product_id': 370438,
                'price_unit': producto_seguros,
                'account_id': 19,
                'split_method': 'by_quantity'
            }
        productos.append(vals3)

        self.env['stock.landed.cost.lines'].create(productos)

        prueba = self.env['stock.picking'].search([('foreign_trade_id', '=', self.pedimento_id.id)])
        print("--")
        print(prueba)
        for pick in prueba:
            self.picking_ids = pick
        print("--")

        print("Haciendo calculos")
        # print(self.facturas_costes_ids.name)
        l_facturas = self.facturas_costes_ids.name
        qty_facturas = len(l_facturas)
        suma_total = 0
        print("Número de Facturas")
        print(qty_facturas)
        
        for fac1 in self.facturas_costes_ids:
            tipo_cambio_factura1 = fac1.name.barmex_currency_rate
            moneda_factura1 = fac1.name.currency_id.name
            for prod in fac1.name.invoice_line_ids:
                suma1 = 0
                suma1 = prod.price_unit * prod.quantity
                if moneda_factura1 == "MXN":
                    suma1 = suma1 * tipo_cambio_factura1
                suma_total += suma1
            
        for fac in self.facturas_costes_ids:
            suma_factura = 0
            
            tipo_cambio_factura = fac.name.barmex_currency_rate
            print("Tipo de cambio")
            print(tipo_cambio_factura)
            moneda_factura = fac.name.currency_id.name
            print("Moneda")
            print(moneda_factura)
            
            print("Total por factura: ")
            for prod in fac.name.invoice_line_ids:
                suma = 0
                suma = prod.price_unit * prod.quantity
                if moneda_factura == "MXN":
                    suma = suma * tipo_cambio_factura
                suma_factura += suma
            suma_total_factura = suma_factura
            print(suma_total_factura)
            fac.productos = suma_total_factura

            print("Porcentaje de factura")
            porcentaje_factura=suma_total_factura*100/suma_total
            print(porcentaje_factura)

            l_productos = fac.name.invoice_line_ids
            qty_productos = len(l_productos)
            print("Cantidad de productos por factura")
            print(qty_productos)

            suma_flete = 0
            suma_otros = 0
            suma_seguros = 0
            suma_tva = 0
            suma_va = 0
            suma_dta = 0
            suma_igi = 0
            suma_iva = 0
            suma_total_final = 0

            for prod in fac.name.invoice_line_ids:
                print("Subtotal por producto")
                subtotal_producto = 0
                subtotal_producto = prod.price_unit * prod.quantity
                if moneda_factura == "MXN":
                    subtotal_producto = subtotal_producto * tipo_cambio_factura
                print(subtotal_producto)

                print("Porcentaje de producto")
                porcentaje_producto=subtotal_producto*100/suma_total_factura
                print(porcentaje_producto)
                
                print("Flete correspondiente por producto")
                flete_producto = (porcentaje_producto/100)*(self.pedimento_id.freight * (porcentaje_factura/100))
                print(flete_producto)
                suma_flete += flete_producto

                print("Otros correspondiente por producto")
                otros_producto = (porcentaje_producto/100)*(self.pedimento_id.other * (porcentaje_factura/100))
                print(otros_producto)
                suma_otros += otros_producto

                print("Seguros correspondiente por producto")
                seguros_producto = (porcentaje_producto/100)*(self.pedimento_id.insurance * (porcentaje_factura/100))
                print(seguros_producto)
                suma_seguros += seguros_producto

                print("Total Valor Aduana por producto")
                total_va_producto = subtotal_producto + flete_producto + otros_producto + seguros_producto
                print(total_va_producto)
                suma_tva += total_va_producto

                print("Valor Aduana por producto")
                va_producto = total_va_producto * self.pedimento_id.exchange_rate
                print(va_producto)
                suma_va += va_producto

                print("Derecho de Trámite Aduanal por producto")
                derecho_ta_producto = va_producto * 0.008
                print(derecho_ta_producto)
                suma_dta += derecho_ta_producto

                print("Impuesto General de Importación por producto")
                igi_producto = va_producto * (prod.product_id.product_tmpl_id.tasa_advalorem_igi/100)
                print(igi_producto)
                suma_igi += igi_producto

                print("IVA por producto")
                iva_producto = (va_producto + derecho_ta_producto + igi_producto)*0.16
                print(iva_producto)
                suma_iva += iva_producto

                print("Total por producto")
                total_producto = derecho_ta_producto + igi_producto + iva_producto
                print(total_producto)
                suma_total_final += total_producto

            fac.flete = suma_flete
            fac.otros = suma_otros
            fac.seguro = suma_seguros
            fac.total_valor_aduana = suma_tva
            fac.valor_aduana = suma_va
            fac.derecho_de_tramite_aduanal = suma_dta
            fac.igi = suma_igi
            fac.iva = suma_iva
            fac.total = suma_total_final

    # #función del botón calcular de costes adicionales
    # def compute_landed_cost(self):
    #     AdjustementLines = self.env['stock.valuation.adjustment.lines']
    #     AdjustementLines.search([('cost_id', 'in', self.ids)]).unlink()

    #     towrite_dict = {}
    #     for cost in self.filtered(lambda cost: cost._get_targeted_move_ids()):
    #         rounding = cost.currency_id.rounding
    #         total_qty = 0.0
    #         total_cost = 0.0
    #         total_weight = 0.0
    #         total_volume = 0.0
    #         total_line = 0.0
    #         all_val_line_values = cost.get_valuation_lines()
    #         for val_line_values in all_val_line_values:
    #             for cost_line in cost.cost_lines:
    #                 val_line_values.update({'cost_id': cost.id, 'cost_line_id': cost_line.id})
    #                 self.env['stock.valuation.adjustment.lines'].create(val_line_values)
    #             total_qty += val_line_values.get('quantity', 0.0)
    #             total_weight += val_line_values.get('weight', 0.0)
    #             total_volume += val_line_values.get('volume', 0.0)

    #             former_cost = val_line_values.get('former_cost', 0.0)
    #             # round this because former_cost on the valuation lines is also rounded
    #             total_cost += cost.currency_id.round(former_cost)

    #             total_line += 1

    #         for line in cost.cost_lines:
    #             value_split = 0.0
    #             for valuation in cost.valuation_adjustment_lines:
    #                 value = 0.0
    #                 if valuation.cost_line_id and valuation.cost_line_id.id == line.id:
    #                     if line.split_method == 'by_quantity' and total_qty:
    #                         per_unit = (line.price_unit / total_qty)
    #                         value = valuation.quantity * per_unit
    #                     elif line.split_method == 'by_weight' and total_weight:
    #                         per_unit = (line.price_unit / total_weight)
    #                         value = valuation.weight * per_unit
    #                     elif line.split_method == 'by_volume' and total_volume:
    #                         per_unit = (line.price_unit / total_volume)
    #                         value = valuation.volume * per_unit
    #                     elif line.split_method == 'equal':
    #                         value = (line.price_unit / total_line)
    #                     elif line.split_method == 'by_current_cost_price' and total_cost:
    #                         per_unit = (line.price_unit / total_cost)
    #                         value = valuation.former_cost * per_unit
    #                     else:
    #                         value = (line.price_unit / total_line)

    #                     if rounding:
    #                         value = tools.float_round(value, precision_rounding=rounding, rounding_method='UP')
    #                         fnc = min if line.price_unit > 0 else max
    #                         value = fnc(value, line.price_unit - value_split)
    #                         value_split += value

    #                     if valuation.id not in towrite_dict:
    #                         towrite_dict[valuation.id] = value
    #                     else:
    #                         towrite_dict[valuation.id] += value
    #     for key, value in towrite_dict.items():
    #         AdjustementLines.browse(key).write({'additional_landed_cost': value})
    #     return True



class facturas_costes(models.Model):
    _name = 'facturas.costes'
    _description = 'Barmex Facturas Costes'

    costes_id = fields.Many2one('stock.landed.cost', 'Facturas Costes', ondelete='cascade')

    name = fields.Many2one('account.move', 'Facturas Costes')

    productos = fields.Float('Valor Mercancia', digits=(12,2))
    flete = fields.Float('Flete', digits=(12,2))
    otros = fields.Float('Otros', digits=(12,2))
    seguro = fields.Float('Seguro', digits=(12,2))
    total_valor_aduana = fields.Float('Total Valor Aduana', digits=(12,2))
    valor_aduana = fields.Float('Valor Aduana', digits=(12,2))
    derecho_de_tramite_aduanal = fields.Float('Derecho Trámite Aduanal', digits=(12,2))
    igi = fields.Float('TASA ADVALOREM (IGI)', digits=(12,2))
    iva = fields.Float('IVA', digits=(12,2))
    total = fields.Float('Total', digits=(12,2))


class facturas_gastos(models.Model):
    _name = 'facturas.gastos'
    _description = 'Barmex Facturas Gastos'

    gastos_id = fields.Many2one('stock.landed.cost', 'Facturas Costes', ondelete='cascade')

    name = fields.Many2one('account.move', 'Facturas Gastos')

    notas = fields.Char('Notas')
    monto_mxn = fields.Float('Monto MXN', digits=(12,2))
