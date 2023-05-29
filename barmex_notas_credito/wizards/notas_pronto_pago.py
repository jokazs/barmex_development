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

    @api.onchange('fecha_final')
    @api.onchange('fecha_inicial')
    @api.depends('fecha_final')
    @api.depends('fecha_inicial')
    def calculo_notas_credito(self):
        print('Calculo de notas de credito')
        active_id = self.env.context.get('active_id')
        move_obj = self.env['account.move']
        nc_original = move_obj.browse(active_id)

        if not nc_original.partner_id:
            raise UserError('Primero seleccionar un cliente')
        if self.fecha_inicial > self.fecha_final:
            raise UserError('La fecha inicial no puede ser mayor a la fecha final')
        for borrar in self.facturas_ids:
            borrar.unlink()

        facturas = self.env['account.move'].search([('partner_id','=',nc_original.partner_id.id),
                                        ('type','=','out_invoice'),
                                        ('state','=','posted'),
                                        ('amount_residual','=',0),
                                        ('invoice_date', '>=',self.fecha_inicial), 
                                        ('invoice_date', '<=', self.fecha_final) ])
        pronto_pago_facturas = self.env['barmex.pronto_pago.facturas']

        for factura in facturas:
            pagos = self.env['account.payment'].search([('communication','=',factura.name),
                                        ('partner_type','=','customer'),
                                        ('payment_type','=','inbound'),
                                        ('state','=','posted') ])
            fecha_maxima = ''
            fecha_maxima = datetime.strptime("01-01-1990", "%d-%m-%Y").date()

            suma_pagos = 0
            for pago in pagos:
                print(pago.payment_date)
                if pago.payment_date >fecha_maxima:
                    fecha_maxima = pago.payment_date
                suma_pagos += pago.amount

            dias_pago = fecha_maxima - factura.invoice_date
            pronto_pago_facturas.create({'pronto_pago_id':self.id,
                                        'invoice_id':factura.id,
                                        'fecha_factura':factura.invoice_date,
                                        'pagos':suma_pagos,
                                        'saldo':factura.amount_residual,
                                        'fecha_ultimo_pago':fecha_maxima,
                                        'dias_pago':int(dias_pago.days) })

        return { 
            'type' : 'ir.actions.do_nothing'
         }

    def aplicar(self):
        print('Calculo de notas de credito')
        return True

class BarmexNotaProntoPagoFacturas(models.TransientModel):
    _name = "barmex.pronto_pago.facturas"
    _description = "Pronto pago facturas"

    pronto_pago_id = fields.Many2one('barmex.pronto_pago')
    invoice_id = fields.Many2one('account.move', string="Factura")

    fecha_factura = fields.Date('Fecha factura')
    pagos = fields.Float('Pagos factura')
    saldo = fields.Float('Saldo')
    fecha_ultimo_pago = fields.Date('Fecha ultimo pago')
    dias_pago = fields.Float('Dias de pago')

    descuento_aplicar = fields.Float('Monto descuento')
    motivo = fields.Char('Motivo descuento')
    aplicar = fields.Boolean('Aplicar')



class BarmexNotaProntoPago(models.TransientModel):
    _name = "barmex.bonificacion"
    _description = "Bonificacion"


    exception_msg = fields.Text(readonly=True)
    fecha_inicial = fields.Date('Fecha inicial', default =  fields.date.today())
    fecha_final = fields.Date('Fecha final', default =  fields.date.today())
    facturas_ids = fields.One2many('barmex.bonificacion.facturas', 'pronto_pago_id')

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

    @api.onchange('fecha_final')
    @api.onchange('fecha_inicial')
    @api.depends('fecha_final')
    @api.depends('fecha_inicial')
    def calculo_notas_credito(self):
        print('Calculo de notas de credito')
        active_id = self.env.context.get('active_id')
        move_obj = self.env['account.move']
        nc_original = move_obj.browse(active_id)

        if not nc_original.partner_id:
            raise UserError('Primero seleccionar un cliente')
        if self.fecha_inicial > self.fecha_final:
            raise UserError('La fecha inicial no puede ser mayor a la fecha final')
        for borrar in self.facturas_ids:
            borrar.unlink()

        facturas = self.env['account.move'].search([('partner_id','=',nc_original.partner_id.id),
                                        ('type','=','out_invoice'),
                                        ('state','=','posted'),
                                        ('amount_residual','=',0),
                                        ('invoice_date', '>=',self.fecha_inicial), 
                                        ('invoice_date', '<=', self.fecha_final) ])
        bonificacion_facturas = self.env['barmex.bonificacion.facturas']

        for factura in facturas:
            pagos = self.env['account.payment'].search([('communication','=',factura.name),
                                        ('partner_type','=','customer'),
                                        ('payment_type','=','inbound'),
                                        ('state','=','posted') ])
            fecha_maxima = ''
            fecha_maxima = datetime.strptime("01-01-1990", "%d-%m-%Y").date()

            suma_pagos = 0
            for pago in pagos:
                print(pago.payment_date)
                if pago.payment_date >fecha_maxima:
                    fecha_maxima = pago.payment_date
                suma_pagos += pago.amount

            dias_pago = fecha_maxima - factura.invoice_date
            bonificacion_facturas.create({'bonificacion_id':self.id,
                                        'invoice_id':factura.id,
                                        'fecha_factura':factura.invoice_date,
                                        'pagos':suma_pagos,
                                        'saldo':factura.amount_residual,
                                        'fecha_ultimo_pago':fecha_maxima,
                                        'dias_pago':int(dias_pago.days) })

        return { 
            'type' : 'ir.actions.do_nothing'
         }

    def aplicar(self):
        print('Calculo de notas de credito')
        return True

class BarmexNotaProntoPagoFacturas(models.TransientModel):
    _name = "barmex.bonificacion.facturas"
    _description = "bonificacion facturas"

    bonificacion_id = fields.Many2one('barmex.bonificacion')
    invoice_id = fields.Many2one('account.move', string="Factura")

    fecha_factura = fields.Date('Fecha factura')
    pagos = fields.Float('Pagos factura')
    saldo = fields.Float('Saldo')
    fecha_ultimo_pago = fields.Date('Fecha ultimo pago')
    dias_pago = fields.Float('Dias de pago')

    descuento_aplicar = fields.Float('Monto descuento')
    motivo = fields.Char('Motivo descuento')
    aplicar = fields.Boolean('Aplicar')