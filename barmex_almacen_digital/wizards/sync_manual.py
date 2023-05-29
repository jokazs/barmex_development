from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError, Warning
from datetime import datetime
import xml.etree.ElementTree as ET
import base64
import requests


class BarmexSyncManual(models.TransientModel):
    _name = "barmex.sync_manual"
    _description = "Sync Manual"


    def ejecutar(self):
        resultado = 'Peticion enviada'
        empresa = self.env['res.company'].browse([self.env.company.id])
        res = ''
        host = empresa.host_produccion
        token = empresa.user_produccion
        try:
            res = requests.get(host,headers=token)
            
        except:
            resultado = f'Error al enviar la solicitud al SAT. Host: {host} Token {token}'
        self.env['almacen.digital_sincronizacion'].create({'api':host, 
                                                                'fecha_sincronizacion':fields.Date.today(),
                                                                'status':resultado})

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Resultado SAT',
                'message': resultado,
                'sticky': False,
                'target': 'current',
            }
        } 
