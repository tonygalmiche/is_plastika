# -*- coding: utf-8 -*-
from odoo import models, fields, api


class account_move(models.Model):
    _inherit = 'account.move'

    is_societe_comptable = fields.Selection(related='partner_id.is_societe_comptable', store=True, index=True)
    is_devise_tunisienne_id = fields.Many2one('res.currency', 'Devise Tunisienne', default=lambda self: self.env['res.currency'].search([('name', '=', 'TND')], limit=1).id)
    is_taux_change_tnd = fields.Float('Taux de change', digits=(12, 4))

    def _fill_taux_change(self):
        """Remplit is_taux_change_tnd depuis is.taux.change pour la date et la devise tunisienne de chaque facture."""
        for move in self:
            if move.invoice_date and move.is_devise_tunisienne_id:
                taux = self.env['is.taux.change'].search([
                    ('date', '=', move.invoice_date),
                    ('devise2_id', '=', move.is_devise_tunisienne_id.id),
                ], limit=1)
                move.is_taux_change_tnd = taux.taux if taux else 0.0

    @api.onchange('invoice_date')
    def _onchange_invoice_date_taux_change(self):
        self._fill_taux_change()

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        user = self.env.user
        if user.is_societe_comptable:
            args = args.copy()
            args.append(('is_societe_comptable', '=', user.is_societe_comptable))
        return super(account_move, self)._search(args, offset=offset, limit=limit, order=order, count=count, access_rights_uid=access_rights_uid)
