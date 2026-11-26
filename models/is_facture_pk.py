# -*- coding: utf-8 -*-
from odoo import models, fields, api


class is_facture_pk(models.Model):
    _inherit = 'is.facture.pk'

    taux_devise_dinar = fields.Float(default=lambda self: self.env.company.get_taux_facturation_pk()[0])
    taux_commission   = fields.Float(default=lambda self: self.env.company.get_taux_facturation_pk()[1])


    @api.onchange('date_facture')
    def onchange_date_facture_taux_pk(self):
        "Facture sans ligne : taux valides à la date de la facture (avec des lignes, la facture garde ses taux car les montants en € des lignes en dépendent)"
        if not self.line_ids:
            self.taux_devise_dinar, self.taux_commission = self.env.company.get_taux_facturation_pk(self.date_facture)


    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('date_facture') and ('taux_devise_dinar' not in vals or 'taux_commission' not in vals):
                taux_devise_dinar, taux_commission = self.env.company.get_taux_facturation_pk(vals['date_facture'])
                vals.setdefault('taux_devise_dinar', taux_devise_dinar)
                vals.setdefault('taux_commission'  , taux_commission)
        return super().create(vals_list)
