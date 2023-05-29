{
    "name":"Barmex Notas de credito",
    "description":"Personalización de Contabilidad para generar notas de crédito Barmex",
    'depends': ['base','stock', 'purchase', 'account', 'sale','sale_stock','purchase_stock', 'sale_purchase'],
    "data":[
        "wizards/notas_credito.xml",
        "views/barmex_notas_credito.xml",
        "views/barmex_account_journal.xml",
        "views/catalogo_notas.xml",
        "views/res_company.xml"
        #"security/ir.model.access.csv"
    ]
}