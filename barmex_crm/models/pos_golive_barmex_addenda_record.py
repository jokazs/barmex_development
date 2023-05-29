from odoo import models, fields, api, _

class BarmexAddendaRecord(models.Model):
    _inherit = 'barmex.addenda.record'

    type = fields.Selection([
        ('calsonickansei', 'Calsonickansei Mexicana'),
        ('hornos', 'Altos Hornos de México'),
        ('femsa', 'FEMSA'),
        ('lala', 'LALA'),
        ('mabe', 'MABE'),
        ('minera', 'Minera del Norte'),
        ('pemex', 'PEMEX'),
        ('porcelanite', 'Porcelanite Lamosa'),
        ('sanmina', 'SANMINA'),
        ('sergoba', 'SERGOBA'),
        ('envases', 'Envases Universales'),
        ('sabritas', 'Sabritas Pepsico'),
        ('jugos', 'Jugos del Valle'),
        ('pilgrims', 'Pilgrims Pride'),
        ('zf', 'ZF SUSPENSION TECHNOLOGY'),
        ('viscofan', 'VISCOFAN'),
    ],
        required=True,
        string="Type")

    acreedor_addenda = fields.Char("Acreedor")
    planta_entrega_addenda = fields.Char("Planta Entrega")
    nolineaart_addenda = fields.Char("No Linea Articulo")
    email_addenda = fields.Char("Email")