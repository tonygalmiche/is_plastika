# -*- coding: utf-8 -*-
from odoo import models, fields, api


class is_bl_manuel(models.Model):
    _inherit = 'is.bl.manuel'

    is_societe_comptable = fields.Selection(related='destinataire_id.is_societe_comptable', store=True, index=True)

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        user = self.env.user
        if user.is_societe_comptable:
            args = args.copy()
            args.append(('is_societe_comptable', '=', user.is_societe_comptable))
        return super(is_bl_manuel, self)._search(args, offset=offset, limit=limit, order=order, count=count, access_rights_uid=access_rights_uid)
