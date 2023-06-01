from odoo import models, fields, api

class Payment(models.Model):
    _name = 'barmex.payment'
    _description = 'Bank payments'
    _order = 'id desc'
    _check_company_auto = True

    payment_date = fields.Date(string='Date',
                               default=fields.Date.context_today,
                               required=True,
                               readonly=True,
                               states={'draft': [('readonly', False)]},
                               copy=False)

    name = fields.Char(readonly=True,
                       required=True,
                       states={'draft': [('readonly', False)]},
                       copy=False)

    journal_id = fields.Many2one('account.journal',
                                 string='Journal',
                                 states={'draft': [('readonly', False)]},
                                 required=True,
                                 readonly=True,
                                 domain="[('type', 'in', ('bank', 'cash')), ('company_id', '=', company_id)]")

    payment_method_id = fields.Many2one('account.payment.method',
                                        string='Payment Method',
                                        states={'draft': [('readonly', False)]},
                                        required=True,
                                        readonly=True)

    partner_id = fields.Many2one('res.partner',
                                 string='Customer',
                                 tracking=True,
                                 readonly=True,
                                 domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
                                 states={'draft': [('readonly', False)]})

    amount = fields.Monetary(string='Amount',
                             required=True,
                             states={'draft': [('readonly', False)]},
                             readonly=True)

    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('posted', 'Validated')
        ],
        readonly=True,
        default='draft',
        string="Status")

    company_id = fields.Many2one('res.company',
                                 related='journal_id.company_id',
                                 string='Company',
                                 states={'draft': [('readonly', False)]},
                                 readonly=True)

    currency_id = fields.Many2one('res.currency',
                                  string='Currency',
                                  required=True,
                                  readonly=True,
                                  states={'draft': [('readonly', False)]},
                                  default=lambda self: self.env.company.currency_id)

    bank_reference = fields.Char(string='Bank reference',
                                 states={'draft': [('readonly', False)]},
                                 readonly=True)

    payment_type = fields.Selection(
        [
            ('outbound', 'Send Money'),
            ('inbound', 'Receive Money'),
            ('transfer', 'Internal Transfer')
        ],
        string='Payment Type',
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]})

    partner_type = fields.Selection(
        [
            ('customer', 'Customer'),
            ('supplier', 'Vendor')
        ],
        tracking=True,
        readonly=True,
        states={'draft': [('readonly', False)]})

    barmex_description = fields.Char(string='Description',
                                     states={'draft': [('readonly', False)]},
                                     readonly=True)

    barmex_office_id = fields.Many2one('barmex.bank.office',
                                       states={'draft': [('readonly', False)]},
                                       readonly=True,
                                       string = 'Bank office')

    def process_payment(self):
        for line in self:
            table = self.env['account.payment']
            payment = table.create({
                'payment_date': line.payment_date,
                'name': line.name,
                'journal_id': line.journal_id.id,
                'payment_method_id': line.payment_method_id.id,
                'partner_id': line.partner_id.id,
                'amount': line.amount,
                'state': 'posted',
                'company_id': line.company_id.id,
                'currency_id': line.currency_id.id,
                'payment_type': line.payment_type,
                'partner_type': line.partner_type
            })
            line.state = 'posted'