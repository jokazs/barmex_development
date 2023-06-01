from odoo import models, fields, api, _

class ProductClassification(models.TransientModel):
    _name = 'barmex.classification.process'
    _description = 'Product classification process'
    _check_company_auto = True


    def process(self):
        self.env['product.product'].classification()
