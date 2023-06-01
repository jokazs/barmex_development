from odoo import models, fields, api, _
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.exceptions import UserError, Warning

class StockMove(models.Model):
    _inherit = ['stock.picking']

    state = fields.Selection(
        selection_add=[
            ('lock', 'Credit Lock'),
            ('total_lock', 'Total Lock'),
        ])

    foreign_trade_id = fields.Many2one('barmex.foreign.trade',
                                       states={'done': [('readonly', True)]})

    foreign_trade_ids = fields.One2many('barmex.foreign.trade',
                                        'move_id',
                                        string='Petitions')

    tax_id = fields.Char(related='partner_id.tax_id',
                         store=True,
                         readonly=True,
                         string='Tax Id')

    previous_state = fields.Char(string='Previous State',
                                 readonly=True)

    stock_accounting_ids = fields.One2many('account.move.line',
                                           'stock_move_id')

    @api.onchange('foreign_trade_id')
    def _foreign_trade(self):
        for record in self.move_line_ids:
            if not record.product_id.categ_id.removal_strategy_id.method in ('fifo', 'lifo'):
                raise Warning(_(
                    'Petition is unavailable for this transaction. All products Removal Strategy has to be FIFO or LIFO.'))
        self.foreign_trade_ids = self.foreign_trade_id

    def button_validate(self):
        res = None
        if self.picking_type_id.code == 'outgoing':
            msg = self.get_credit_message()
            if msg:
                return (
                    self.env['barmex.alert'].create({
                        'exception_msg': msg,
                        'partner_id': self.partner_id.id,
                        'origin_reference': '{},{}'.format('stock.picking', self.id),
                        'continue_method': 'action_lock',
                    }).action_show(_('Delivery Credit Alert'))
                )

        res = super(StockMove, self).button_validate()

        # Only do prices validation on purchases
        if self.picking_type_id.code == 'incoming':

            recepciones = self.env['purchase.order'].search([('name','=',self.origin),('state','=','purchase')], limit = 1)

            try:
                documentos = recepciones.origin.split(',')
                for documento in documentos:
                    salidas = self.env['stock.picking'].search([('origin','=',documento),('state','=','confirmed')], limit = 1)
                    for salida in salidas:
                        if salida:
                            salida.action_assign()
            except:
                print('Error en asignar las cantidades pendientes de salidas')
            # Auto transfer journals
            for line in self.move_ids_without_package:
                print(self.location_dest_id)
                print(line.transfer_to)
                    
                if self.location_dest_id == line.transfer_to:
                    print("Entro al if")
                    pass
                elif self.location_dest_id != line.transfer_to:
                    print("Entro al else")
                    line.product_id.last_currency = line.last_currency
                    line.product_id.last_price = line.last_price

                    vendor_price = self.env['product.supplierinfo'].search(
                        [('name', '=', self.partner_id.id), ('product_id', '=', line.product_id.id)])

                    if not vendor_price:
                        vendor_price = self.env['product.supplierinfo'].search(
                            [('name', '=', self.partner_id.id),
                            ('product_tmpl_id', '=', line.product_id.product_tmpl_id.id)])

                    if not vendor_price:
                        vendor_price = self.env['product.supplierinfo'].create({
                            'currency_id': self.env.ref('base.main_company').currency_id.id,
                            'delay': 1,
                            'min_qty': 1,
                            'name': self.partner_id.id,
                            'price': 1,
                            'product_id': line.product_id.id,
                            'product_tmpl_id': line.product_id.product_tmpl_id.id,
                        })

                    vendor_price.price = line.last_price
                    vendor_price.currency_id = line.last_currency.id

                    qty = line.quantity_done if line.quantity_done > 0 else line.product_uom_qty
                    pick_lines = []
                    if line.transferencia_creada != True: #verifico si ya está creado este producto
                        if line.transfer_to:
                            pick_line_values = {
                                'name': line.name,
                                'product_id': line.product_id.id,
                                'product_uom_qty': qty,
                                'product_uom': line.product_uom.id,
                                'state': 'draft',
                            }
                            pick_lines.append((0, 0, pick_line_values))
                            line.transferencia_creada = True #marco como hecho el producto
                            for transfer in self.move_ids_without_package: #hago un nuevo recorrido de productos para buscar mas de ese almacen
                                qty_t = transfer.quantity_done if transfer.quantity_done > 0 else transfer.product_uom_qty
                                if transfer.transfer_to == line.transfer_to:
                                    if transfer.transferencia_creada != True:
                                        pick_line_values_t = {
                                        'name': transfer.name,
                                        'product_id': transfer.product_id.id,
                                        'product_uom_qty': qty_t,
                                        'product_uom': transfer.product_uom.id,
                                        'state': 'draft',
                                        }
                                        pick_lines.append((0, 0, pick_line_values_t))
                                        transfer.transferencia_creada = True


                            picking = {
                                'partner_id': line.transfer_to.company_id.partner_id.id,
                                'picking_type_id': self.env['stock.picking.type'].search([('code', '=', 'internal')],
                                                                                        limit=1).id,
                                'origin': line.origin,
                                'location_id': line.location_dest_id.id,
                                'location_dest_id': line.transfer_to.id,
                                'move_type': 'direct',
                                'move_lines': pick_lines,
                            }
                            transfer = self.env['stock.picking'].sudo().create(picking)

                            if transfer:
                                transfer.action_confirm()
                                transfer.action_assign()

                if self.foreign_trade_id:
                    #Si la entrada tiene un pedimento entonces se crea un registro para llevar control de esa cantidad.
                    petition = self.env['barmex.petition.relation'].create({
                        'product_id': line.product_id.id,
                        'available': qty,
                        'petition': self.foreign_trade_id.petition,
                        'date': fields.datetime.now(),
                        'foreign_trade_id': self.foreign_trade_id.id
                    })

            self.stock_account()

        return res

    def get_credit_message(self):
        ret = False
        if self.state != 'lock':
            if self.partner_id.sale_order_exceeded and self.partner_id.sale_order_include:
                ret = _('Has one or more credit limits exceeded.\nThis delivery will be locked')
            elif self.partner_id.draft_invoice_exceeded and self.partner_id.draft_invoice_include:
                ret = _('Has one or more credit limits exceeded.\nThis delivery will be locked')
            elif self.partner_id.open_invoice_exceeded and self.partner_id.open_invoice_include:
                ret = _('Has one or more credit limits exceeded.\nThis delivery will be locked')
            elif self.partner_id.partially_payed_invoice_exceeded and self.partner_id.partially_payed_invoice_include:
                ret = _('Has one or more credit limits exceeded.\nThis delivery will be locked')
            elif self.partner_id.open_account_exceeded and self.partner_id.open_account_include:
                ret = _('Has one or more credit limits exceeded.\nThis delivery will be locked')
            elif self.partner_id.partially_open_account_exceeded and self.partner_id.partially_open_account_include:
                ret = _('Has one or more credit limits exceeded.\nThis delivery will be locked')
            elif self.partner_id.credit_exceeded or self.partner_id.locked_by_due:
                ret = _('Has one or more credit limits exceeded.\nThis delivery will be locked')
            elif self.partner_id.due_invoice_lock and self.partner_id.locked_by_due:
                ret = _('Has one or more invoices due.\nThis delivery will be locked')

        return ret

    def action_lock(self):
        self.state = 'lock'

    def approve_delivery(self):
        self.post()

    def _get_saleorder(self):
        sale = self.env['sale.order'].search([('name', '=', self.origin)])
        print(sale)
        return sale

    def _get_subtotal(self):
        subtotal = 0
        for record in self.move_ids_without_package:
            subtotal += record._get_subtotal();

        return subtotal

    def _get_taxes(self):
        res = 0
        for record in self.move_ids_without_package:
            res += record._get_itemtax();

        return res

    def _trim_notes(self):
        if self.note and len(self.note) > 55:
            return self.note[:25] + '\n' + self.note[25:55] + '...'
        else:
            return self.note

    def _amount_in_words(self):

        currency = self._get_saleorder().currency_id
        total = self._get_subtotal() + self._get_taxes()

        amount_i, amount_d = divmod(total, 1)
        amount_d = round(amount_d, 2)
        amount_d = int(round(amount_d * 100, 2))
        words = currency.with_context(lang=self.partner_id.lang or 'es_ES').amount_to_text(amount_i).upper()
        invoice_words = '%(words)s %(amount_d)02d/100 %(curr_t)s' % dict(
            words=words, amount_d=amount_d, curr_t=currency.name.upper())
        return invoice_words

    def _get_purchase(self):
        purchase = self.env['purchase.order'].search([('name', '=', self.origin)])

        return purchase

    def print_delivery_detail(self):
        return self.env.ref('barmex.barmex_delivery_report_detailed').report_action(self)

    def stock_account(self):
        if self.picking_type_id.code == 'incoming':

            source = self.location_dest_id.complete_name.split('/')
            source_acc = self.env['stock.warehouse'].search([('code', '=', source[0])]).stock_account

            if not source_acc:
                raise Warning(
                    'No se dispone cuenta de valor de inventario para el asiento contable asociado a esta transferencia')
            accounting = []

            for line in self.move_ids_without_package:
                move = self.env['account.move'].create({
                    'ref': self.name,
                    'journal_id': line.product_id.categ_id.property_stock_journal.id
                })

                accounting.append((0, 0, {
                    'account_id': line.product_id.categ_id.property_stock_account_input_categ_id.id,
                    'name': line.product_id.name,
                    'credit': line.product_id.price * line.quantity_done,
                    'move_id': move.id
                }))

                accounting.append((0, 0, {
                    'account_id': source_acc.id,
                    'name': line.product_id.name,
                    'debit': line.product_id.price * line.quantity_done,
                    'move_id': move.id
                }))

                self.stock_accounting_ids = accounting

        if self.picking_type_id.code == 'outgoing':
            source = self.location_id.complete_name.split('/')
            source_acc = self.env['stock.warehouse'].search([('code', '=', source[0])]).stock_account
            if not source_acc:
                raise Warning(
                    'No se dispone cuenta de valor de inventario para el asiento contable asociado a esta transferencia')
            accounting = []

            for line in self.move_ids_without_package:
                move = self.env['account.move'].create({
                    'ref': self.name,
                    'journal_id': line.product_id.categ_id.property_stock_journal.id
                })

                accounting.append((0, 0, {
                    'account_id': line.product_id.categ_id.property_stock_account_input_categ_id.id,
                    'name': line.product_id.name,
                    'debit': line.product_id.price * line.quantity_done,
                    'move_id': move.id
                }))

                accounting.append((0, 0, {
                    'account_id': source_acc.id,
                    'name': line.product_id.name,
                    'credit': line.product_id.price * line.quantity_done,
                    'move_id': move.id
                }))

                self.stock_accounting_ids = accounting

        if self.picking_type_id.code == 'internal':
            source = self.location_id.complete_name.split('/')
            source_acc = self.env['stock.warehouse'].search([('code', '=', source[0])]).stock_account
            dest = self.location_dest_id.complete_name.split('/')
            dest_acc = self.env['stock.warehouse'].search([('code', '=', dest[0])]).stock_account
            accounting = []

            if not source_acc or not dest_acc:
                raise Warning(
                    'No se dispone cuenta de valor de inventario para el asiento contable asociado a esta transferencia')

            if source != dest:
                move = self.env['account.move'].create({
                    'ref': self.name,
                    'journal_id': line.product_id.categ_id.property_stock_journal.id
                })

                accounting.append((0, 0, {
                    'account_id': dest_acc.id,
                    'name': line.product_id.name,
                    'debit': line.product_id.price * line.quantity_done,
                    'move_id': move.id
                }))

                accounting.append((0, 0, {
                    'account_id': source_acc.id,
                    'name': line.product_id.name,
                    'credit': line.product_id.price * line.quantity_done,
                    'move_id': move.id
                }))

                self.stock_accounting_ids = accounting