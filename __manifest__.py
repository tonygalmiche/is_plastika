# -*- coding: utf-8 -*-
{
    "name"     : "Module Odoo 16 pour Plasti-ka",
    "version"  : "0.1",
    "author"   : "InfoSaône",
    "category" : "InfoSaône",
    "description": """
Module Odoo 16 pour Plasti-ka
===================================================
""",
    "maintainer" : "InfoSaône",
    "website"    : "http://www.infosaone.com",
    "depends"    : [
        "is_plastigray16",
    ],
    "data" : [
        "security/ir.model.access.csv",
        "views/menu.xml",
        "views/product_view.xml",
        "views/sale_view.xml",
        "views/is_demande_achat_view.xml",
        "views/is_ligne_reception.xml",
        "views/is_cout_view.xml",
        "views/is_taux_change_view.xml",
    ], 
    "qweb": [
    ],
    "assets": {
    },
    "installable": True,
    "application": True,
    "license": "LGPL-3",
}
