# -*- coding: utf-8 -*-
{
    'name': "CFDI 4.0 v13 Enterprise",

    'summary': """Agrega tipo de facturación en los diarios para asignar si es 3.3 o 4.0""",

    'description': """
    """,

    'author': "TuOdoo / Barmex",
    'website': "http://www.tuodoo.com",
    'category': 'Accounting/Accounting',
    'version': '13.0.2',
    'depends': ['l10n_mx_edi','account', 'barmex'],
    'data': [
        #'security/ir.model.access.csv',
        'views/res_partner_views.xml',
        #'views/account_payment_views.xml',
        #'views/account_tax_views.xml',
        #'views/account_journal_views.xml',
        'data/ir_cron.xml',
        'data/4.0/cfdi.xml',
        #'data/4.0/payment20.xml',
    ],
}
