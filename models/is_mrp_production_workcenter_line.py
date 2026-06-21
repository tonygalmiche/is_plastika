# -*- coding: utf-8 -*-
from odoo import models, fields, api


class is_mrp_production_workcenter_line(models.Model):
    _inherit = 'is.mrp.production.workcenter.line'

    is_societe_comptable = fields.Selection(related='product_id.product_tmpl_id.is_societe_comptable')

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        user = self.env.user
        if user.is_societe_comptable:
            args = args.copy()
            args.append(('product_id.product_tmpl_id.is_societe_comptable', '=', user.is_societe_comptable))
        return super(is_mrp_production_workcenter_line, self)._search(args, offset=offset, limit=limit, order=order, count=count, access_rights_uid=access_rights_uid)
