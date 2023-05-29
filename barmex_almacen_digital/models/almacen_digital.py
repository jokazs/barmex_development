# from dataclasses import field
import string
from odoo import models,fields
from odoo.exceptions import UserError

class AlmacenDigital(models.Model):
    _name = "almacen.digital"
    _description = 'guardar las facturas desde el Web Service del SAT'
    
    #quita el borrado
    def unlink(self):
        raise UserError('No es posible borrar')
        return True

    def copy(self):
        raise UserError('No es posible copiar')
        return True

    def _compute_calculo_cantidad_pagada(self):
        for line in self:
            line.saldo = 0
            suma = 0
            folios = line.pagos_ad_ids
            #for lines in folios:
            #    if lines.state != 'draft':
            #        suma += lines.cantidad_pagada
            cantidad_pagada = line.cantidad_pagada

            if cantidad_pagada >= line.total and line.total > 0:   
                line.status_folio='pagado'
                if cantidad_pagada > line.total:
                    line.saldo = 0
                else:
                    line.saldo = line.total - cantidad_pagada
            elif cantidad_pagada > 0:
                line.status_folio='parcialmente'
                line.saldo = line.total - cantidad_pagada
            elif cantidad_pagada == 0:
                line.status_folio = 'no_asignado'

    def _compute_vacio(self):
        suma = 0
        for line in self:
            for folios in line.pagos_ad_ids:
                if folios:
                    suma = suma + 1
            if suma != 0:
                line.status_folio_check = True
            else:
                line.status_folio_check = False
            



    name = fields.Char(string="UUID")
    fecha_comprobante = fields.Date(string='Fecha')
    serie = fields.Char(string="Serie")
    folio = fields.Char(string="Folio")
    rfc_emisor = fields.Char(string="RFC")
    rfc_receptor = fields.Char(string="RFC Receptor")
    nombre_emisor = fields.Char(string="Nombre")
    moneda = fields.Char(string="Moneda")
    tipo_de_cambio = fields.Float(string="Tipo de Cambio")
    total = fields.Float(string="Total")
    forma_de_pago = fields.Integer(string="Forma de pago")
    compra_gasto = fields.Selection(selection=[('compra', 'Compra'),('gasto', 'Gasto')], string='Compra/Gasto', default='gasto')
    productos_ids = fields.One2many("almacen.digital_productos","factura_id","Productos")
    tipo_de_comprobante = fields.Char(string="Tipo de comprobante")
    impuestos = fields.Float(string="Impuestos")

    status_folio = fields.Selection([('no_asignado', 'No Asignado'),('parcialmente', 'Asignado Parcialmente'),('pagado', 'Pagado')],string='Status',default='no_asignado')

    pagos_ad_ids = fields.Many2many('account.payment','account_payment_id_almacen_digital_id','almacen_digital_id','account_payment_id',string='Almacen Digital',stored=True)
    move_ids = fields.Many2many('account.move','account_move_id_almacen_digital_id','almacen_digital_id','account_move_id',string='Almacen Digital',stored=True)

    cantidad_pagada = fields.Float('Cantidad pagada')
    saldo = fields.Float('Saldo', compute='_compute_calculo_cantidad_pagada')
    notas = fields.Text(string="Notas")

    status_folio_check = fields.Boolean('check vacio', default=False, compute='_compute_vacio')

    _order = "fecha_comprobante desc"

class AlmacenDigitalProductos(models.Model):
    _name = "almacen.digital_productos"
    _description = 'guardar productos'

    #quita el borrado
    def unlink(self):
        raise UserError('No es posible borrar')
        return True

    def copy(self):
        raise UserError('No es posible copiar')
        return True

    name = fields.Char("Producto")
    cantidad = fields.Float("Cantidad")
    precio = fields.Float("Precio")
    factura_id = fields.Many2one("almacen.digital","Factura")
    clave_prod_serv = fields.Integer("Clave productos y servicios")
    clave_unidad = fields.Char("Clave unidades")
    uuid = fields.Char("UUID")

class AlmacenDigitalSincronizacion(models.Model):
    _name = 'almacen.digital_sincronizacion'
    _description = 'almacen.digital_sincronizacion'
    

    api = fields.Char("Api")
    fecha_sincronizacion = fields.Date(string='Fecha Sincronizacion')
    status = fields.Char("Status")