# -*- coding: utf-8 -*-

from odoo import api, fields, models, registry

import json
import random
from datetime import datetime
#import pip
import os
import logging
import threading
import time

_logger = logging.getLogger(__name__)

try:
    import pymysql
except:
    _logger.debug('Install pymysql')
    command = 'python3 -m pip install pymysql'
    _logger.debug(command)
    os.system(command)
    import pymysql

class ProductStock(models.Model):
    _name = 'product.stock'
    _description = 'Stock de productos'
    _rec_name = 'product_id'

    product_id = fields.Many2one('product.product', string='Product', required=True)
    product_name = fields.Char('Product Name', required=True)
    location_id = fields.Many2one('stock.location', string='Almacén', required=True)
    warehouse_name = fields.Char('Product Name', required=True)
    quantity_on_hand = fields.Float(string='Cantidad existente', default=0, readonly=True)
    quantity_available = fields.Float(string='Cantidad disponible', default=0, readonly=True)
    sync = fields.Boolean('Sync Status', help="Sync Status", default=False, index=True)

    _sql_constraints = [
        ('product_location_unique', 'unique(product_id, location_id)', 'El registro de stock ya existe.'),
        ('product_warehouse_name_unique', 'unique(product_name, location_id)', 'El registro de stock ya existe.')
    ]

    def sync_to_mysql(self, host, user, password, database, port, sync_all=False):
        run_key = "customer_portal_sync"

        try:
            sync = json.loads(self.env['ir.config_parameter'].sudo().get_param(run_key))
            if "success" not in sync["status"].keys():
                sync["status"]["healthcheck"] += 1
                self.env['ir.config_parameter'].sudo().set_param(run_key, json.dumps(sync))
                _logger.debug("In Progress {}".format(sync["status"]["healthcheck"]))
                if sync["status"]["healthcheck"] > 2:
                    raise Exception("Restart Customer Portal Sync...")
                return
            elif "error" in sync["status"].keys():
                raise Exception("Error Ocurrs Customer Portal Sync...")
            else:
                raise Exception("Resume Customer Portal Sync...")
        except:
            _logger.debug("Starting")
            run = random.getrandbits(32)
            dateTime = datetime.now()
            sync_dict = {"run": "{}".format(run), "status": {"start": "{}".format(dateTime), "runing": "{}".format(dateTime), "healthcheck": 0}}
            sync = self.env['ir.config_parameter'].sudo().set_param(run_key, json.dumps(sync_dict))

        if sync_all:
            product_stocks = self.env['product.stock'].sudo().search([])
            _logger.debug("Sync All Products")
        else:
            product_stocks = self.env['product.stock'].sudo().search([('sync', '=', False)], limit=100)
        values_list = [[
            product_stock.quantity_on_hand,
            product_stock.quantity_available,
            product_stock.product_name,
            product_stock.warehouse_name,
            product_stock.quantity_on_hand,
            product_stock.quantity_available, 
        ] for product_stock in product_stocks]
        _logger.debug("Values to SQL: {}".format(values_list))
        if not values_list:
            dateTime = datetime.now()
            sync_dict["status"]["success"] = "{}".format(dateTime)
            self.env['ir.config_parameter'].sudo().set_param(run_key, json.dumps(sync_dict))
            _logger.debug("No data to process")
            return
        try:
            # Conexión a la base de datos MySQL
            conn = pymysql.connect(host=host, user=user, password=password, db=database, port=port)
            cursor = conn.cursor()
            _logger.debug("SQL")
            sql = """
            INSERT INTO bmx_existencias (cod_art_rel_id, cod_alm_rel_id, art_exist, art_apartado, ult_mov_exist)
            SELECT a.art_id, m.id_almacen, %s, %s, NULL
            FROM bmx_articulos a
            JOIN bmx_almacenes m
            ON a.art_clave = %s AND m.almacen_clave = %s
            ON DUPLICATE KEY UPDATE
            art_exist = %s, art_apartado = %s, ult_mov_exist = NULL
            """
            for v_i, values in enumerate(values_list):
                try:
                    _logger.debug("RUN SQL")
                    _logger.debug(sql)
                    _logger.debug(values)
                    cursor.execute(sql, values)
                    _logger.debug(cursor._last_executed)
                    values_list[v_i].append(True)
                except Exception as e:
                    _logger.debug("SQL failed: {}".format(e))
                    _logger.debug("SQL DETAIL")
                    _logger.debug(cursor._last_executed)
                    values_list[v_i].append(False)
            conn.commit()
            cursor.close()
            conn.close()

            for product_stock, values in zip(product_stocks, values_list):
                if (product_stock.quantity_on_hand == values[0] and product_stock.quantity_available == values[1]) and values[6]:
                    product_stock.sync = True
            dateTime = datetime.now()
            sync_dict["status"]["success"] = "{}".format(dateTime)
            self.env['ir.config_parameter'].sudo().set_param(run_key, json.dumps(sync_dict))
        except Exception as e:
            dateTime = datetime.now()
            sync_dict["status"]["error"] = "{}".format(e)
            self.env['ir.config_parameter'].sudo().set_param("{}_last_error".format(run_key), json.dumps({"msj": "{}".format(e), "datetime": "{}".format(dateTime)}))

class StockMove(models.Model):
    _inherit = 'stock.move'

    def _action_done(self, cancel_backorder=False):
        _logger.info("Updating product stock...")
        res = super(StockMove, self)._action_done(cancel_backorder=cancel_backorder)
        seconds = random.uniform(1, 10)
        threads = []
        for stock_move in self:
            try:
                # Ejecutar el método en un hilo después de un delay de 5 segundos
                t = threading.Timer(seconds, stock_move.with_env(self.env)._update_product_stock)
                t.start()
                threads.append(t)
            except:
                pass

        # Esperar a que todos los hilos terminen
        #for t in threads:
        #    t.join()

        return res

    def _action_assign(self):
        _logger.info("Updating product stock...")
        res = super(StockMove, self)._action_assign()
        seconds = random.uniform(1, 10)
        threads = []
        for stock_move in self:
            try:
                # Ejecutar el método en un hilo después de un delay de 5 segundos
                t = threading.Timer(seconds, stock_move.with_env(self.env)._update_product_stock)
                t.start()
                threads.append(t)
            except:
                pass

        # Esperar a que todos los hilos terminen
        #for t in threads:
        #    t.join()

        return res

    def _do_unreserve(self):
        _logger.info("Updating product stock...")
        res = super(StockMove, self)._do_unreserve()
        seconds = random.uniform(1, 10)
        threads = []
        for stock_move in self:
            try:
                # Ejecutar el método en un hilo después de un delay de 5 segundos
                t = threading.Timer(seconds, stock_move.with_env(self.env)._update_product_stock)
                t.start()
                threads.append(t)
            except:
                pass

        # Esperar a que todos los hilos terminen
        #for t in threads:
        #    t.join()

        return res


    def _update_product_stock(self):
         with api.Environment.manage():
            with registry(self.env.cr.dbname).cursor() as new_cr:
                new_env = api.Environment(new_cr, self.env.uid, self.env.context)
                stock_move = self.with_env(new_env)
                _logger.info("Update product stock Function...")
                try:
                    product = stock_move.product_id
                    location1 = stock_move.location_dest_id
                    location2 = stock_move.location_id

                    locations = [stock_move.location_dest_id, stock_move.location_id]

                    for location in locations:

                        location_name = location.complete_name.split("/")[0]
                        location_id = location.id

                        if not location_name.isdigit():
                            continue


                        stock_quant = stock_move.env['stock.quant'].search([('product_id', '=', product.id), ('location_id', '=', location_id)], limit=1)
                        reserved_quantity = stock_quant.reserved_quantity if stock_quant else 0.0
                        on_hand_qty = stock_quant.quantity if stock_quant else 0.0

                        _logger.debug("############### STOCK QUANT: {} {}".format(on_hand_qty, reserved_quantity))
                        
                        product_stock = stock_move.env['product.stock'].sudo().search([('product_id', '=', product.id), ('location_id', '=', location_id)])
                        if product_stock:
                            product_stock.quantity_on_hand = on_hand_qty
                            product_stock.quantity_available = reserved_quantity
                            product_stock.product_name = product.default_code
                            product_stock.warehouse_name = location_name
                            product_stock.sync = False
                        else:
                            try:
                                wharehouse_name = location_name
                                if len(product.default_code) > 0:
                                    stock_move.env['product.stock'].sudo().create({
                                        'product_id': product.id,
                                        'product_name': product.default_code,
                                        'location_id': location_id,
                                        'warehouse_name': wharehouse_name,
                                        'quantity_on_hand': on_hand_qty,
                                        'quantity_available': reserved_quantity,
                                        'sync': False,
                                    })
                                    stock_move.env.cr.commit()
                            except Exception as e:
                                _logger.debug("Error Customer Sync -> {}".format(e))
                    cron = stock_move.env['ir.cron'].sudo().search([('name', '=', 'Sync Product Stock to Customer Portal')])
                    retries = 0
                    while(True):
                        retries = retries + 1
                        if retries > 50:
                            _logger.error("upgrade Product Stock was Retried to 50 attempts")
                            break
                        try:
                            cron.method_direct_trigger()
                            _logger.info("update Product Stock Works Correctly")
                            break
                        except Exception as e:
                            _logger.info("Try to update Product Stock {}".format(e))
                            _logger.info("Retry...")
                            time.sleep(1)
                    _logger.info("Update product stock Function Completed...")
                except Exception as e:
                    _logger.error('Update product stock Function Exception{}'.format(e))

