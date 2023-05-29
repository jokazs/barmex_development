# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    "name": """Carta Porte tipo T """,
    'version': '1.1.',
    'category': 'Account',
    'description': """
    Carta Porte a partir de salidas de almacén para entregas que requieren caminos federales.
    """,
    'depends': [
        'delivery',
        'l10n_mx_edi',
        'web_map',
    ],
    "demo": [
        'demo/res_partner.xml',
        'demo/vehicle.xml',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/cfdi_cartaporte.xml',
        'data/cfdi_cartaporte_ct.xml',
        'data/l10n_mx_edi_part.xml',
        #'views/res_partner_views.xml',
        'views/stock_picking_views.xml',
        'views/vehicle_views.xml',
        'views/report_deliveryslip.xml',
        'views/carta_porte_reporte.xml',
        'views/carta_porte_reporte_ct.xml',
        'views/action_cp.xml',
    ],
    'installable': True,
    'auto_install': True,
    'application': False,
}
