# -*- coding: utf-8 -*-
from math import ceil
from odoo import models, fields, api


class account_move(models.Model):
    _inherit = 'account.move'

    is_societe_comptable = fields.Selection(related='partner_id.is_societe_comptable', store=True, index=True)
    is_devise_tunisienne_id = fields.Many2one('res.currency', 'Devise Tunisienne', default=lambda self: self.env['res.currency'].search([('name', '=', 'TND')], limit=1).id)
    is_taux_change_tnd = fields.Float('Taux de change', digits=(12, 4))

    is_total_mp = fields.Monetary(
        'Total matière première',
        currency_field='currency_id',
        compute='_compute_is_totals_pu',
        store=True,
    )
    is_total_amt = fields.Monetary(
        'Total amortissement outillage',
        currency_field='currency_id',
        compute='_compute_is_totals_pu',
        store=True,
    )
    is_total_service = fields.Monetary(
        'Total service',
        currency_field='currency_id',
        compute='_compute_is_totals_pu',
        store=True,
    )

    @api.depends('invoice_line_ids.quantity', 'invoice_line_ids.is_pu_mp', 'invoice_line_ids.is_pu_amt', 'amount_untaxed')
    def _compute_is_totals_pu(self):
        for move in self:
            total_mp = sum(l.quantity * l.is_pu_mp for l in move.invoice_line_ids)
            total_amt = sum(l.quantity * l.is_pu_amt for l in move.invoice_line_ids)
            move.is_total_mp = total_mp
            move.is_total_amt = total_amt
            move.is_total_service = move.amount_untaxed - total_mp - total_amt

    is_nb_pieces = fields.Integer('Nombre de pièces', compute='_compute_is_conditionnement', store=True)
    is_nb_colis = fields.Integer('Nombre de colis', compute='_compute_is_conditionnement', store=True)
    is_nb_palettes = fields.Integer('Nombre de palettes', compute='_compute_is_conditionnement', store=True)

    @api.depends('invoice_line_ids.quantity', 'invoice_line_ids.product_id')
    def _compute_is_conditionnement(self):
        for move in self:
            nb_pieces = 0
            nb_colis = 0
            nb_palettes = 0
            for line in move.invoice_line_ids:
                nb_pieces += int(line.quantity)
                packaging = line.product_id.packaging_ids[:1]
                if packaging and packaging.qty:
                    line_colis = ceil(line.quantity / packaging.qty)
                    nb_colis += line_colis
                    colis_par_palette = (packaging.ul_qty or 1) * (packaging.rows or 1)
                    nb_palettes += ceil(line_colis / colis_par_palette)
            move.is_nb_pieces = nb_pieces
            move.is_nb_colis = nb_colis
            move.is_nb_palettes = nb_palettes

    def imprimer_simple_double(self):
        action = super().imprimer_simple_double()
        if action and action.get('url'):
            attachment_id = int(action['url'].split('/web/content/')[1].split('?')[0])
            attachment = self.env['ir.attachment'].browse(attachment_id)
            if len(self) == 1:
                new_name = 'Facture-Plasti-ka-%s.pdf' % self.name.replace('/', '').replace(' ', '')
            else:
                new_name = 'Factures-Plasti-ka.pdf'
            attachment.write({'name': new_name})
            action['url'] = '/web/content/%s?download=true&filename=%s' % (attachment_id, new_name)
        return action

    def _fill_taux_change(self):
        """Remplit is_taux_change_tnd depuis is.taux.change pour la date et la devise tunisienne de chaque facture."""
        for move in self:
            if move.invoice_date and move.is_devise_tunisienne_id:
                taux = self.env['is.taux.change'].search([
                    ('date', '=', move.invoice_date),
                    ('devise2_id', '=', move.is_devise_tunisienne_id.id),
                ], limit=1)
                move.is_taux_change_tnd = taux.taux if taux else 0.0

    @api.onchange('invoice_date')
    def _onchange_invoice_date_taux_change(self):
        self._fill_taux_change()

    is_picking_count = fields.Integer('Nombre de livraisons', compute='_compute_is_picking_count')

    def _compute_is_picking_count(self):
        for move in self:
            move.is_picking_count = self.env['stock.picking'].search_count([
                ('state', '!=', 'cancel'),
                '|',
                ('sale_id.invoice_ids', '=', move.id),
                ('purchase_id.invoice_ids', '=', move.id),
            ])

    def action_view_related_pickings(self):
        """Affiche les livraisons associées aux lignes de cette facture."""
        pickings = self.env['stock.picking']
        # Récupérer les pickings liés via les sales orders ou les mouvements de stock
        if self.invoice_origin and self.invoice_origin.startswith('Sale Order'):
            sales = self.env['sale.order'].search([('name', 'ilike', self.invoice_origin)])
            pickings = self.env['stock.picking'].search([('sale_id', 'in', sales.ids)])
        else:
            # Récupérer les pickings des lignes de facture
            pickings = self.env['stock.picking'].search([
                ('state', '!=', 'cancel'),
                '|',
                ('sale_id.invoice_ids', '=', self.id),
                ('purchase_id.invoice_ids', '=', self.id),
            ])
        
        action = self.env.ref('stock.action_picking_tree_all').read()[0]
        action['domain'] = [('id', 'in', pickings.ids)]
        action['context'] = {'default_picking_type_id': False}
        return action

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        user = self.env.user
        if user.is_societe_comptable:
            args = args.copy()
            args.append(('is_societe_comptable', '=', user.is_societe_comptable))
        return super(account_move, self)._search(args, offset=offset, limit=limit, order=order, count=count, access_rights_uid=access_rights_uid)
