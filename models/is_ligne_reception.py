# -*- coding: utf-8 -*-
from odoo import models, fields, api


class is_ligne_reception(models.Model):
    _inherit = 'is.ligne.reception'

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        # Filtrer par société comptable de l'utilisateur
        user = self.env.user
        if user.is_societe_comptable:
            args = args.copy()
            args.append(('is_societe_comptable', '=', user.is_societe_comptable))
        
        return super(is_ligne_reception, self)._search(args, offset=offset, limit=limit, order=order, count=count, access_rights_uid=access_rights_uid)
