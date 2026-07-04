# -*- coding: utf-8 -*-
from odoo import models, fields, api


class product_pricelist(models.Model):
    _inherit = 'product.pricelist'

    # Passage en champ related le 04/07/2026 : forcer le recalcul de la colonne stockée avec :
    # UPDATE product_pricelist pl SET is_societe_comptable = rp.is_societe_comptable FROM res_partner rp WHERE pl.partner_id = rp.id;
    # UPDATE product_pricelist SET is_societe_comptable = NULL WHERE partner_id IS NULL;
    
    is_societe_comptable = fields.Selection(related='partner_id.is_societe_comptable', store=True, index=True)

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        user = self.env.user
        if user.is_societe_comptable:
            args = args.copy()
            args += ['|', ('is_societe_comptable', '=', False), ('is_societe_comptable', '=', user.is_societe_comptable)]
        return super(product_pricelist, self)._search(args, offset=offset, limit=limit, order=order, count=count, access_rights_uid=access_rights_uid)


class product_pricelist_item(models.Model):
    _inherit = 'product.pricelist.item'

    is_societe_comptable = fields.Selection(related='pricelist_id.is_societe_comptable', store=True, index=True)

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        user = self.env.user
        if user.is_societe_comptable:
            args = args.copy()
            args += ['|', ('is_societe_comptable', '=', False), ('is_societe_comptable', '=', user.is_societe_comptable)]
        return super(product_pricelist_item, self)._search(args, offset=offset, limit=limit, order=order, count=count, access_rights_uid=access_rights_uid)
