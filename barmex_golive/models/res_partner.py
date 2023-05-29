from odoo import models, fields, api

class resPartner(models.Model):
    _name = "res.partner"
    _inherit = "res.partner"

    proveedor = fields.Boolean(compute='fun_proveedor')
    cliente = fields.Boolean(compute='fun_cliente')
    email_pago_proveedores = fields.Char('Email Pago Proveedores')
   
    def fun_proveedor(self):
        if self.supplier_rank > 0:
            self.proveedor = 1
        else:
            self.proveedor = 0


    def fun_cliente(self):
        if self.customer_rank > 0:
            self.cliente = 1
        else:
           self.cliente = 0 

    @api.onchange('proveedor')
    def fun_proveedor_change(self):
        if self.proveedor == 1:
            self.supplier_rank = 1
        else:
            self.supplier_rank = 0

    @api.onchange('cliente')
    def fun_cliente_change(self):
        if self.cliente == 1:
            self.customer_rank = 1
        else:
           self.customer_rank = 0 

    # @api.onchange('cliente','proveedor')
    # def fun_clienteproveedor_change(self):
    #     if self.cliente == 1 and self.proveedor == 1:
    #         self.customer_rank = 0
    #         self.customer_rank = 0
    
    

