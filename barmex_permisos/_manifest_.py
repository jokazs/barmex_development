{
    'name' : 'Barmex Permisos',
    'version' : '1.3.5',
    'author' : 'Barmex',
    'website' : '',
    'category' : 'Tools',
    'sequence' : 10,
    'licence' : 'AGPL-3',
    'summary' : 'Permisos Barmex',
    'depends' : [],
    'data' : [
        #security
        'security/model_security.xml',
        'security/ir.model.access.csv',
    ],
    'installable' : True,
    'application' : True,
    'auto_install' : False,
}
