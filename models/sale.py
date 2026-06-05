# -*- coding: utf-8 -*-
from odoo import models, fields, api
from .product import societe_comptable_list


class sale_order(models.Model):
    _inherit = 'sale.order'

    is_societe_comptable = fields.Selection(related='partner_id.is_societe_comptable', store=True, tracking=True)

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        # Filtrer par société comptable de l'utilisateur
        user = self.env.user
        if user.is_societe_comptable:
            args = args.copy()
            args.append(('is_societe_comptable', '=', user.is_societe_comptable))
        
        return super(sale_order, self)._search(args, offset=offset, limit=limit, order=order, count=count, access_rights_uid=access_rights_uid)
