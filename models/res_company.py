# -*- coding: utf-8 -*-
from odoo import models, fields


class is_taux_facturation_pk(models.Model):
    _name = 'is.taux.facturation.pk'
    _description = 'Taux devise dinar et commission pour la facturation PK'
    _order = 'date_debut desc'

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


    def get_taux_facturation_pk(self, date=False):
        """Taux devise dinar et taux de commission valides à la date indiquée (aujourd'hui par défaut) :
        ligne du tableau avec la date de début la plus récente avant ou à cette date, sinon les 2 champs de la société"""
        self.ensure_one()
        date = date or fields.Date.context_today(self)
        ligne = self.env['is.taux.facturation.pk'].search([
            ('company_id', '=', self.id),
            ('date_debut', '<=', date),
        ], order='date_debut desc', limit=1)
        if ligne:
            return ligne.taux_devise_dinar, ligne.taux_commission
        return self.is_taux_devise_dinar, self.is_taux_commission
