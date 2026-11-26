# -*- coding: utf-8 -*-
import re
from odoo import models, fields
from odoo.exceptions import ValidationError


class res_partner(models.Model):
    _inherit = 'res.partner'

    is_fournisseur_pk_id = fields.Many2one(
        'res.partner', 'Fournisseur de PK', tracking=True, copy=False,
        domain=[('is_company', '=', True), ('supplier', '=', True), ('is_societe_comptable', '=', 'plasti_ka')],
        help="Fournisseur de la commande de PK générée à la validation d'une commande de Gray à ce fournisseur",
    )
    is_fournisseur_gray_id = fields.Many2one(
        'res.partner', 'Fournisseur de Gray', compute='_compute_is_fournisseur_gray_id',
        help="Fournisseur de Gray dont ce fournisseur est le « Fournisseur de PK »",
    )


    def _compute_is_fournisseur_gray_id(self):
        for obj in self:
            fournisseur = False
            if obj.id:
                fournisseur = self.search([('is_fournisseur_pk_id', '=', obj.id)], limit=1)
            obj.is_fournisseur_gray_id = fournisseur


    def creer_fournisseur_pk_action(self):
        """Crée le fournisseur de PK par copie du fournisseur de Gray (adresse reprise) :
        nom sans « PLASTI-KA chez », code suffixé par PK, société comptable Plasti-ka, sans liste de prix d'achat"""
        self.ensure_one()
        if not self.is_company or not self.supplier or self.is_societe_comptable != 'plastigray':
            raise ValidationError("Action réservée aux sociétés fournisseurs de Plastigray")
        if self.is_fournisseur_pk_id:
            raise ValidationError("Le fournisseur de PK est déjà renseigné (%s)" % self.is_fournisseur_pk_id.display_name)
        name = re.sub(r'^\s*PLASTI-KA\s+chez\s+', '', self.name or '', flags=re.IGNORECASE).strip()
        fournisseur = self.copy({
            'name'                 : name,
            'is_societe_comptable' : 'plasti_ka',
            'supplier'             : True,
            'customer'             : False,
            'pricelist_purchase_id': False,
        })
        # La copie de is_plastigray16 impose « (copie) » sur les codes : ils sont remplacés ensuite.
        # Le nom est réécrit pour recalculer le nom affiché (« NOM (code/code adresse) »), qui ne dépend pas des codes
        fournisseur.write({
            'name'       : name,
            'is_code'    : '%sPK' % (self.is_code or ''),
            'is_adr_code': self.is_adr_code,
        })
        self.is_fournisseur_pk_id = fournisseur.id
        return {
            'type'     : 'ir.actions.act_window',
            'res_model': 'res.partner',
            'res_id'   : fournisseur.id,
            'view_mode': 'form',
            'target'   : 'current',
        }
