# -*- coding: utf-8 -*-
from odoo import models, fields, api


class is_pricelist_item(models.Model):
    _inherit = 'is.pricelist.item'

    is_societe_comptable = fields.Selection(related='price_version_id.pricelist_id.is_societe_comptable')

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        user = self.env.user
        if user.is_societe_comptable:
            args = args.copy()
            args.append(('price_version_id.pricelist_id.is_societe_comptable', '=', user.is_societe_comptable))
        return super(is_pricelist_item, self)._search(args, offset=offset, limit=limit, order=order, count=count, access_rights_uid=access_rights_uid)
