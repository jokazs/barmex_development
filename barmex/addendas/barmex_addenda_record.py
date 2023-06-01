from odoo import models, fields, api, _


class BarmexAddendaRecord(models.Model):
    _name = 'barmex.addenda.record'
    _description = 'Barmex Addenda Record'
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

    po = fields.Char("Pedido")

    recepcion = fields.Char(string="Recepción")

    division = fields.Char(string="División")

    servicio = fields.Char(string="Hoja Servicio")

    transporte = fields.Char(string="Transporte")

    recepcion = fields.Char(string="Recepción")

    transporte = fields.Char(string="Num. Transporte")

    cuenta = fields.Char(string="Num. Cuenta Pago")

    ejercicio = fields.Char(string="Ejercicio")

    inicio = fields.Char("Fecha Inicio Liquidación")

    fin = fields.Char("Fecha Final Liquidación")

    fem_clase = fields.Selection([
        ('1', 'Factura'),
        ('2', 'Consignación'),
        ('3', 'Retención'),
        ('8', 'Nota de Cargo'),
        ('9', 'Nota de Crédito')],
        string="Clase de Documento"
    )

    fem_entrada = fields.Char(string="Num. Entrada")

    fem_remision = fields.Char(string="Num. Remisión")

    fem_socio = fields.Char(string="Num Socio")

    fem_costo = fields.Char(string="Centro Costos")

    fem_ret1 = fields.Char(string="Retencion1")

    fem_ret2 = fields.Char(string="Retencion2")

    fem_ret3 = fields.Char(string="Retencion3")

    por_folio = fields.Char("Folio")

    pem_linea = fields.Char("Linea")

    pem_part = fields.Char("Part")

    env_trans = fields.Char("Transaccion")

    env_sec = fields.Char("Secuencia")

    env_albaran = fields.Char("Albaran")

    gln = fields.Char("GLN")

    lala_entity = fields.Char("Entity Type")

    lala_creator_id = fields.Char("Unique Creator ID")

    lala_inst = fields.Char("Special Instruction")

    lala_reference = fields.Char("Reference Identification")

    lala_date = fields.Char("Reference Date")

    lala_address = fields.Char("Shipping Name")

    lala_supplier = fields.Char("Supplier")