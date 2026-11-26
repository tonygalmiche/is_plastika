# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from .product import societe_comptable_list


# Champs des lignes d'une commande Gray reliée à une commande PK qui ne sont plus modifiables après validation
CHAMPS_LIGNE_VERROUILLES = ('product_id', 'product_qty', 'product_uom', 'price_unit', 'date_planned')

# Contexte qui autorise la modification d'une commande Gray reliée à une commande PK
CONTEXTE_MAJ_COMMANDE_PK = 'is_maj_commande_pk'


class purchase_order(models.Model):
    _inherit = 'purchase.order'

    is_societe_comptable = fields.Selection(related='partner_id.is_societe_comptable', store=True, index=True)
    is_commande_pk_id    = fields.Many2one('purchase.order', 'Commande PK' , readonly=True, copy=False, index=True,
        help="Commande au fournisseur de PK générée à la validation de cette commande de Gray")
    is_commande_gray_id  = fields.Many2one('purchase.order', 'Commande Gray', readonly=True, copy=False, index=True,
        help="Commande de Gray dont la validation a généré cette commande au fournisseur de PK")


    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        user = self.env.user
        if user.is_societe_comptable and not self.env.context.get('is_sans_filtre_societe_comptable'):
            args = args.copy()
            args.append(('is_societe_comptable', '=', user.is_societe_comptable))
        return super()._search(args, offset=offset, limit=limit, order=order, count=count, access_rights_uid=access_rights_uid)


    def button_approve(self, force=False):
        res = super().button_approve(force=force)
        for obj in self:
            obj._creer_commande_pk()
        return res


    def button_cancel(self):
        "Commande PK reliée : annulable uniquement par la commande Gray ; commande Gray annulée : commande PK annulée"
        if not self.env.context.get(CONTEXTE_MAJ_COMMANDE_PK):
            for obj in self:
                if obj.is_commande_gray_id:
                    raise ValidationError(
                        "La commande %s est reliée à la commande Gray %s : annulez la commande Gray"
                        % (obj.name, obj.is_commande_gray_id.name)
                    )
        res = super().button_cancel()
        commandes_pk = self.mapped('is_commande_pk_id').filtered(lambda c: c.state != 'cancel')
        if commandes_pk:
            commandes_pk.with_context(**{CONTEXTE_MAJ_COMMANDE_PK: True, 'is_sans_filtre_societe_comptable': True}).button_cancel()
            for obj in self.filtered('is_commande_pk_id'):
                obj.message_post(body="Commande PK %s annulée" % obj.is_commande_pk_id.name)
        return res


    def _creer_commande_pk(self):
        """Commande Gray validée chez un fournisseur relié à un fournisseur de PK : création et validation de la commande PK
        (article comptable PK, prix TND de la liste d'achat du fournisseur de PK, lien ligne à ligne)"""
        self.ensure_one()
        fournisseur_pk = self.partner_id.is_fournisseur_pk_id
        if not fournisseur_pk or self.is_commande_gray_id:
            return False
        if self.is_commande_pk_id and self.is_commande_pk_id.state != 'cancel':
            return False
        liste_tnd = fournisseur_pk.pricelist_purchase_id
        if not liste_tnd:
            raise ValidationError(
                "Le fournisseur de PK « %s » n'a pas de liste de prix d'achat (TND)" % fournisseur_pk.display_name
            )
        lignes = self.order_line.filtered(lambda l: not l.display_type)
        for line in lignes:
            if not line.product_id.is_article_comptable_pk_id:
                raise ValidationError(
                    "L'article %s n'a pas d'article comptable PK (fiche article, onglet Comptabilité)" % line.product_id.is_code
                )
        commande_pk = self.create({
            'partner_id'         : fournisseur_pk.id,
            'pricelist_id'       : liste_tnd.id,
            'currency_id'        : liste_tnd.currency_id.id,
            'fiscal_position_id' : self.env['account.fiscal.position']._get_fiscal_position(fournisseur_pk).id,
            'payment_term_id'    : fournisseur_pk.property_supplier_payment_term_id.id,
            'picking_type_id'    : self.picking_type_id.id,
            'location_id'        : self.location_id.id,
            'date_order'         : self.date_order,
            'origin'             : self.name,
            'is_demandeur_id'    : self.is_demandeur_id.id,
            'is_commande_gray_id': self.id,
        })
        liste_tnd = liste_tnd.with_context(is_sans_filtre_societe_comptable=True)
        for line in lignes:
            # Prix TND de l'article de Gray (la liste TND est saisie par article de Gray, pas par article comptable)
            price, justification = liste_tnd.price_get(
                product = line.product_id,
                qty     = line.product_qty,
                date    = line.date_planned.date(),
            )
            ligne_pk = self.env['purchase.order.line'].with_context(**{CONTEXTE_MAJ_COMMANDE_PK: True}).create({
                'order_id'        : commande_pk.id,
                'product_id'      : line.product_id.is_article_comptable_pk_id.id,
                'name'            : line.name,
                'product_qty'     : line.product_qty,
                'product_uom'     : line.product_uom.id,
                'date_planned'    : line.date_planned,
                'price_unit'      : price,
                'is_justification': justification,
                'is_ligne_gray_id': line.id,
            })
            ligne_pk._compute_tax_id()
            line.with_context(**{CONTEXTE_MAJ_COMMANDE_PK: True}).is_ligne_pk_id = ligne_pk.id
        commande_pk.test_prix0()
        self.is_commande_pk_id = commande_pk.id
        commande_pk.button_confirm()
        self.message_post(body="Commande PK %s créée" % commande_pk.name)
        commande_pk.message_post(body="Commande créée à la validation de la commande Gray %s" % self.name)
        return commande_pk


class purchase_order_line(models.Model):
    _inherit = 'purchase.order.line'

    is_societe_comptable = fields.Selection(related='order_id.is_societe_comptable', store=True, index=True)
    is_ligne_pk_id       = fields.Many2one('purchase.order.line', 'Ligne commande PK' , readonly=True, copy=False, index=True)
    is_ligne_gray_id     = fields.Many2one('purchase.order.line', 'Ligne commande Gray', readonly=True, copy=False, index=True)


    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        user = self.env.user
        if user.is_societe_comptable and not self.env.context.get('is_sans_filtre_societe_comptable'):
            args = args.copy()
            args.append(('is_societe_comptable', '=', user.is_societe_comptable))
        return super()._search(args, offset=offset, limit=limit, order=order, count=count, access_rights_uid=access_rights_uid)


    def _test_commande_gray_verrouillee(self, orders):
        """Commande Gray validée et reliée à une commande PK : plus de modification (annuler et recommencer).
        Commande PK reliée à une commande Gray : jamais modifiable (elle suit la commande Gray)"""
        if self.env.context.get(CONTEXTE_MAJ_COMMANDE_PK):
            return
        for order in orders:
            if order.state in ('purchase', 'done') and order.is_commande_pk_id and order.is_commande_pk_id.state != 'cancel':
                raise ValidationError(
                    "La commande %s est reliée à la commande PK %s : elle n'est plus modifiable après validation "
                    "(annulez-la puis recommencez)" % (order.name, order.is_commande_pk_id.name)
                )
            if order.is_commande_gray_id:
                raise ValidationError(
                    "La commande %s est reliée à la commande Gray %s : elle n'est pas modifiable"
                    % (order.name, order.is_commande_gray_id.name)
                )


    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        self._test_commande_gray_verrouillee(records.mapped('order_id'))
        return records


    def write(self, vals):
        if set(vals) & set(CHAMPS_LIGNE_VERROUILLES):
            self._test_commande_gray_verrouillee(self.mapped('order_id'))
        return super().write(vals)


    def unlink(self):
        self._test_commande_gray_verrouillee(self.mapped('order_id'))
        return super().unlink()
