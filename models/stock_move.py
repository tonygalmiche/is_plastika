# -*- coding: utf-8 -*-
from odoo import models, fields, api
from .purchase import CONTEXTE_MAJ_COMMANDE_PK


# Contexte de la synchronisation des réceptions PK : réceptions et mouvements PK lus sans le filtre par société comptable
CONTEXTE_SANS_FILTRE = {'is_sans_filtre_societe_comptable': True, CONTEXTE_MAJ_COMMANDE_PK: True}


class stock_move(models.Model):
    _inherit = 'stock.move'

    is_societe_comptable = fields.Selection(related='product_id.product_tmpl_id.is_societe_comptable', store=True, index=True)

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        user = self.env.user
        if user.is_societe_comptable and not self.env.context.get('is_sans_filtre_societe_comptable'):
            args = args.copy()
            args.append(('is_societe_comptable', '=', user.is_societe_comptable))
        return super(stock_move, self)._search(args, offset=offset, limit=limit, order=order, count=count, access_rights_uid=access_rights_uid)


    def _get_moves_gray_lies_pk(self):
        "Mouvements en cours de réceptions de Gray dont la ligne de commande est reliée à une ligne de commande PK"
        return self.filtered(lambda m: m.state not in ('done', 'cancel') and m.purchase_line_id.is_ligne_pk_id)


    def _action_done(self, cancel_backorder=False):
        """Réception Gray validée : validation de la réception PK pour les mêmes quantités
        (reliquat PK créé ou annulé comme celui de Gray)"""
        moves_gray_ids = self._get_moves_gray_lies_pk().ids
        res = super()._action_done(cancel_backorder=cancel_backorder)
        if moves_gray_ids:
            moves_gray = self.browse(moves_gray_ids).with_context(**CONTEXTE_SANS_FILTRE).filtered(lambda m: m.state == 'done')
            moves_gray._valider_receptions_pk(cancel_backorder)
        return res


    def _valider_receptions_pk(self, cancel_backorder):
        #** Quantités reçues par ligne de commande PK (unité de la ligne de commande PK)
        qt_par_ligne_pk = {}
        for move in self:
            ligne_gray = move.purchase_line_id
            ligne_pk   = ligne_gray.is_ligne_pk_id
            qt = move.product_uom._compute_quantity(move.quantity_done, ligne_gray.product_uom)
            qt = ligne_gray.product_uom._compute_quantity(qt, ligne_pk.product_uom)
            qt_par_ligne_pk[ligne_pk] = qt_par_ligne_pk.get(ligne_pk, 0) + qt

        #** Quantités faites sur les mouvements PK en cours
        moves_pk = self.env['stock.move']
        for ligne_pk, qt in qt_par_ligne_pk.items():
            for move_pk in ligne_pk.move_ids.filtered(lambda m: m.state not in ('done', 'cancel')):
                qt_move = min(qt, ligne_pk.product_uom._compute_quantity(move_pk.product_uom_qty, ligne_pk.product_uom))
                if qt_move <= 0:
                    continue
                move_pk.quantity_done = ligne_pk.product_uom._compute_quantity(qt_move, move_pk.product_uom)
                moves_pk |= move_pk
                qt -= qt_move

        #** Validation des réceptions PK (tous leurs mouvements pour créer ou annuler le reliquat)
        pickings_pk = moves_pk.mapped('picking_id')
        moves_todo = pickings_pk.move_ids.filtered(lambda m: m.state not in ('done', 'cancel'))
        if moves_todo:
            moves_todo._action_done(cancel_backorder=cancel_backorder)
            reception_gray = self.mapped('picking_id')[:1]
            for picking in pickings_pk:
                picking.write({'date_done': fields.Datetime.now(), 'is_reception_gray_id': reception_gray.id})
                picking.message_post(body="Réception validée par la réception Gray %s" % ', '.join(self.mapped('picking_id.name')))


    def _action_cancel(self):
        "Reliquat ou réception Gray annulé : mouvements PK en cours de la ligne PK annulés s'il ne reste rien à recevoir côté Gray"
        lignes_gray_ids = self._get_moves_gray_lies_pk().mapped('purchase_line_id').ids
        res = super()._action_cancel()
        if lignes_gray_ids:
            lignes_gray = self.env['purchase.order.line'].browse(lignes_gray_ids).with_context(**CONTEXTE_SANS_FILTRE)
            for ligne_gray in lignes_gray:
                if ligne_gray.move_ids.filtered(lambda m: m.state not in ('done', 'cancel')):
                    continue
                moves_pk = ligne_gray.is_ligne_pk_id.move_ids.filtered(lambda m: m.state not in ('done', 'cancel'))
                if moves_pk:
                    moves_pk._action_cancel()
        return res
