from odoo import models,fields

class CredentialsAD(models.Model):
    _name = "credenciales"
    _description = 'agregar documentos para el autenticación del almacen digital'
    # un solo registro por RFC
    name = fields.Char("RFC")
    password_fiel = fields.Char("Contraseña",help="campo solo para anotar contraseña")
    cer_fiel_name = fields.Char("Certificado")
    cer_fiel = fields.Binary(string="Archivo Certificado",attachment=False)
    key_fiel_name = fields.Char("Key")
    key_fiel = fields.Binary(string="Archivo Key",attachment=False)

    datos_enviados = fields.Boolean(compute='fun_ad_enviados')

    def fun_ad_enviados(self):
        if self.key_fiel_name != "" and self.cer_fiel_name != "":
            self.datos_enviados = 1
        else:
           self.datos_enviados = 0

