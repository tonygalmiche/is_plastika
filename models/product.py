# -*- coding: utf-8 -*-
from odoo import models, fields, api

societe_comptable_list = [
    ('plastigray', 'Plastigray'),
    ('plasti_ka', 'Plasti-ka'),
]


class is_category(models.Model):
    _inherit = 'is.category'

    is_societe_comptable = fields.Selection(societe_comptable_list, "Société comptable", default='plastigray', tracking=True, index=True)

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        # Filtrer par société comptable de l'utilisateur
        user = self.env.user
        if user.is_societe_comptable:
            args = args.copy()
            args.append(('is_societe_comptable', '=', user.is_societe_comptable))
        
        return super(is_category, self)._search(args, offset=offset, limit=limit, order=order, count=count, access_rights_uid=access_rights_uid)


class product_template(models.Model):
    _inherit = 'product.template'

    is_societe_comptable = fields.Selection(related='is_category_id.is_societe_comptable', store=True, tracking=True, index=True)
    is_article_comptable_pk_id = fields.Many2one(
        'product.product', 'Article comptable PK', tracking=True,
        domain=[('is_societe_comptable', '=', 'plasti_ka'), ('is_section_analytique_ha_id.name', '=', 'GROUPE')],
        help="Article utilisé sur la commande au fournisseur de PK générée depuis la commande de Gray (son compte de charges est celui de PK)",
    )

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        # Filtrer par société comptable de l'utilisateur
        user = self.env.user
        if user.is_societe_comptable:
            args = args.copy()
            args.append(('is_societe_comptable', '=', user.is_societe_comptable))

        return super(product_template, self)._search(args, offset=offset, limit=limit, order=order, count=count, access_rights_uid=access_rights_uid)


class is_product_packaging(models.Model):
    _inherit = 'is.product.packaging'

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        user = self.env.user
        if user.is_societe_comptable:
            args = args.copy()
            args.append(('product_tmpl_id.is_societe_comptable', '=', user.is_societe_comptable))
        return super(is_product_packaging, self)._search(args, offset=offset, limit=limit, order=order, count=count, access_rights_uid=access_rights_uid)
