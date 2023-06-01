from odoo import models, fields, api, _
from odoo.exceptions import Warning, ValidationError, UserError


class SaleOrder(models.Model):
    _inherit = ['sale.order']

    state = fields.Selection(
        selection_add=[
            ('lock', 'Credit Lock'),
            ('total_lock', 'Total Lock'),
            ('bloqueo_cyc', 'Bloqueado CyC'),
        ])

    previous_state = fields.Char(string='Previous State',
                                 readonly=True)

    lco_sale_participants_ids = fields.Many2many('crm.lead',
                                                 string='Participants')

    lco_property_product_pricelist_id = fields.Many2one('product.pricelist',
                                                        store=True,
                                                        copied=True,
                                                        on_delete='restricted',
                                                        string="Reseller price")

    lco_fact_global_related = fields.Boolean(string='Global invoicing',
                                             related='partner_id.lco_fact_global')

    lco_sale_customer_type = fields.Many2one(string='Customer type',
                                         related='partner_id.lco_customer_type',
                                         store=True,
                                         copied=True,
                                         readonly=True)

    credit_currency = fields.Many2one(string='Credit Currency',
                                      related='partner_id.credit_currency')

    sale_order_available = fields.Monetary(string='Sale Order Credit Available',
                                           related='partner_id.sale_order_available')

    customer_credit_available = fields.Monetary(string='Customer Credit Available',
                                                related='partner_id.credit_available')

    partner_addenda_id = fields.Many2one(string="Addenda Type",
                                         related="partner_id.addenda_id")

    addenda_id = fields.Many2one('barmex.addenda.record',
                                 string="Addenda",
                                 domain="[('id','=',addenda_num)]")

    addenda_num = fields.Integer('Addenda ID')

    lco_is_prospect = fields.Boolean(string='Cliente prospecto',
                                        related='partner_id.lco_is_prospect')
    
    is_prospect = fields.Boolean(string='Is prospect', computed='_get_is_prospect')
    
    l10n_mx_edi_payment_method_id = fields.Many2one('l10n_mx_edi.payment.method', 'Forma de pago')
    
    @api.depends('partner_id')
    @api.onchange('partner_id')
    def _update_l10n_mx_edi_payment_method_id(self):
        if self.partner_id.x_l10n_mx_edi_payment_method_id:
            self.l10n_mx_edi_payment_method_id = self.partner_id.x_l10n_mx_edi_payment_method_id
            
    @api.onchange('order_line')
    @api.depends('order_line')
    def _get_is_prospect(self):
        self._update_l10n_mx_edi_payment_method_id()
        for record in self.order_line:
            if record.lco_prod_prospecto:
                self.is_prospect = True

    @api.onchange('x_studio_field_PR9lL','is_prospect')
    @api.depends('x_studio_field_PR9lL','is_prospect')
    def _get_note(self):
        self.note = ''
        if self.is_prospect:
            self.note = 'Precios de referencia, pueden ser modificados en cualquier momento.'
        for item in self.x_studio_field_PR9lL:
            if self.note:
                self.note += '\n' + item.x_name
            else: 
                self.note += item.x_name

    def get_credit_message(self):
        self.ensure_one()

        msg = ""
        order_amount = self.currency_id._convert(self.amount_total, self.partner_id.credit_currency, self.env.company,
                                                 self.date_order)

        if not self.partner_id.exceed_limit:
            if self.partner_id.sale_order_exceeded:
                msg = _("Sale order credit limit exceeded.\nThis order will be locked.")

            elif order_amount > self.partner_id.sale_order_available and self.partner_id.sale_order_include:
                msg = _("Sale order credit will be exceeded with this order.\nThis order will be locked.")

            elif self.partner_id.credit_exceeded:
                msg = _("Credit limit exceeded.\nThis order will be locked.")

            elif self.partner_id.total_risk + order_amount > self.partner_id.general_limit:
                msg = _("Credit limit will be exceeded with this order.\nThis order will be locked.")

            elif self.partner_id.due_invoice_lock and self.partner_id.locked_by_due:
                msg = _("Has due invoices.\nThis order will be locked")

            if self.state == 'lock':
                msg = False

        return msg

    def action_lock(self):
        self.state = 'lock'

    def action_bloqueocyc(self):
        self.previous_state = self.state
        self.state = 'bloqueo_cyc'

    def approve_order(self):
        self.action_confirm()

    def prospect_product(self):
        for record in self.order_line:
            if record.lco_prod_prospecto:
                raise UserError(_("This operation is not allowed with prospect products"))

    def prospect_client(self):
        if self.lco_is_prospect or self.partner_id.lco_customer_type == 'PROSPECTO':
            raise UserError("Esta operación no es válida para prospectos.")

    def action_confirm(self):
        self.prospect_product()
        self.prospect_client()
        msg = self.get_credit_message()
        if msg:
            return (
                self.env['barmex.alert'].create({
                    'exception_msg': msg,
                    'partner_id': self.partner_id.id,
                    'origin_reference': '{},{}'.format('sale.order', self.id),
                    'continue_method': 'action_lock',
                }).action_show(_('Sale Order Credit Alert'))
            )

        else:
            return super(SaleOrder, self).action_confirm()


    @api.onchange('partner_invoice_id')
    def onchange_invoice_id(self):
        if not self.partner_id:
            self.update({
                'partner_invoice_id': False,
                'partner_shipping_id': False,
                'fiscal_position_id': False,
            })
            return
        if self.partner_id == self.partner_invoice_id:
            return

        values = {
            'payment_term_id': self.partner_invoice_id.property_payment_term_id and self.partner_invoice_id.property_payment_term_id.id or False,
            'team_id': self.partner_invoice_id.team_id and self.partner_invoice_id.team_id.id or False
        }

        self.update(values)



    @api.onchange('partner_id')
    def onchange_partner_id(self):
        """
        Update the following fields when the partner is changed:
        - Pricelist
        - Distributor Pricelist (LCO)
        - Payment terms
        - Invoice address
        - Delivery address
        - Sales Team
        """
        if not self.partner_id:
            self.update({
                'partner_invoice_id': False,
                'partner_shipping_id': False,
                'fiscal_position_id': False,
            })
            return

        addr = self.partner_id.address_get(['delivery', 'invoice'])
        partner_user = self.partner_id.user_id or self.partner_id.commercial_partner_id.user_id
        values = {
            # 'pricelist_id': self.partner_id.property_product_pricelist and self.partner_id.property_product_pricelist.id or False,
            # 'lco_property_product_pricelist_id': self.partner_id.lco_property_product_pricelist and self.partner_id.lco_property_product_pricelist.id or False,
            'payment_term_id': self.partner_id.property_payment_term_id and self.partner_id.property_payment_term_id.id or False,
            'partner_invoice_id': addr['invoice'],
            'partner_shipping_id': addr['delivery'],
        }
        user_id = partner_user.id
        if not self.env.context.get('not_self_saleperson'):
            user_id = user_id or self.env.uid
        if user_id and self.user_id.id != user_id:
            values['user_id'] = user_id

        if self.env['ir.config_parameter'].sudo().get_param(
                'account.use_invoice_terms') and self.env.company.invoice_terms:
            values['note'] = self.with_context(lang=self.partner_id.lang).env.company.invoice_terms
        if not self.env.context.get('not_self_saleperson') or not self.team_id:
            values['team_id'] = self.env['crm.team'].with_context(
                default_team_id=self.partner_id.team_id.id
            )._get_default_team_id(domain=['|', ('company_id', '=', self.company_id.id), ('company_id', '=', False)],
                                   user_id=user_id)
        self.update(values)

    def _prepare_invoice(self):
        invoice_vals = super(SaleOrder, self)._prepare_invoice()

        invoice_vals['l10n_mx_edi_usage'] = self.partner_id.l10n_mx_edi_usage
        if self.partner_id.lco_sale_zone.journal_id:
            invoice_vals['journal_id'] = self.partner_id.lco_sale_zone.journal_id.id
        else: 
            raise ValidationError('Libro contable no esta definido en Zona de ventas')
        if self.partner_id.collector_ids:
            invoice_vals['collector_id'] = self.partner_id.collector_ids[0]
        if self.addenda_id:
            invoice_vals['addenda_id'] = self.addenda_id
            invoice_vals['addenda_num'] = self.addenda_num

        if self.partner_id.invoicing_currency:
            invoice_vals['currency_id'] = self.env.company.currency_id.id,

        return invoice_vals

    @api.onchange('pricelist_id', 'lco_property_product_pricelist_id')
    def onchange_pricelist_id(self):
        for record in self:
            if record.pricelist_id:
                if record.currency_id.id != record.lco_property_product_pricelist_id.currency_id.id:
                    record.update({'lco_property_product_pricelist_id': False})
            for line in record.order_line:
                line.product_id_change()

    def total_lock(self):
        self.previous_state = self.state
        self.state = 'total_lock'

        for record in self.picking_ids:
            record.update({
                'previous_state': record.state,
                'state': 'total_lock',
            })
        for record in self.invoice_ids:
            record.update({
                'previous_state': record.state,
                'state': 'total_lock',
            })

    def unlock(self):
        self.state = self.previous_state
        self.previous_state = ''
        if self.picking_ids:
            for record in self.picking_ids:
                record.update({
                    'state': record.previous_state,
                    'previous_state': '',
                })
        if self.invoice_ids:
            for record in self.invoice_ids:
                record.update({
                    'state': record.previous_state,
                    'previous_state': '',
                })

    # @api.onchange('partner_id')
    # def _available_pricelist(self):
    #     pricelist = self.env['barmex.customer.product.pricelist'].search([('partner_id', '=', self.partner_id.id)])
    #     ids = []
    #     # ids2 = []
    #     for record in pricelist:
    #         if not record.pricelist_id.reseller_price:
    #             ids.append(record.pricelist_id.id)
    #         # else:
    #         #     ids2.append(record.pricelist_id.id)

    #     return {'domain':
    #                 {'pricelist_id': [('id', 'in', ids)]
    #                 #  'lco_property_product_pricelist_id': [('id', 'in', ids2)]
    #                 }
    #             }

    # @api.onchange('partner_id')
    # def onchange_partner_id(self):
    #     super(SaleOrder, self).onchange_partner_id()

    #     ret = False

    #     pricelist = self.env['barmex.customer.product.pricelist'].search(
    #         [('pricelist_id', '=', self.partner_id.property_product_pricelist.id)])

    #     for record in pricelist:
    #         if record.partner_id.id == self.partner_id.id:
    #             ret = True

    #     if not ret:
    #         self.update({
    #             'pricelist_id': False
    #         })

    def _amount_to_words(self):

        currency = self.currency_id
        total = self.amount_total

        amount_i, amount_d = divmod(total, 1)
        amount_d = round(amount_d, 2)
        amount_d = int(round(amount_d * 100, 2))
        words = currency.with_context(lang=self.partner_id.lang or 'es_ES').amount_to_text(amount_i).upper()
        invoice_words = '%(words)s %(amount_d)02d/100 %(curr_t)s' % dict(
            words=words, amount_d=amount_d, curr_t=currency.name.upper())
        return invoice_words

    @api.onchange('partner_id')
    def _set_addenda(self):
        for record in self:
            if record.partner_addenda_id:
                addenda = self.env['barmex.addenda.record'].create({
                    'name': record.partner_addenda_id.name,
                    'type': record.partner_addenda_id.type,
                })

                record.update({
                    'addenda_id': addenda.id,
                    'addenda_num': addenda.id,
                })