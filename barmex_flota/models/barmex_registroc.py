from email.policy import default
from odoo import models, fields, api, _
from datetime import date
from odoo.exceptions import AccessError, ValidationError

class registroc(models.Model):
    _name = 'barmex.registroc'
    _description = 'barmex.registroc'
    _inherit = 'mail.thread', 'mail.activity.mixin', 'utm.mixin'

    @api.model
    def create(self, vals):
        x = self.env['ir.sequence'].next_by_code('barmex.registroc') or '/'
        vals['name'] = x
        return super(registroc, self).create(vals)

    @api.onchange('litros','costo_litro')
    @api.depends('litros','costo_litro')
    def on_litros_change(self):
        if not self.litros:
            self.total = 0
        else:  
            self.total = (self.costo_litro * self.litros)

    @api.onchange('hubodometro','litros', 'unidad_id')
    @api.depends('hubodometro','litros', 'unidad_id')
    def on_kilometraje_change(self):
        try:
            ultimo_hubodometro = self.env['barmex.registroc'].search([('unidad_id.id', '=', self.unidad_id.id)], limit = 2, order='id desc')[0].hubodometro
        except Exception as e:
            print('este es el except')
            print(e)
            ultimo_hubodometro = 0
            
        recorrido = self.hubodometro - ultimo_hubodometro
        
        if ultimo_hubodometro == 0:
            print('puso 400')
            if(self.litros > 0):
                self.rendimiento = (recorrido / self.litros)
                self.km_recorrido = recorrido
            else:
                self.rendimiento = recorrido
                self.km_recorrido = recorrido
        else:
            print('ya entro')
            print(recorrido)
            print(self.litros)
            print(ultimo_hubodometro)
            print(self.hubodometro)
            if(self.litros > 0):
                self.rendimiento = (recorrido / self.litros)
                self.km_recorrido = recorrido
            else:
                self.rendimiento = recorrido
                self.km_recorrido = recorrido

    name = fields.Char('Folio de Combustible')
    realizada = fields.Date('Fecha realizada')
    litros = fields.Float('Litros')
    total = fields.Float('Total')
    costo_litro = fields.Float('Costo por litros')
    hubodometro = fields.Float('Kilometros en Hubodometro')
    km_recorrido = fields.Float('Km recorrido')
    rendimiento = fields.Float('Rendimiento calculado')
    comentarios = fields.Text('Comentarios/Detalles')
    lugar_combustible = fields.Selection([('local', 'Carga Local'),
                              ('externa', 'Carga Externa')],
                             'Lugar de Carga', index=True, default='local')
    lugar_gasolinera = fields.Selection([('gas1', 'Gasolinera Norte'),
                              ('gas2', 'Gasolinera Sur'),
                              ('gas3', 'Gasolinera Este'),
                              ('gas4', 'Gasolinera Oeste')],
                             'Nombre Gasolinera', index=True, default='gas1')
    unidad_id = fields.Many2one('barmex.unidades', 'Unidad')
    gasolineria_id = fields.Many2one('barmex.gasolinerias', 'Gasolineria')