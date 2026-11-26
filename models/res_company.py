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
