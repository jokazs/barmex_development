from odoo import models,fields

class CRMLead(models.Model):
    _inherit = "crm.lead"
    _description = 'add currency to crm.lead'

    currency_lead = fields.Selection([('MXN','MXN'),('USD','USD'),('EUR','EUR'),('other','Other')],'Moneda', default='MXN')

    zona_venta_cliente = fields.Many2one(string='Zona de Venta del Cliente',
                                related="partner_id.lco_sale_zone", store=True)

    agente_venta_cliente = fields.Many2one(string='Agente de Venta del Cliente',
                                related="partner_id.proveedor_employee", store=True)