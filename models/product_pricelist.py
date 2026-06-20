# -*- coding: utf-8 -*-
from odoo import models, fields, api
from .product import societe_comptable_list


class product_pricelist(models.Model):
    _inherit = 'product.pricelist'

    is_societe_comptable = fields.Selection(societe_comptable_list, "Société comptable", default='plastigray', index=True)

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        user = self.env.user
        if user.is_societe_comptable:
            args = args.copy()
            args.append(('is_societe_comptable', '=', user.is_societe_comptable))
        return super(product_pricelist, self)._search(args, offset=offset, limit=limit, order=order, count=count, access_rights_uid=access_rights_uid)


class product_pricelist_item(models.Model):
    _inherit = 'product.pricelist.item'

    is_societe_comptable = fields.Selection(related='pricelist_id.is_societe_comptable', store=True, index=True)

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        user = self.env.user
        if user.is_societe_comptable:
            args = args.copy()
            args.append(('is_societe_comptable', '=', user.is_societe_comptable))
        return super(product_pricelist_item, self)._search(args, offset=offset, limit=limit, order=order, count=count, access_rights_uid=access_rights_uid)
