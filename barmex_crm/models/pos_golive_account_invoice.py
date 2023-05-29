import base64
from lxml import etree
from lxml.objectify import fromstring

from odoo import _, api, fields, models, tools

import logging
_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = ['account.move']

    def l10n_mx_edi_append_addenda(self, xml_signed):
        self.ensure_one()
        addenda = (
            self.partner_id.l10n_mx_edi_addenda or
            self.partner_id.commercial_partner_id.l10n_mx_edi_addenda)
        if not addenda:
            return xml_signed
        values = {
            'record': self,
        }
        addenda_node_str = addenda.render(values=values).strip()
        if not addenda_node_str:
            return xml_signed
        tree = fromstring(base64.decodebytes(xml_signed))      
        addenda_node = fromstring(addenda_node_str)
        if addenda_node.tag != '{http://www.sat.gob.mx/cfd/4}Addenda':
            node = etree.Element(etree.QName(
                'http://www.sat.gob.mx/cfd/4', 'Addenda'))
            node.append(addenda_node)
            addenda_node = node
        tree.append(addenda_node)
        self.message_post(
            body=_('Addenda has been added in the CFDI with success'),
            subtype='account.mt_invoice_validated')
        encode_xml = etree.tostring(tree, pretty_print=True, xml_declaration=True, encoding='UTF-8')
        #_logger.info(encode_xml)  
        if self.addenda_id.type == "viscofan":
            encode_xml = encode_xml.decode('utf-8')
            _logger.info(encode_xml)
            encode_xml = encode_xml.replace("<Viscofan>\n","")
            encode_xml = encode_xml.replace("</Viscofan>\n","")
            encode_xml = encode_xml.encode('utf-8')
        elif self.addenda_id.type == "femsa":
            encode_xml = encode_xml.decode('utf-8')
            _logger.info(encode_xml)
            encode_xml = encode_xml.replace("<noVersAdd/>","<noVersAdd></noVersAdd>")
            encode_xml = encode_xml.replace("<claseDoc/>","<claseDoc></claseDoc>")
            encode_xml = encode_xml.replace("<noSociedad/>","<noSociedad></noSociedad>")
            encode_xml = encode_xml.replace("<noProveedor/>","<noProveedor></noProveedor>")
            encode_xml = encode_xml.replace("<noPedido/>","<noPedido></noPedido>")
            encode_xml = encode_xml.replace("<moneda/>","<moneda></moneda>")
            encode_xml = encode_xml.replace("<noEntrada/>","<noEntrada></noEntrada>")
            encode_xml = encode_xml.replace("<noRemision/>","<noRemision></noRemision>")
            encode_xml = encode_xml.replace("<noSocio/>","<noSocio></noSocio>")
            encode_xml = encode_xml.replace("<centroCostos/>","<centroCostos></centroCostos>")
            encode_xml = encode_xml.replace("<iniPerLiq/>","<iniPerLiq></iniPerLiq>")
            encode_xml = encode_xml.replace("<finPerLiq/>","<finPerLiq></finPerLiq>")
            encode_xml = encode_xml.replace("<retencion1/>","<retencion1></retencion1>")
            encode_xml = encode_xml.replace("<retencion2/>","<retencion2></retencion2>")
            encode_xml = encode_xml.replace("<retencion3/>","<retencion3></retencion3>")
            encode_xml = encode_xml.replace("<email/>","<email></email>")
            encode_xml = encode_xml.encode('utf-8')

        xml_signed = base64.encodebytes(encode_xml)
        #xml_signed = base64.encodebytes(etree.tostring(tree, pretty_print=True, xml_declaration=True, encoding='UTF-8'))
        attachment_id = self.l10n_mx_edi_retrieve_last_attachment()
        attachment_id.write({
            'datas': xml_signed,
            'mimetype': 'application/xml'
        })



        return xml_signed
