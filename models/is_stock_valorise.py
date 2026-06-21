# -*- coding: utf-8 -*-
from odoo import models, fields, api


class is_stock_valorise(models.Model):
    _inherit = 'is.stock.valorise'

    is_societe_comptable = fields.Selection(related='product_id.is_societe_comptable')

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        user = self.env.user
        if user.is_societe_comptable:
            args = args.copy()
            args.append(('product_id.is_societe_comptable', '=', user.is_societe_comptable))
        return super(is_stock_valorise, self)._search(args, offset=offset, limit=limit, order=order, count=count, access_rights_uid=access_rights_uid)
