import string
from odoo import _, api, fields, models
from odoo.tools.misc import clean_context
from datetime import datetime
from odoo.exceptions import UserError

#stock/models/stock_rule.py

class abastecimientos_log(models.Model):
    _name = 'abastecimientos.log'
    _description= 'Abastecimientos Log'
    name = fields.Char('Grupo abastecimiento', size=120)
    fecha_abastecimiento = fields.Date('Fecha ejecucion',  default=datetime.today())
    estado = fields.Char('Estado', size=60)
    marca = fields.Many2one('product.category', string='Marca', required=True)
    route_ids = fields.Many2many(
        'stock.location.route', string='Preferred Routes',
        help="Apply specific route(s) for the replenishment instead of product's default routes.")
    productos_ids = fields.One2many('abastecimientos.log.productos', 'abastecimiento_id', string="Productos")

class abastecimientos_log_productos(models.Model):
    _name = 'abastecimientos.log.productos'
    _description= 'Abastecimientos Log Productos'
    name = fields.Many2one('product.product', string='Producto')
    log = fields.Text('Log')
    almacen = fields.Many2one('stock.warehouse', string="Almacen")
    abastecimiento_id = fields.Many2one('abastecimientos.log', string='Abastecimiento')

class StockSchedulerCompute(models.TransientModel):
    _name = "stock.scheduler.compute"
    _description = 'Run Scheduler Manually'
    _inherit = "stock.scheduler.compute"
   
    almacen = fields.Many2one('stock.warehouse', string="Almacen")
    marca = fields.Many2one('product.category', string='Marca', required=True)
    date_planned = fields.Date('Scheduled Date',  default=datetime.today())
    route_ids = fields.Many2many(
        'stock.location.route', string='Preferred Routes',
        help="Apply specific route(s) for the replenishment instead of product's default routes.",
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    company_id = fields.Many2one('res.company')

    def abastecimientos(self):
        #Si almacen esta vacio necesitamos iterar sobre todos los almacenes. (MUY TARDADO - MUY)
        #Fix: dejar seleccionar una lista de almacenes. Many2One pero que sea many2many
        #En el codigo iterar sobre esa lista de almacenes.
        #Opción B: Habilitar un booleano que sea seleccionar todos los almacenes, si es TRUE entonces hacer una busqueda de almacenes principales harcodeados.
        #self.env['stock.warehouse'].search(
        #            [('name', 'in', ('lista de almacnes principales...'))]
        #        ).with_context(location=self.almacen.lot_stock_id.id)

        #   Revisar que almacen tiene stock.warehouse.orderpoint para ese producto.
        # prueba = self.env['stock.warehouse.orderpoint'].search(
        #            [('product_id', '=', producto.id)]
        #        )
        # print(prueba)
        #Buscar productos que pertenezcan a esa categoria

        abastecimientos = self.env['abastecimientos.log'].create({'name':f'{datetime.today()} - {self.marca.name} - Ejecucion manual {self.env.user.name}',
            'estado':'iniciado', 'marca': self.marca.id})

        if self.almacen:            
            almacen_ids = [self.almacen.id]
        else:
            productos_ids_sc = self.env['product.product'].search(
                        [('categ_id', '=', self.marca.id)]
                    )
            print(productos_ids_sc)
            print("--")
            ids_productos = [producto.id for producto in productos_ids_sc]
            print(ids_productos)
            print("--")
            orderpoints = self.env['stock.warehouse.orderpoint'].search(
                        [('product_id', 'in', ids_productos)]
                    )
            print(orderpoints)
            almacen_ids = list(set([almacen.warehouse_id.id for almacen in orderpoints]))
            print("+-+-+-+-+-+-+-+-+")
            print(almacen_ids)
        for almacen_id in almacen_ids:
            print("Almacen id ¿Qué es")
            print(almacen_id)
            almacen = self.env['stock.warehouse'].search(
                        [('id', '=', almacen_id)],limit=1
                    )
            productos_ids = self.env['product.product'].search(
                        [('categ_id', '=', self.marca.id)]
                    ).with_context(location=almacen.lot_stock_id.id)
            if productos_ids:
                #productos = self.env['product.product'].browse(productos_ids)

                for producto in productos_ids:
                    abastecimientos_producto = self.env['abastecimientos.log.productos'].create({'name':producto.id,
                            'almacen':almacen_id, 'abastecimiento_id': abastecimientos.id, 'log':'Iniciando'})
                    uom_reference = producto.uom_id
                    #Busca por cada producto el stock max /min configurado
                    max_min_cant = self.env['stock.warehouse.orderpoint'].search(
                        [('warehouse_id', '=', almacen_id),('product_id', '=', producto.id)]
                    )
                    # print("Buscando las reglas de abastecimiento")
                    # print(producto.default_code)
                    print("Almacen id ¿Qué es")
                    print(almacen_id)
                    max_min_cant_count = self.env['stock.warehouse.orderpoint'].search_count(
                        [('warehouse_id', '=', almacen_id),('product_id', '=', producto.id)]
                    )
                    
                    # print(f'PRODUCTO {producto.default_code}')
                    # print(f'{max_min_cant_count}')
                    #No funciona, checar si el resultado de Search esta vacio
                    if max_min_cant_count > 0:
                        # print('PRODUCTO MAYOR A 0')
                        if producto.free_qty <= max_min_cant.product_min_qty:
                            print(f'PRODUCTO {producto.default_code} NECESITA MAS STOCK. MINIMO: {max_min_cant.product_min_qty}')
                            abastecimientos_producto.log = f'PRODUCTO {producto.default_code} NECESITA MAS STOCK. MINIMO: {max_min_cant.product_min_qty}'
                            try:
                                self.env['procurement.group'].with_context(clean_context(self.env.context)).run([
                                    self.env['procurement.group'].Procurement(
                                        producto,
                                        max_min_cant.product_max_qty - producto.free_qty, #OBTENER ESTE NUMERO
                                        uom_reference,
                                        almacen.lot_stock_id,  # Location
                                        _(f"{almacen.name} abastecimiento"),  # Name
                                        _(f"{almacen.name} Stock MAX MIN"),  # Origin
                                        almacen.company_id,
                                        self._prepare_run_abastecimientos(max_min_cant,almacen)  # Values
                                    )
                                ])
                                print("YA CREE LA PRETICIÓN DE PRESUPUESTO")
                            except UserError as error:
                                #raise UserError(error)
                                abastecimientos_producto.log = f'Error: {error}'

                        else:
                            abastecimientos_producto.log = f'Regla no ejecutada porque se detecto Stock suficiente para el producto. Valores: \n producto.free_qty: {producto.free_qty} \n max_min_cant.product_min_qty: {max_min_cant.product_min_qty}'
                            
                    else:
                        print('PRODUCTO IGUAL A 0')
                        abastecimientos_producto.log = f'El producto {producto.default_code} no tiene configuradas reglas de stock maximo y minimo en el almacen {almacen.name}'
                        #raise UserError(f'El producto {producto.default_code} no tiene configuradas reglas de stock maximo y minimo en el almacen {self.almacen.name}')
        abastecimientos.estado = 'Finalizado'
        return {
            'type': 'ir.actions.client',
            'tag': 'reload', #display_notification
            'params': {
                'message': 'Proceso de planificador finalizado, ir al menu de compras para revisar las solicitudes',
                'type': 'success',
                'sticky': False,
            }
        }

    def _prepare_run_abastecimientos(self, orderpoint= False, warehouse_id=1):
        
        replenishment = self.env['procurement.group'].create({})

        values = {
            'warehouse_id': warehouse_id,
            'route_ids': self.route_ids,
            'date_planned': self.date_planned,
            'group_id': replenishment,
            'orderpoint_id': orderpoint
        }
        return values
