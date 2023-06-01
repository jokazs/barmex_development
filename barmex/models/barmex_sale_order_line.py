from datetime import datetime
from odoo import api, fields, models, _
from odoo.tools.misc import formatLang, get_lang
from odoo.exceptions import ValidationError, Warning

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    lco_price_dist = fields.Float('Reseller price',
                                  store=True)

    lco_price_diff = fields.Float(string='Difference',
                                  store=True)

    lco_prod_prospecto = fields.Boolean(string='Prospect',
                                        related='product_id.lco_is_prospect_prod')

    is_listprice_modified = fields.Boolean(string='Accept price modification?',
                                           store=True,
                                           readonly=True)

    lco_delivery_time = fields.Char(string='Delivery Time')

    def _modify_price(self):
        if self._product_in_pricelist().fixed_price == 0 or self.order_id.pricelist_id.is_modify_listprice:
            self.is_listprice_modified = True

    @api.onchange('product_id')
    def product_id_change(self):
        super(SaleOrderLine, self).product_id_change()

        if self.order_id.partner_id:
            if self.order_id.pricelist_id:
                if self.product_id:
                    product_pricelist = self._product_in_pricelist()
                    self._modify_price()

                    if not product_pricelist:
                        raise ValidationError(_("{} isn't in pricelist".format(self.product_id.name)))

            else:
                raise ValidationError(_('Pricelist not selected'))
        else:
            raise ValidationError(_('Customer not selected'))

        vals = {}

        product_dist = self.product_id.with_context(
            lang=get_lang(self.env, self.order_id.partner_id.lang).code,
            partner=self.order_id.partner_id,
            quantity=self.product_uom_qty,
            date=self.order_id.date_order,
            pricelist=self.order_id.lco_property_product_pricelist_id.id,
            uom=self.product_uom.id
        )

        if self.order_id.lco_property_product_pricelist_id and self.order_id.partner_id:
            vals['lco_price_dist'] = self.env['account.tax']._fix_tax_included_price_company(
                self._get_dist_display_price(product_dist), product_dist.taxes_id, self.tax_id, self.company_id)

        self.update(vals)

    def _prepare_invoice_line(self):
        res = super(SaleOrderLine, self)._prepare_invoice_line()

        dist = self.lco_price_dist
        diff = self.lco_price_diff
        if self.order_id.partner_id.invoicing_currency:
            res['price_unit'] = self._change_currency(self.price_unit)
            dist = self._change_currency(dist)
            diff = self._change_currency(diff)

        res['lco_price_dist'] = dist
        res['lco_price_diff'] = diff
        res['l10n_mx_edi_customs_number'] = self._get_petition()

        if self.display_type:
            res['account_id'] = False

        return res

    def _get_petition(self):
        delivery = self.env['stock.move.line'].search(
            [('product_id', '=', self.product_id.id), ('picking_id.sale_id', '=', self.order_id.id)])
        pedimento = []
        for record in delivery:
            pedimento.append(record.petition)
        res = ''

        if len(pedimento) == 0:
            res = ''
        else:
            try:
                res = ','.join(pedimento)
            except:
                print('No tiene pedimento')
                #raise Warning(_("No tiene pedimento"))
        return res

    def _change_currency(self, amount):

        local_cur = self.env.company.currency_id
        today = datetime.now().date()
        origin = self.order_id.currency_id

        res = origin._convert(amount, local_cur, self.env.company, today)
        return res

    def _get_dist_display_price(self, product):
        # it is possible that a no_variant attribute is still in a variant if
        # the type of the attribute has been changed after creation.
        no_variant_attributes_price_extra = [
            ptav.price_extra for ptav in self.product_no_variant_attribute_value_ids.filtered(
                lambda ptav:
                ptav.price_extra and
                ptav not in product.product_template_attribute_value_ids
            )
        ]
        if no_variant_attributes_price_extra:
            product = product.with_context(
                no_variant_attributes_price_extra=tuple(no_variant_attributes_price_extra)
            )

        if self.order_id.lco_property_product_pricelist_id.discount_policy == 'with_discount':
            return product.with_context(pricelist=self.order_id.lco_property_product_pricelist_id.id).price
        product_context = dict(self.env.context, partner_id=self.order_id.partner_id.id, date=self.order_id.date_order,
                               uom=self.product_uom.id)

        final_price, rule_id = self.order_id.lco_property_product_pricelist_id.with_context(
            product_context).get_product_price_rule(product or self.product_id, self.product_uom_qty or 1.0,
                                                    self.order_id.partner_id)
        base_price, currency = self.with_context(product_context)._get_real_price_currency(product, rule_id,
                                                                                           self.product_uom_qty,
                                                                                           self.product_uom,
                                                                                           self.order_id.lco_property_product_pricelist_id.id)
        if currency != self.order_id.lco_property_product_pricelist_id.currency_id:
            base_price = currency._convert(
                base_price, self.order_id.lco_property_product_pricelist_id.currency_id,
                self.order_id.company_id or self.env.company, self.order_id.date_order or fields.Date.today())
        return max(base_price, final_price)

    def _get_display_price(self, product):
        res = super(SaleOrderLine, self)._get_display_price(product)

        if self.product_id.sale_offer:
            pricelist = self._product_in_pricelist()
            res = pricelist.fixed_price

        return res

    def _product_in_pricelist(self):
        pricelist = None
        product_pricelist = ''

        if self.order_id.pricelist_id.global_cliente == True:
            #La lista aplica solamente para algunos clientes
            pasa = False
            print('Comparando !!!')
            print(self.order_id.pricelist_id.customer_ids)
            print(self.order_id.pricelist_id)
            for clientes in self.order_id.pricelist_id.customer_ids:
                print('Comparando clientes')
                print(clientes.partner_id.id)
                print(self.order_id.partner_id.id)
                if clientes.partner_id.id == self.order_id.partner_id.id:
                    pasa = True
            if pasa == False:
                raise Warning(_("Lista de precios no valida para este cliente"))

        #Primero busca una regla especifica para el producto en la lista de precios definida
        product_pricelist = self.env['product.pricelist.item'].search(
            [('pricelist_id', '=', self.order_id.pricelist_id.id),
             '|', ('product_id', '=', self.product_id.id),
             '&', ('product_tmpl_id', '=', self.product_id.product_tmpl_id.id),
             ('product_id', '=', False), ], limit=1)
        #Es mas eficiente primero buscar el producto en especifico y luego hacer el for entre las reglas de precios
        #print(f'Busqueda. product_id: pricelist_id {pricelist.id} {self.product_id.id} product_tmpl_id: {self.product_id.product_tmpl_id.id}')
        if not product_pricelist:
            try:
                for reglas_precios in self.order_id.pricelist_id.item_ids:
                    #Si no se encuentra regla especifica para el producto se busca politica global
                    if reglas_precios.applied_on == '3_global':
                        #La tarifa está basada en otra, hay que buscar si el producto pertenece a esa tarifa
                        if reglas_precios.base == 'pricelist':
                            product_in_subpricelist = self.env['product.pricelist.item'].search(
                                [('pricelist_id', '=', reglas_precios.base_pricelist_id.id),
                                 '|', ('product_id', '=', self.product_id.id),
                                 '&', ('product_tmpl_id', '=', self.product_id.product_tmpl_id.id),
                                 ('product_id', '=', False), ], limit=1)
                            if product_in_subpricelist:
                                return product_in_subpricelist
                            #Si en la tarifa se eligio que solamente los productos en la sublista son los validos.
                            #En caso contrario siempre deja agregar el producto
                            elif reglas_precios.base_pricelist_id.sublista_valido:
                                raise Warning(_("Producto Invalido para la lista de precios seleccionada"))

                        product_pricelist = reglas_precios
                        #print('Regla global!')
                        #print('Lo dejo pasar porque aplica a todos los productos')
                        return product_pricelist
                    #Si no hay politica global se busca por categoria
                    if reglas_precios.applied_on == '2_product_category':
                            if reglas_precios.categ_id.id == self.product_id.categ_id.id:
                                product_pricelist = reglas_precios
                                print('Regla por categoria!')
                                #print('Lo dejo pasar porque aplica a todos los productos')
                                return product_pricelist
                        #check si el producto esta en esa categoria, si si esta regresas la lista y ya.
            except Exception as e:
                print(e)
                raise Warning(_("Lista de precio Invalida"))
            raise Warning(_("Producto Invalido para la lista de precios seleccionada"))

        return product_pricelist