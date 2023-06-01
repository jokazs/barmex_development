from odoo import models, fields, api

class Conversion(models.TransientModel):
    _name = 'barmex.conversion'
    _description = 'Conversion table'

    qty = fields.Float(string='Quantity',
                       default=1)

    orig_uom = fields.Many2one('uom.uom',
                               string='UoM original')

    dest_uom = fields.Many2one('uom.uom',
                               string='UoM final')

    category = fields.Char(string='Category',
                           readonly=True)

    result = fields.Float(string='Result',
                          readonly=True)

    @api.onchange('qty')
    def _update_qty(self):
        if self.qty > 0:
            if self.orig_uom:
                if self.dest_uom:
                    self._conversion()

    @api.onchange('orig_uom')
    def _update_orig(self):
        if self.qty > 0:
            if self.orig_uom:
                if self.dest_uom:
                    self._conversion()

    @api.onchange('dest_uom')
    def _update_dest(self):
        if self.qty > 0:
            if self.orig_uom:
                if self.dest_uom:
                    self._conversion()

    def _conversion(self):
        res = self._to_reference()

        if self.dest_uom.uom_type == 'bigger':
            res = res / self.dest_uom.factor_inv
        elif self.dest_uom.uom_type == 'smaller':
            res = res * self.dest_uom.factor

        self.result = res

    def _to_reference(self):
        if self.orig_uom.uom_type == 'smaller':
            return self.qty / self.orig_uom.factor
        elif self.orig_uom.uom_type == 'bigger':
            return self.qty * self.orig_uom.factor_inv
        else:
            return self.qty

    @api.onchange('orig_uom')
    def _def_category(self):
        self.dest_uom = False

        if self.orig_uom:
            self.category = self.orig_uom.category_id.name
            return {'domain': {'dest_uom': [('category_id', '=', self.orig_uom.category_id.id)]}}
        else:
            self.category = ''
            return {'domain': {'dest_uom': []}}