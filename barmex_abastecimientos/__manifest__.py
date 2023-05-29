{
    "name":"Barmex Abastecimientos",
    "description":"Personalización de MRP para generar pedidos de compra Barmex",
    'depends': ['base','stock', 'purchase', 'sale','sale_stock','purchase_stock', 'sale_purchase'],
    "data":[
        "views/wizard_abastecimientos.xml",
        "views/barmex_sale_order.xml",
        "views/barmex_product_supplierinfo.xml"
        #"security/ir.model.access.csv"
    ]
}