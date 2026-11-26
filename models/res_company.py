# -*- coding: utf-8 -*-
from odoo import models, fields
from odoo.exceptions import ValidationError


class is_taux_facturation_pk(models.Model):
    _name = 'is.taux.facturation.pk'
    _description = 'Taux devise dinar et commission pour la facturation PK'
    _order = 'date_debut'

    company_id        = fields.Many2one('res.company', 'Société', required=True, ondelete='cascade', index=True)
    date_debut        = fields.Date('Date de début', required=True, index=True)
    taux_devise_dinar = fields.Float('Taux devise dinar' , digits=(12, 4), required=True)
    taux_commission   = fields.Float('Taux de commission', digits=(12, 4), required=True)

    _sql_constraints = [
        ('unique_company_date_debut', 'UNIQUE(company_id, date_debut)', 'Une ligne existe déjà pour cette date de début'),
    ]


class res_company(models.Model):
    _inherit = 'res.company'

    is_taux_facturation_pk_ids = fields.One2many('is.taux.facturation.pk', 'company_id', 'Taux devise dinar et commission')
    is_maj_listes_gray_vsb     = fields.Boolean('Mise à jour des listes de prix Gray possible', compute='_compute_is_maj_listes_gray_vsb')
    is_client_gray_pk_id       = fields.Many2one('res.partner', 'Client Gray de PK',
        domain=[('is_societe_comptable', '=', 'plasti_ka'), ('is_company', '=', True)],
        help="Client (société comptable Plasti-ka) des factures de refacturation à Gray des factures fournisseur PK")


    def _compute_is_maj_listes_gray_vsb(self):
        "Bouton réservé à un utilisateur sans société comptable (il voit les listes de prix des 2 sociétés)"
        for obj in self:
            obj.is_maj_listes_gray_vsb = not self.env.user.is_societe_comptable


    def get_ligne_taux_facturation_pk(self, date=False):
        "Ligne du tableau des taux valide à la date indiquée (aujourd'hui par défaut) : date de début la plus récente avant ou à cette date"
        self.ensure_one()
        date = date or fields.Date.context_today(self)
        return self.env['is.taux.facturation.pk'].search([
            ('company_id', '=', self.id),
            ('date_debut', '<=', date),
        ], order='date_debut desc', limit=1)


    def get_taux_facturation_pk(self, date=False):
        """Taux devise dinar et taux de commission valides à la date indiquée (aujourd'hui par défaut) :
        ligne du tableau avec la date de début la plus récente avant ou à cette date, sinon les 2 champs de la société"""
        ligne = self.get_ligne_taux_facturation_pk(date)
        if ligne:
            return ligne.taux_devise_dinar, ligne.taux_commission
        return self.is_taux_devise_dinar, self.is_taux_commission


    def maj_listes_prix_gray_action(self):
        "Met à jour toutes les listes de prix Gray générées depuis les listes de prix TND des fournisseurs de PK"
        if self.env.user.is_societe_comptable:
            raise ValidationError(
                "Action réservée à un utilisateur sans société comptable (il doit voir les listes de prix de Plastigray et de Plasti-ka)"
            )
        pricelists = self.env['product.pricelist'].search([
            ('type', '=', 'purchase'),
            ('currency_id.name', '=', 'TND'),
            ('partner_id', '!=', False),
        ]).filtered('is_maj_liste_gray_vsb')
        if not pricelists:
            raise ValidationError("Aucune liste de prix TND d'un fournisseur de PK relié à un fournisseur de Gray")
        pricelists.maj_liste_prix_gray_action()
        return {
            'type': 'ir.actions.client',
            'tag' : 'display_notification',
            'params': {
                'type'   : 'success',
                'message': "%s liste(s) de prix Gray mise(s) à jour : %s" % (len(pricelists), ', '.join(pricelists.mapped('name'))),
                'sticky' : True,
            },
        }
