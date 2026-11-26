# -*- coding: utf-8 -*-
from math import ceil
from markupsafe import Markup
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class account_move(models.Model):
    _inherit = 'account.move'

    is_societe_comptable = fields.Selection(related='partner_id.is_societe_comptable', store=True, index=True)
    is_devise_tunisienne_id = fields.Many2one('res.currency', 'Devise Tunisienne', default=lambda self: self.env['res.currency'].search([('name', '=', 'TND')], limit=1).id)
    is_taux_change_tnd = fields.Float('Taux de change', digits=(12, 4))

    #** Refacturation à Gray des factures fournisseur PK ***********************
    is_facture_refacturation_id = fields.Many2one('account.move', 'Refacturée à Gray par', copy=False, readonly=True, index=True,
        help="Facture client à Gray qui refacture cette facture fournisseur PK")
    is_factures_refacturees_ids = fields.One2many('account.move', 'is_facture_refacturation_id', 'Factures fournisseur PK refacturées', readonly=True)
    is_a_refacturer = fields.Boolean('À refacturer à Gray', compute='_compute_is_a_refacturer', store=True, index=True,
        help="Facture fournisseur PK validée, avec des réceptions reliées à des commandes Gray, pas encore refacturée à Gray (ou refacturation annulée)")


    def _get_lignes_a_refacturer(self):
        "Lignes de la facture fournisseur PK dont la réception est reliée à une commande Gray"
        return self.invoice_line_ids.filtered(
            lambda l: l.display_type == 'product' and l.is_move_id.purchase_line_id.is_ligne_gray_id
        )


    @api.depends('move_type', 'state', 'is_societe_comptable', 'invoice_line_ids.is_move_id',
                 'is_facture_refacturation_id', 'is_facture_refacturation_id.state')
    def _compute_is_a_refacturer(self):
        for obj in self:
            obj.is_a_refacturer = bool(
                obj.move_type == 'in_invoice' and obj.state == 'posted' and obj.is_societe_comptable == 'plasti_ka'
                and (not obj.is_facture_refacturation_id or obj.is_facture_refacturation_id.state == 'cancel')
                and obj._get_lignes_a_refacturer()
            )


    def refacturer_gray_action(self):
        """Factures fournisseur PK sélectionnées : une facture client à Gray (brouillon, en EUR) par fournisseur,
        une ligne de commentaire par facture fournisseur, une ligne par réception (article comptable PK,
        code Gray et réception Gray dans le libellé, unité et prix de la ligne de commande Gray)"""
        client = self.env.company.is_client_gray_pk_id
        if not client:
            raise ValidationError("Le client Gray de PK n'est pas renseigné (fiche société)")
        factures = self.filtered('is_a_refacturer')
        if not factures:
            raise ValidationError("Aucune facture fournisseur PK à refacturer à Gray dans la sélection")
        factures_gray = self.env['account.move']
        position_fiscale = self.env['account.fiscal.position']._get_fiscal_position(client)
        for fournisseur in factures.mapped('partner_id'):
            factures_fournisseur = factures.filtered(lambda f: f.partner_id == fournisseur).sorted(lambda f: (f.invoice_date, f.id))
            lignes = []
            for facture in factures_fournisseur:
                lignes.append((0, 0, {
                    'display_type': 'line_note',
                    'name'        : "REFACTURATION %s %s" % (fournisseur.name, facture.supplier_invoice_number or facture.name),
                }))
                for ligne in facture._get_lignes_a_refacturer():
                    article_pk = ligne.product_id
                    if not article_pk.property_account_income_id:
                        raise ValidationError(
                            "L'article comptable PK %s n'a pas de compte de produits (fiche article, onglet Comptabilité)" % article_pk.is_code
                        )
                    ligne_gray     = ligne.is_move_id.purchase_line_id.is_ligne_gray_id
                    article_gray   = ligne_gray.product_id
                    reception_gray = ligne.is_move_id.picking_id.is_reception_gray_id
                    lignes.append((0, 0, {
                        'product_id'                     : article_pk.id,
                        'name'                           : "%s %s - %s" % (article_gray.is_code, article_gray.name, reception_gray.name or ''),
                        'quantity'                       : ligne.product_uom_id._compute_quantity(ligne.quantity, ligne_gray.product_uom, round=False),
                        'product_uom_id'                 : ligne_gray.product_uom.id,
                        'price_unit'                     : ligne_gray.price_unit,
                        'tax_ids'                        : [(6, 0, position_fiscale.map_tax(article_pk.taxes_id).ids)],
                        'is_section_analytique_id'       : article_pk.is_section_analytique_id.id,
                        'is_ligne_facture_fournisseur_id': ligne.id,
                    }))
            facture_gray = self.env['account.move'].create({
                'move_type'     : 'out_invoice',
                'partner_id'    : client.id,
                'fiscal_position_id': position_fiscale.id,
                'currency_id'   : self.env.company.currency_id.id,
                'invoice_date'  : fields.Date.context_today(self),
                'invoice_origin': ', '.join(f.supplier_invoice_number or f.name for f in factures_fournisseur),
                'invoice_line_ids': lignes,
            })
            facture_gray._fill_taux_change()
            factures_fournisseur.write({'is_facture_refacturation_id': facture_gray.id})
            for facture in factures_fournisseur:
                facture.message_post(body=Markup("Facture refacturée à Gray : %s") % facture_gray._get_html_link(title="facture client"))
            factures_gray |= facture_gray
        return {
            'name'     : 'Refacturation à Gray',
            'type'     : 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'views'    : [(self.env.ref('account.view_out_invoice_tree').id, 'tree'), (self.env.ref('account.view_move_form').id, 'form')],
            'domain'   : [('id', 'in', factures_gray.ids)],
            'context'  : {'default_move_type': 'out_invoice'},
        }

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

    @api.model_create_multi
    def create(self, vals_list):
        "Facture fournisseur d'un partenaire Plasti-ka sans devise : devise des commandes de ses lignes (TND), et non celle de la société"
        for vals in vals_list:
            if vals.get('move_type') not in ('in_invoice', 'in_refund') or vals.get('currency_id') or not vals.get('partner_id'):
                continue
            if self.env['res.partner'].browse(vals['partner_id']).is_societe_comptable != 'plasti_ka':
                continue
            ligne_ids = [
                commande[2]['purchase_line_id'] for commande in vals.get('invoice_line_ids', [])
                if isinstance(commande, (list, tuple)) and len(commande) > 2
                and isinstance(commande[2], dict) and commande[2].get('purchase_line_id')
            ]
            devise = self.env['purchase.order.line'].browse(ligne_ids).mapped('order_id.currency_id')[:1]
            if devise:
                vals['currency_id'] = devise.id
        return super().create(vals_list)


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
