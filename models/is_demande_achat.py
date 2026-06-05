# -*- coding: utf-8 -*-
from odoo import models, fields, api
from .product import societe_comptable_list


class is_demande_achat_fg(models.Model):
    _inherit = 'is.demande.achat.fg'

    is_societe_comptable = fields.Selection(related='fournisseur_id.is_societe_comptable', store=True, tracking=True)

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        # Filtrer par société comptable de l'utilisateur
        user = self.env.user
        if user.is_societe_comptable:
            args = args.copy()
            args.append(('is_societe_comptable', '=', user.is_societe_comptable))
        
        return super(is_demande_achat_fg, self)._search(args, offset=offset, limit=limit, order=order, count=count, access_rights_uid=access_rights_uid)


class is_demande_achat_invest(models.Model):
    _inherit = 'is.demande.achat.invest'

    is_societe_comptable = fields.Selection(related='fournisseur_id.is_societe_comptable', store=True, tracking=True)

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        # Filtrer par société comptable de l'utilisateur
        user = self.env.user
        if user.is_societe_comptable:
            args = args.copy()
            args.append(('is_societe_comptable', '=', user.is_societe_comptable))
        
        return super(is_demande_achat_invest, self)._search(args, offset=offset, limit=limit, order=order, count=count, access_rights_uid=access_rights_uid)


class is_demande_achat_moule(models.Model):
    _inherit = 'is.demande.achat.moule'

    is_societe_comptable = fields.Selection(related='fournisseur_id.is_societe_comptable', store=True, tracking=True)

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        # Filtrer par société comptable de l'utilisateur
        user = self.env.user
        if user.is_societe_comptable:
            args = args.copy()
            args.append(('is_societe_comptable', '=', user.is_societe_comptable))
        
        return super(is_demande_achat_moule, self)._search(args, offset=offset, limit=limit, order=order, count=count, access_rights_uid=access_rights_uid)


class is_demande_achat_serie(models.Model):
    _inherit = 'is.demande.achat.serie'

    is_societe_comptable = fields.Selection(related='fournisseur_id.is_societe_comptable', store=True, tracking=True)

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        # Filtrer par société comptable de l'utilisateur
        user = self.env.user
        if user.is_societe_comptable:
            args = args.copy()
            args.append(('is_societe_comptable', '=', user.is_societe_comptable))
        
        return super(is_demande_achat_serie, self)._search(args, offset=offset, limit=limit, order=order, count=count, access_rights_uid=access_rights_uid)
