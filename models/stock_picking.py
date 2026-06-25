# -*- coding: utf-8 -*-
from odoo import models, fields, api


class stock_picking(models.Model):
    _inherit = 'stock.picking'

    is_societe_comptable = fields.Selection(related='partner_id.is_societe_comptable', store=True, index=True)

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        user = self.env.user
        if user.is_societe_comptable:
            args = args.copy()
            args.append(('is_societe_comptable', '=', user.is_societe_comptable))
        return super(stock_picking, self)._search(args, offset=offset, limit=limit, order=order, count=count, access_rights_uid=access_rights_uid)

    def creer_factures_action(self):
        """Surcharge pour alimenter le taux de change après création des factures.
        Les champs PU et price_unit sont injectés à la création via _prepare_invoice_line()."""
        res = super().creer_factures_action()
        invoices = self.mapped('sale_id.invoice_ids').filtered(lambda m: m.state == 'draft')
        invoices._fill_taux_change()
        return res
