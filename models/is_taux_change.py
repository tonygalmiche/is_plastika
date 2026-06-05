# -*- coding: utf-8 -*-
from odoo import models, fields, api
import requests
import logging

_logger = logging.getLogger(__name__)


class is_taux_change(models.Model):
    _name = 'is.taux.change'
    _description = 'Taux de change'
    _order = 'date desc'

    date = fields.Date('Date', required=True, default=fields.Date.today)
    devise1_id = fields.Many2one('res.currency', 'Devise 1', required=True, default=lambda self: self.env.ref('base.EUR').id)
    devise2_id = fields.Many2one('res.currency', 'Devise 2', required=True)
    taux = fields.Float('Taux de change', digits=(12, 6), required=True)

    _sql_constraints = [
        ('unique_date_devises', 'UNIQUE(date, devise1_id, devise2_id)', 'Un taux de change existe déjà pour ce jour et ces devises')
    ]

    @api.model
    def recuperer_taux_change_jour(self):
        """Récupère automatiquement le taux de change EUR/TND du jour via API gratuite sans clé"""
        from datetime import date as date_class
        today = date_class.today()
        
        try:
            # API gratuite sans authentification : exchangerate-api.com (1500 req/mois)
            url = "https://api.exchangerate-api.com/v4/latest/EUR"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Récupérer le taux TND
            rates = data.get('rates', {})
            if 'TND' not in rates:
                _logger.warning("Aucun taux TND trouvé dans la réponse API")
                return
            
            taux = float(rates['TND'])
            
            # Chercher le dinars tunisien
            tnd = self.env['res.currency'].search([('name', '=', 'TND')], limit=1)
            if not tnd:
                _logger.warning("Devise TND non trouvée dans le système")
                return
            
            eur = self.env.ref('base.EUR')
            
            # Vérifier si le taux existe déjà pour aujourd'hui
            existing = self.search([
                ('date', '=', today),
                ('devise1_id', '=', eur.id),
                ('devise2_id', '=', tnd.id)
            ], limit=1)
            
            if not existing:
                self.create({
                    'date': today,
                    'devise1_id': eur.id,
                    'devise2_id': tnd.id,
                    'taux': taux
                })
                _logger.info(f"Taux de change EUR/TND du {today} : {taux} créé avec succès")
            else:
                existing.write({'taux': taux})
                _logger.info(f"Taux de change EUR/TND du {today} : {taux} mis à jour")
            
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération du taux de change: {str(e)}")
