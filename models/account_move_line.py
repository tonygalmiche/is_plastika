# -*- coding: utf-8 -*-
from odoo import models, fields, api


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    # PU.MP : Part unitaire de matière première = Part Matière + Part composant + Part emballage
    is_pu_mp = fields.Float(
        'PU.MP',
        digits=(14, 4),
        help="Part unitaire de matière première = Part Matière + Part composant + Part emballage",
    )

    # PU.AMT : Part unitaire amortissement moule = Amt client négocié
    is_pu_amt = fields.Float(
        'PU.AMT',
        digits=(14, 4),
        help="Part unitaire amortissement moule = Amt client négocié",
    )

    # PU.PF : Part unitaire produit fini = Valeur ajoutée = Prix de vente - PU.MP - PU.AMT
    is_pu_pf = fields.Float(
        'PU.PF',
        digits=(14, 4),
        help="Part unitaire produit fini = Valeur ajoutée = Prix de vente - PU.MP - PU.AMT",
    )

    def _get_tarif_cial(self):
        """Recherche le tarif commercial indice 999 pour le client et l'article de la ligne."""
        partner = self.move_id.partner_id.commercial_partner_id
        product_tmpl = self.product_id.product_tmpl_id
        if not partner or not product_tmpl:
            return False
        return self.env['is.tarif.cial'].search([
            ('partner_id', '=', partner.id),
            ('product_id', '=', product_tmpl.id),
            ('indice_prix', '=', 999),
        ], limit=1)

    def _fill_from_tarif_cial(self):
        """Remplit price_unit et les champs PU depuis le tarif commercial (indice=999)."""
        for line in self:
            tarif = line._get_tarif_cial()
            if tarif:
                pu_mp  = tarif.part_matiere + tarif.part_composant + tarif.part_emballage
                pu_amt = tarif.amortissement_moule
                pu_pf  = tarif.prix_vente - pu_mp - pu_amt
                line.price_unit = tarif.prix_vente
                line.is_pu_mp   = pu_mp
                line.is_pu_amt  = pu_amt
                line.is_pu_pf   = pu_pf
            else:
                line.is_pu_mp  = 0.0
                line.is_pu_amt = 0.0
                line.is_pu_pf  = 0.0

    @api.onchange('product_id')
    def _onchange_product_id_pu(self):
        self._fill_from_tarif_cial()
