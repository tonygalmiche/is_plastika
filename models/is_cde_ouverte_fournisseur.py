# -*- coding: utf-8 -*-
from odoo import models, fields, api


class is_cde_ouverte_fournisseur(models.Model):
    _inherit = 'is.cde.ouverte.fournisseur'

    is_societe_comptable = fields.Selection(related='partner_id.is_societe_comptable', store=True, index=True)

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        user = self.env.user
        if user.is_societe_comptable:
            args = args.copy()
            args.append(('is_societe_comptable', '=', user.is_societe_comptable))
        return super(is_cde_ouverte_fournisseur, self)._search(args, offset=offset, limit=limit, order=order, count=count, access_rights_uid=access_rights_uid)


class is_cde_ouverte_fournisseur_product(models.Model):
    _inherit = 'is.cde.ouverte.fournisseur.product'

    is_societe_comptable = fields.Selection(related='order_id.is_societe_comptable', store=True, index=True)

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        user = self.env.user
        if user.is_societe_comptable:
            args = args.copy()
            args.append(('is_societe_comptable', '=', user.is_societe_comptable))
        return super(is_cde_ouverte_fournisseur_product, self)._search(args, offset=offset, limit=limit, order=order, count=count, access_rights_uid=access_rights_uid)


class is_cde_ferme_cadencee(models.Model):
    _inherit = 'is.cde.ferme.cadencee'

    is_societe_comptable = fields.Selection(related='partner_id.is_societe_comptable', store=True, index=True)

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        user = self.env.user
        if user.is_societe_comptable:
            args = args.copy()
            args.append(('is_societe_comptable', '=', user.is_societe_comptable))
        return super(is_cde_ferme_cadencee, self)._search(args, offset=offset, limit=limit, order=order, count=count, access_rights_uid=access_rights_uid)


class is_export_edi(models.Model):
    _inherit = 'is.export.edi'

    is_societe_comptable = fields.Selection(related='partner_id.is_societe_comptable', store=True, index=True)

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        user = self.env.user
        if user.is_societe_comptable:
            args = args.copy()
            args.append(('is_societe_comptable', '=', user.is_societe_comptable))
        return super(is_export_edi, self)._search(args, offset=offset, limit=limit, order=order, count=count, access_rights_uid=access_rights_uid)
