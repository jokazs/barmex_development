{
    "name":"Almacen Digital",
    "description":"Facturas del almacén digital",
    'depends' : ['account'],
    "data":[
        "views/almacen_digital.xml",
        "views/res_company.xml",
        "views/account_move.xml",
        "wizards/sync_manual.xml",
        "wizards/cargar_xml.xml",
        "views/almacen_digital_barmex_account_payment.xml",
        "security/ir.model.access.csv"
    ]
}