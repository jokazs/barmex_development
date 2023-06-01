from odoo import models, fields, api, _

class BarmexAddenda(models.Model):
    _name = 'barmex.addenda'
    _description = 'Barmex Addenda'
    _order = 'id desc'
    _check_company_auto = True

    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.company)

    name = fields.Char("Name",
                       required=True)

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
        ],
        required=True,
        string="Type")

    l10n_mx_edi_addenda = fields.Many2one('ir.ui.view',
                                          string='Addenda',
                                          help='A view representing the addenda',
                                          required=True,
                                          domain=[('l10n_mx_edi_addenda_flag', '=', True)])

    sociedad = fields.Char(string="Número de Sociedad",
                           default="1",
                           required=True)

    proveedor = fields.Char(string="Número de Proveedor",
                            default="1",
                            required=True)

    correo = fields.Char(string="Correo",
                         default="daniel.fuentes@barmex.com.mx",
                         required=True)

    mabe_calle = fields.Char(string="Calle",
                             default="Industrias",
                             required=True)

    mabe_planta = fields.Char(string="Planta de Entrega",
                              default="C005",
                              required=True)

    mabe_ext = fields.Char(string="Num. Ext.",
                           default="S/N",
                           required=True)

    mabe_int = fields.Char(string="Num. Int.",
                           default="S/N",
                           required=True)

    por_emisor = fields.Char(string="Emisor",
                             default="0115737",
                             required=True)

    por_receptor = fields.Char(string="Receptor",
                               default="0108918",
                               required=True)

    por_planta = fields.Char(string="Planta Emite",
                             default="R101",
                             required=True)

    san_cust = fields.Char(string="Customer Code",
                           default="43667",
                           required=True)

    san_name = fields.Char(string="Entidad",
                           default="SANMINA-SCI SYSTEMS DE MEXICO S.A. DE C.V.",
                           required=True)

    env_id = fields.Char(string="Id Factura",
                         default="Factura",
                         required=True)

    env_trans = fields.Char(string="Id Transaccion",
                            default="Con_Pedido",
                            required=True)

    sab_tipo = fields.Char(string="Tipo",
                           default="AddendaPCO",
                           required=True)

    sab_tipoDoc = fields.Char(string="Tipo Documento",
                              default="1",
                              required=True)

    pil_proceso = fields.Char(string="Proceso",
                              default="1",
                              required=True)

    lala_seller = fields.Char(string="Alternate Party ID",
                              default="802904",
                              required=True)

