# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from .purchase import CONTEXTE_MAJ_COMMANDE_PK


class stock_picking(models.Model):
    _inherit = 'stock.picking'

    is_societe_comptable = fields.Selection(related='partner_id.is_societe_comptable', store=True, index=True)
    is_reception_gray_id = fields.Many2one('stock.picking', 'Réception Gray', readonly=True, copy=False, index=True,
        help="Réception de Gray dont la validation a validé cette réception PK")
    is_reception_pk_id   = fields.Many2one('stock.picking', 'Réception PK', compute='_compute_is_reception_pk_id',
        help="Réception PK validée par la validation de cette réception de Gray")
    is_reception_pk_liee = fields.Boolean('Réception PK reliée à une commande Gray', compute='_compute_is_reception_pk_liee')


    def _compute_is_reception_pk_liee(self):
        for obj in self:
            obj.is_reception_pk_liee = bool(obj.move_ids.mapped('purchase_line_id.is_ligne_gray_id'))


    def _compute_is_reception_pk_id(self):
        for obj in self:
            reception = False
            if obj.id:
                reception = self.with_context(is_sans_filtre_societe_comptable=True).search(
                    [('is_reception_gray_id', '=', obj.id)], limit=1
                )
            obj.is_reception_pk_id = reception


    def action_annuler_reception(self):
        """Réception PK reliée : annulable uniquement par la réception Gray.
        Réception Gray annulée : réceptions PK validées par celle-ci annulées de la même façon"""
        if not self.env.context.get(CONTEXTE_MAJ_COMMANDE_PK):
            for obj in self:
                if obj.is_reception_gray_id:
                    raise ValidationError(
                        "La réception %s est reliée à la réception Gray %s : annulez la réception Gray"
                        % (obj.name, obj.is_reception_gray_id.name)
                    )
        receptions_pk = self.env['stock.picking'].with_context(
            is_sans_filtre_societe_comptable=True, **{CONTEXTE_MAJ_COMMANDE_PK: True}
        ).search([('is_reception_gray_id', 'in', self.ids), ('state', '=', 'done')])
        res = super().action_annuler_reception()
        for reception_pk in receptions_pk:
            reception_pk.action_annuler_reception()
            reception_pk.message_post(body="Réception annulée par l'annulation de la réception Gray %s" % reception_pk.is_reception_gray_id.name)
        return res


    def _test_reception_pk(self):
        "Réception d'une commande PK reliée à une commande Gray : validée ou annulée uniquement par la réception Gray"
        if self.env.context.get(CONTEXTE_MAJ_COMMANDE_PK):
            return
        for obj in self:
            if obj.is_reception_pk_liee:
                raise ValidationError(
                    "La réception %s est reliée à une commande Gray : elle est validée ou annulée par la réception Gray" % obj.name
                )


    def button_validate(self):
        self._test_reception_pk()
        return super().button_validate()


    def _action_done(self):
        "Contrôle aussi la validation par l'assistant « Transfert » (is_plastigray16), qui ne passe pas par button_validate"
        self._test_reception_pk()
        return super()._action_done()


    def action_cancel(self):
        self._test_reception_pk()
        return super().action_cancel()

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        user = self.env.user
        if user.is_societe_comptable and not self.env.context.get('is_sans_filtre_societe_comptable'):
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
