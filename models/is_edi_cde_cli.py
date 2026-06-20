# -*- coding: utf-8 -*-
from odoo import models, fields, api


class is_edi_cde_cli(models.Model):
    _inherit = 'is.edi.cde.cli'

    is_societe_comptable = fields.Selection(related='partner_id.is_societe_comptable', store=True, index=True)

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        user = self.env.user
        if user.is_societe_comptable:
            args = args.copy()
            args.append(('is_societe_comptable', '=', user.is_societe_comptable))
        return super(is_edi_cde_cli, self)._search(args, offset=offset, limit=limit, order=order, count=count, access_rights_uid=access_rights_uid)
