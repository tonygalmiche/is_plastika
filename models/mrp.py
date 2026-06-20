# -*- coding: utf-8 -*-
from odoo import models, fields, api
from .product import societe_comptable_list


class mrp_bom(models.Model):
    _inherit = 'mrp.bom'

    is_societe_comptable = fields.Selection(related='product_tmpl_id.is_societe_comptable', store=True, index=True)

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        user = self.env.user
        if user.is_societe_comptable:
            args = args.copy()
            args.append(('is_societe_comptable', '=', user.is_societe_comptable))
        return super(mrp_bom, self)._search(args, offset=offset, limit=limit, order=order, count=count, access_rights_uid=access_rights_uid)


class mrp_bom_line(models.Model):
    _inherit = 'mrp.bom.line'

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        user = self.env.user
        if user.is_societe_comptable:
            args = args.copy()
            args.append(('bom_id.product_tmpl_id.is_societe_comptable', '=', user.is_societe_comptable))
        return super(mrp_bom_line, self)._search(args, offset=offset, limit=limit, order=order, count=count, access_rights_uid=access_rights_uid)


class mrp_routing(models.Model):
    _inherit = 'mrp.routing'

    is_societe_comptable = fields.Selection(societe_comptable_list, "Société comptable", default='plastigray', index=True)

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        user = self.env.user
        if user.is_societe_comptable:
            args = args.copy()
            args.append(('is_societe_comptable', '=', user.is_societe_comptable))
        return super(mrp_routing, self)._search(args, offset=offset, limit=limit, order=order, count=count, access_rights_uid=access_rights_uid)


class mrp_routing_workcenter(models.Model):
    _inherit = 'mrp.routing.workcenter'

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        user = self.env.user
        if user.is_societe_comptable:
            args = args.copy()
            args.append(('routing_id.is_societe_comptable', '=', user.is_societe_comptable))
        return super(mrp_routing_workcenter, self)._search(args, offset=offset, limit=limit, order=order, count=count, access_rights_uid=access_rights_uid)
