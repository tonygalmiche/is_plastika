# -*- coding: utf-8 -*-
from odoo import models, fields, api


class is_certifications_qualite_suivi(models.Model):
    _inherit = 'is.certifications.qualite.suivi'

    is_societe_comptable = fields.Selection(related='partner_id.is_societe_comptable')

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        user = self.env.user
        if user.is_societe_comptable:
            args = args.copy()
            args.append(('partner_id.is_societe_comptable', '=', user.is_societe_comptable))
        return super(is_certifications_qualite_suivi, self)._search(args, offset=offset, limit=limit, order=order, count=count, access_rights_uid=access_rights_uid)
