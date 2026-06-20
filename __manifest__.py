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
        "views/product_view.xml",
        "views/sale_view.xml",
        "views/is_demande_achat_view.xml",
        "views/is_ligne_reception.xml",
        "views/is_cout_view.xml",
        "views/is_taux_change_view.xml",
        "views/mrp_view.xml",
        "views/is_fiche_tampographie_view.xml",
        "views/is_certifications_qualite_suivi_view.xml",
        "views/product_pricelist_view.xml",
        "views/is_pricelist_item_view.xml",
        "views/is_cde_ouverte_fournisseur_view.xml",
        "views/is_cde_ferme_cadencee_view.xml",
        "views/is_export_edi_view.xml",
        "views/account_move_view.xml",
        "views/menu.xml",
    ], 
    "qweb": [
    ],
    "assets": {
    },
    "installable": True,
    "application": True,
    "license": "LGPL-3",
}
