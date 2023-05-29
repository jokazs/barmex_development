from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError, Warning
from datetime import datetime

class BarmexNotaProntoPago(models.TransientModel):
    _name = "barmex.pronto_pago"
    _description = "Pronto pago"


    exception_msg = fields.Text(readonly=True)
    fecha_inicial = fields.Date('Fecha inicial', default =  fields.date.today())
    fecha_final = fields.Date('Fecha final', default =  fields.date.today())
    facturas_ids = fields.One2many('barmex.pronto_pago.facturas', 'pronto_pago_id')

    def create_wizard(self): 

        wizard_id = self.create({})
        wizard_id.calculo_notas_credito()
        # YOUR POPULATION CODE HERE     
        return { 
            'name': 'Notas de credito Pronto pago', 
            'view_type': 'form', 
            'view_mode': 'form', 
            'res_model': 'barmex.pronto_pago', 
            'res_id': wizard_id.id, 
            'type': 'ir.actions.act_window', 
            'target': 'new', 
            'context': self.env.context 
        }


    def calculo_notas_credito(self):
        active_id = self.env.context.get('active_id')
        move_obj = self.env['account.move']
        nc_original = move_obj.browse(active_id)

        if not nc_original.partner_id:
            raise UserError('Primero seleccionar un cliente')
        if not nc_original.state == 'draft':
            raise UserError('El estado de la nota de crédito es distinto de borrador')

        for borrar in self.facturas_ids:
            borrar.unlink()

        facturas = self.env['account.move'].search([('partner_id','=',nc_original.partner_id.id),
                                        ('type','=','out_invoice'),
                                        ('state','=','posted'),
                                        ('amount_residual','>',0) ])
        pronto_pago_facturas = self.env['barmex.pronto_pago.facturas']

        for factura in facturas:
            print(factura.name)
            domain = [('partner_id','=',nc_original.partner_id.id),
                        ('partner_type','=','customer'),
                        ('payment_type','=','inbound'),
                        ('state','=','posted') ]
            print(domain)
            pagos = self.env['account.payment'].search(domain)
            fecha_maxima = ''
            fecha_maxima = datetime.strptime("01-01-1990", "%d-%m-%Y").date()

            #Este codigo es super ineficiente, hay que buscar una mejor forma de ligar pagos con facturas
            suma_pagos = 0
            for pago in pagos:
                for invoice in pago.invoice_ids:
                    if invoice.name == factura.name:
                        if pago.payment_date >fecha_maxima:
                            fecha_maxima = pago.payment_date
                        suma_pagos += pago.barmex_used_amount_cur

            

            #Si la factura no tiene pagos asociados detectados ir al siguiente movimiento
            if suma_pagos == 0:
                fecha_maxima = None
                dias_pago = 0
                descuento = 0
                aplicar = False
            else:
                dias_pago = (fecha_maxima - factura.invoice_date).days
                cat_pp_aplica = self.env['barmex.pronto_pago_catalogo'].search([('plazo_pago_id','=',factura.invoice_payment_term_id.id)])
                descuento = 0
                aplicar = False

                if cat_pp_aplica:
                    dias_primer_rango = cat_pp_aplica.dias_pp
                    dias_segundo_rango = cat_pp_aplica.dias_pp_seg
                    if dias_pago <= dias_primer_rango:
                        descuento = suma_pagos * (cat_pp_aplica.dias_pp_por/100)
                        aplicar = True

                    if dias_pago > dias_primer_rango and dias_pago <= dias_segundo_rango:
                        descuento = suma_pagos * (cat_pp_aplica.dias_pp_seg_por/100)
                        aplicar = True


            datos = {'pronto_pago_id':self.id,
                                        'invoice_id':factura.id,
                                        'currency_id':factura.currency_id.id,
                                        'fecha_factura':factura.invoice_date,
                                        'pagos':suma_pagos,
                                        'saldo':factura.amount_residual,
                                        'fecha_ultimo_pago':fecha_maxima,
                                        'descuento_aplicar': descuento,
                                        'aplicar' : aplicar,
                                        'dias_pago':dias_pago }

            pronto_pago_facturas.create(datos)
            

        return { 
            'type' : 'ir.actions.do_nothing'
         }

    def aplicar(self):
        active_id = self.env.context.get('active_id')
        move_line = self.env['account.move.line']
        move_obj = self.env['account.move']
        nc_original = move_obj.browse(active_id)
        empresa = self.env.company
        if not empresa.producto_pp_id.id:
            raise UserError('Producto utilizado para pronto pago no configurado en Ajustes')

        if not nc_original.journal_id.nota_credito_cuenta.id:
            raise UserError('Cuenta contable de notas de crédito no definida en el Diario')

        cfdi_relacionado = []
        for factura_descuento in self.facturas_ids:
            if factura_descuento.aplicar:
                #check_move_validity se utiliza porque al agregar un nuevo registro se descuadra el total, si se activa este check da error
                invoice_line = move_line.with_context(check_move_validity=False, noonchange=True).create([{
                    'product_id':empresa.producto_pp_id.id,
                    'move_id': active_id,
                    'quantity': 1,
                    'price_unit': factura_descuento.descuento_aplicar,
                    #'currency_id': factura_descuento.invoice_id.currency_id.id,
                    'partner_id':factura_descuento.invoice_id.partner_id.id,
                    'account_id':nc_original.journal_id.nota_credito_cuenta.id,
                    'account_internal_type':'other',
                    'credit': 0,
                    'debit': factura_descuento.descuento_aplicar,
                    'balance': factura_descuento.descuento_aplicar,
                    'price_subtotal': factura_descuento.descuento_aplicar,
                    'price_total': factura_descuento.descuento_aplicar,
                    'name': f'Descuento pronto pago: {factura_descuento.invoice_id.name}',
                    'move_name': f'Descuento pronto pago: {factura_descuento.invoice_id.name}',
                    'ref':factura_descuento.invoice_id.name,
                    'exclude_from_invoice_tab': False,
                    'is_landed_costs_line': False,
                    'l10n_mx_edi_qty_umt':0,
                    'tax_exigible': False
                    }])
                #Al activar el on_change los precios se van a 0, por eso esta parte
                invoice_line._onchange_product_id()
                invoice_line._onchange_price_subtotal()
                invoice_line.write({'price_subtotal': factura_descuento.descuento_aplicar,
                    'price_total': factura_descuento.descuento_aplicar,
                    'price_unit': factura_descuento.descuento_aplicar,
                    'name': f'Descuento pronto pago: {factura_descuento.invoice_id.name}'})
                cfdi_relacionado.append(f'01|{factura_descuento.invoice_id.l10n_mx_edi_cfdi_uuid}')

        nc_original.with_context(check_move_validity=False)._recompute_dynamic_lines(recompute_all_taxes= True)
        try:
            if nc_original.l10n_mx_edi_origin:
                relacionado = '|'.join(cfdi_relacionado)
                nc_original.l10n_mx_edi_origin = f"{nc_original.l10n_mx_edi_origin},{relacionado}"
            else:
                nc_original.l10n_mx_edi_origin = '|'.join(cfdi_relacionado)
        except:
            print('Error al crear CFDIs relacionados')
        return True

class BarmexNotaProntoPagoFacturas(models.TransientModel):
    _name = "barmex.pronto_pago.facturas"
    _description = "Pronto pago facturas"

    pronto_pago_id = fields.Many2one('barmex.pronto_pago')
    invoice_id = fields.Many2one('account.move', string="Factura")
    currency_id = fields.Many2one('res.currency', string="Moneda")
    fecha_factura = fields.Date('Fecha factura')
    pagos = fields.Float('Pagos factura')
    saldo = fields.Float('Saldo')
    fecha_ultimo_pago = fields.Date('Fecha ultimo pago')
    dias_pago = fields.Float('Dias de pago')

    descuento_aplicar = fields.Float('Monto descuento')
    motivo = fields.Char('Motivo descuento')
    aplicar = fields.Boolean('Aplicar')



class BarmexBonificacionPago(models.TransientModel):
    _name = "barmex.bonificacion"
    _description = "Bonificacion"


    exception_msg = fields.Text(readonly=True)
    fecha_inicial = fields.Date('Fecha inicial', default =  fields.date.today())
    fecha_final = fields.Date('Fecha final', default =  fields.date.today())
    facturas_ids = fields.One2many('barmex.bonificacion.facturas', 'bonificacion_id')

    def create_wizard(self): 

        wizard_id = self.create({})
        wizard_id.calculo_notas_credito()
        # YOUR POPULATION CODE HERE 

        return { 
            'name': 'Notas de credito Bonificacion', 
            'view_type': 'form', 
            'view_mode': 'form', 
            'res_model': 'barmex.bonificacion', 
            'res_id': wizard_id.id, 
            'type': 'ir.actions.act_window', 
            'target': 'new', 
            'context': self.env.context 
        }


    def calculo_notas_credito(self):
        active_id = self.env.context.get('active_id')
        move_obj = self.env['account.move']
        nc_original = move_obj.browse(active_id)

        if not nc_original.partner_id:
            raise UserError('Primero seleccionar un cliente')
        for borrar in self.facturas_ids:
            borrar.unlink()

        facturas = self.env['account.move'].search([('partner_id','=',nc_original.partner_id.id),
                                        ('type','=','out_invoice'),
                                        ('state','=','posted'),
                                        ('amount_residual','>',0) ])
        bonificacion_facturas = self.env['barmex.bonificacion.facturas']

        for factura in facturas:

            #CHECAR CAMPO COMMUNICATION
            pagos = self.env['account.payment'].search([('communication','=',factura.name),
                                        ('partner_type','=','customer'),
                                        ('payment_type','=','inbound'),
                                        ('state','=','posted') ])

            suma_bonif = 0
            for producto in factura.invoice_line_ids:
                suma_bonif += producto.lco_price_diff

            bonificacion_facturas.create({'bonificacion_id':self.id,
                                        'invoice_id':factura.id,
                                        'currency_id':factura.currency_id.id,
                                        'fecha_factura':factura.invoice_date,
                                        'saldo':factura.amount_residual,
                                        'amount_total':factura.amount_total,
                                        'descuento_aplicar':suma_bonif})

        return { 
            'type' : 'ir.actions.do_nothing'
         }

    def aplicar(self):
        active_id = self.env.context.get('active_id')
        move_line = self.env['account.move.line']
        move_obj = self.env['account.move']
        nc_original = move_obj.browse(active_id)
        empresa = self.env.company
        if not empresa.producto_bon_id.id:
            raise UserError('Producto utilizado para bonificaciones no configurado en Ajustes')

        if not nc_original.journal_id.nota_credito_cuenta.id:
            raise UserError('Cuenta contable de notas de crédito no definida en el Diario')
        cfdi_relacionado = []   
        for factura_descuento in self.facturas_ids:
            if factura_descuento.aplicar:
                #check_move_validity se utiliza porque al agregar un nuevo registro se descuadra el total, si se activa este check da error
                invoice_line = move_line.with_context(check_move_validity=False, noonchange=True).create([{
                    'product_id':empresa.producto_bon_id.id,
                    'move_id': active_id,
                    'quantity': 1,
                    'price_unit': factura_descuento.descuento_aplicar,
                    #'currency_id': factura_descuento.invoice_id.currency_id.id,
                    'partner_id':factura_descuento.invoice_id.partner_id.id,
                    'account_id':nc_original.journal_id.nota_credito_cuenta.id,
                    'account_internal_type':'other',
                    'credit': 0,
                    'debit': factura_descuento.descuento_aplicar,
                    'balance': factura_descuento.descuento_aplicar,
                    'price_subtotal': factura_descuento.descuento_aplicar,
                    'price_total': factura_descuento.descuento_aplicar,
                    'name': f'Descuento Bonificaciones: {factura_descuento.invoice_id.name}',
                    'move_name': f'Descuento Bonificaciones: {factura_descuento.invoice_id.name}',
                    'ref':factura_descuento.invoice_id.name,
                    'exclude_from_invoice_tab': False,
                    'is_landed_costs_line': False,
                    'l10n_mx_edi_qty_umt':0,
                    'tax_exigible': False
                    }])
                #Al activar el on_change los precios se van a 0, por eso esta parte
                invoice_line._onchange_product_id()
                invoice_line._onchange_price_subtotal()
                invoice_line.write({'price_subtotal': factura_descuento.descuento_aplicar,
                    'price_total': factura_descuento.descuento_aplicar,
                    'price_unit': factura_descuento.descuento_aplicar,
                    'name': f'Descuento Bonificaciones: {factura_descuento.invoice_id.name}'})
                cfdi_relacionado.append(f'01|{factura_descuento.invoice_id.l10n_mx_edi_cfdi_uuid}')

        nc_original.with_context(check_move_validity=False)._recompute_dynamic_lines(recompute_all_taxes= True)
        try:
            if nc_original.l10n_mx_edi_origin:
                relacionado = '|'.join(cfdi_relacionado)
                nc_original.l10n_mx_edi_origin = f"{nc_original.l10n_mx_edi_origin},{relacionado}"
            else:
                nc_original.l10n_mx_edi_origin = '|'.join(cfdi_relacionado)
        except:
            print('Error al crear CFDIs relacionados')
        return True

class BarmexNotaBonificacionFacturas(models.TransientModel):
    _name = "barmex.bonificacion.facturas"
    _description = "bonificacion facturas"

    bonificacion_id = fields.Many2one('barmex.bonificacion')
    invoice_id = fields.Many2one('account.move', string="Factura")
    currency_id = fields.Many2one('res.currency', string="Moneda")
    amount_total = fields.Float('Total factura')
    fecha_factura = fields.Date('Fecha factura')
    pagos = fields.Float('Pagos factura')
    saldo = fields.Float('Saldo')
    fecha_ultimo_pago = fields.Date('Fecha ultimo pago')
    dias_pago = fields.Float('Dias de pago')

    descuento_aplicar = fields.Float('Monto descuento')
    motivo = fields.Char('Motivo descuento')
    aplicar = fields.Boolean('Aplicar')