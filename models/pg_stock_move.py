# -*- coding: utf-8 -*-
from odoo import models, fields, api


class pg_stock_move(models.Model):
    _inherit = 'pg.stock.move'

    is_societe_comptable = fields.Selection(related='product_id.product_tmpl_id.is_societe_comptable', store=True, index=True)

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        user = self.env.user
        if user.is_societe_comptable:
            args = args.copy()
            args.append(('is_societe_comptable', '=', user.is_societe_comptable))
        return super(pg_stock_move, self)._search(args, offset=offset, limit=limit, order=order, count=count, access_rights_uid=access_rights_uid)
