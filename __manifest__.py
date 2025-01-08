# -*- coding: utf-8 -*-
{
    'name': "Orbit registry Activity",

    'summary': """
        """,

    'description': """
        Orbit registro actividades
    """,

    'author': "Alberto Garcia - Orbit",
    'website': "",

    'category': 'Uncategorized',
    'version': '0.2',

    # any module necessary for this one to work correctly
    'depends': ['base','helpdesk','project'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/imputaciones_views.xml',
        'views/imputaciones_menus.xml',
        'views/actividades_views.xml',  
        'views/actividades_menus.xml'        
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'application': True,
    'license':'LGPL-3'
}