from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError, Warning
from datetime import datetime
import xml.etree.ElementTree as ET
import base64



class BarmexCargarXML(models.TransientModel):
    _name = "barmex.cargar_xml"
    _description = "Pronto pago"


    archivo_xml = fields.Binary('Archivo XML')
    archivos_xml = fields.Many2many('ir.attachment', string='Files', required=True,
                                      help='Carga masiva de archivos XML del SAT')

    def cargar(self):
        resultado = ''
        try:
            for archivo in self.archivos_xml:
                datos = base64.decodestring(archivo.datas)
                factura,productos = self.create_dict(datos)
                check_si_existe = self.env['almacen.digital'].search_count([('name','=',factura['name'])])
                if self.env.company.vat != factura['rfc_receptor']:
                    raise UserError(f"RFC del receptor del CFDI no coincide con RFC en compañia. {factura['rfc_receptor']} [{self.env.company.vat}]")
                if check_si_existe == 0:
                    factura_creada = self.env['almacen.digital'].create(factura)
                    for producto in productos:
                        producto['factura_id'] = factura_creada.id
                    productos_creados = self.env['almacen.digital_productos'].create(productos)
                    resultado = 'XML Agregado a Almacen Digital'
                else:
                    resultado = 'UUID Ya existe en Almacen digital'

        except TypeError as e:
            raise ValidationError(u'ERROR: {}'.format(e))
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Carga de archivos',
                'message': resultado,
                'sticky': False,
                'target': 'current',
            }
        } 

    def create_dict(self, xml):
        """regresa la info de la factura en XML como diccionario"""
        def get_attr_child(root,tag,attr):
            """Explora por los hijos del xml para encontrar un tag y obtener un atributo de este"""
            for i in root:
                if i.tag.find(tag) != -1:
                    return i.get(attr)

        float_none = lambda x: x if(x is not None) else 0

        result = {}
        productos,producto = [],{}
        tree = ET.fromstring(xml)
        root = tree

        #parents
        for attr in ['Fecha', 'Serie', 'Folio', 'Total', 'Moneda', 'TipoCambio', 'FormaPago','TipoDeComprobante']:
            if attr in root.attrib.keys():
                result[attr] = float_none(root.attrib[attr])
            else:
                result[attr] = None

        #childs
        for attr in [('Emisor','Rfc','provedor_rfc'),('Emisor','Nombre','provedor_nombre'),('Impuestos','TotalImpuestosTrasladados','impuestos'),('Receptor','Rfc','receptor_rfc')]:
            try:
                result[attr[2]] = get_attr_child(root,attr[0],attr[1])
            except:
                result[attr[2]] = None

        #UUID
        for tag in root:
            if tag.tag.find('Complemento') != -1:
                for child in tag:
                    if child.tag.find('TimbreFiscalDigital') != -1:
                        uuid = child.get('UUID')
                        result['uuid'] = uuid

        #products
        for tag in root:
            if tag.tag.find('Conceptos') != -1:
                for product in tag:
                    for attr in ['Descripcion', 'Cantidad', 'Importe','ClaveProdServ','ClaveUnidad']:
                        if attr in product.attrib.keys():
                            producto[attr] = float_none(product.attrib[attr])
                        else:
                            producto[attr] = None
                    producto['uuid'] = uuid
                    producto['factura_id'] = 100
                    #names
                    productos_names = {'Descripcion':'name', 'Cantidad':'cantidad', 'Importe':'precio', 
                                       'ClaveProdServ':'clave_prod_serv', 'ClaveUnidad':'clave_unidad'}
                    for c_n in productos_names:
                        producto[productos_names[c_n]] = producto.pop(c_n)
                    #add_product list
                    productos.append(producto)
                    producto = {}
        
        #gasto
        result['compra_gasto'] = 'gasto'
        #names
        factura_names = {'Fecha':'fecha_comprobante', 'Serie':'serie', 'Folio':'folio', 'Total':'total', 'Moneda':'moneda', 
                         'TipoCambio':'tipo_de_cambio', 'FormaPago':'forma_de_pago', 'TipoDeComprobante':'tipo_de_comprobante', 
                         'provedor_rfc':'rfc_emisor', 'provedor_nombre':'nombre_emisor', 'impuestos':'impuestos', 'uuid':'name',
                         'receptor_rfc':'rfc_receptor'}
        for c_n in factura_names:
            result[factura_names[c_n]] = result.pop(c_n)
        
        return result,productos
