# -*- coding: utf-8 -*-
from odoo import models, fields, api
from .product import societe_comptable_list


class sale_order(models.Model):
    _inherit = 'sale.order'

    is_societe_comptable = fields.Selection(related='partner_id.is_societe_comptable', store=True, tracking=True)

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        # Filtrer par société comptable de l'utilisateur
        user = self.env.user
        if user.is_societe_comptable:
            args = args.copy()
            args.append(('is_societe_comptable', '=', user.is_societe_comptable))

        return super(sale_order, self)._search(args, offset=offset, limit=limit, order=order, count=count, access_rights_uid=access_rights_uid)


    def get_pic_3mois(self, ok=False, **kwargs):
        # Filtre le résultat du PIC 3 mois par société comptable de l'utilisateur.
        # Le super() construit le dict via SQL sans tenir compte de is_societe_comptable ;
        # on récupère les product.template en lot puis on exclut les articles de l'autre société.
        res = super().get_pic_3mois(ok=ok, **kwargs)
        user = self.env.user
        if user.is_societe_comptable:
            tmpl_ids = list({vals['row']['product_tmpl_id'] for vals in res['dict'].values()})
            pts = self.env['product.template'].browse(tmpl_ids)
            allowed_ids = {pt.id for pt in pts if pt.is_societe_comptable == user.is_societe_comptable}
            res['dict'] = {k: v for k, v in res['dict'].items() if v['row']['product_tmpl_id'] in allowed_ids}
        return res


class sale_order_line(models.Model):
    _inherit = 'sale.order.line'

    is_societe_comptable = fields.Selection(related='order_id.is_societe_comptable', store=True, index=True)

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        user = self.env.user
        if user.is_societe_comptable:
            args = args.copy()
            args.append(('is_societe_comptable', '=', user.is_societe_comptable))
        return super(sale_order_line, self)._search(args, offset=offset, limit=limit, order=order, count=count, access_rights_uid=access_rights_uid)

    def _prepare_invoice_line(self, **optional_vals):
        res = super()._prepare_invoice_line(**optional_vals)
        # _create_invoices_aves_regroupement (is_plastigray16) n'applique pas la position
        # fiscale : on le fait ici explicitement sur les taxes et le compte.
        fiscal_pos = self.order_id.fiscal_position_id
        if fiscal_pos:
            tax_ids_raw = res.get('tax_ids', [])
            decoded_ids = []
            for cmd in tax_ids_raw:
                cmd = tuple(cmd)
                if cmd[0] == 6 and len(cmd) >= 3:
                    decoded_ids += list(cmd[2])
                elif cmd[0] == 4 and len(cmd) >= 2:
                    decoded_ids.append(cmd[1])
            if decoded_ids:
                taxes = self.env['account.tax'].browse(decoded_ids)
                res['tax_ids'] = [(6, 0, fiscal_pos.map_tax(taxes).ids)]
            if res.get('account_id'):
                account = self.env['account.account'].browse(res['account_id'])
                res['account_id'] = fiscal_pos.map_account(account).id
        # Injecter price_unit et les champs PU depuis le tarif commercial (indice=999)
        partner = self.order_id.partner_invoice_id.commercial_partner_id
        product_tmpl = self.product_id.product_tmpl_id
        if partner and product_tmpl:
            tarif = self.env['is.tarif.cial'].search([
                ('partner_id', '=', partner.id),
                ('product_id', '=', product_tmpl.id),
                ('indice_prix', '=', 999),
            ], limit=1)
            if tarif:
                pu_mp = tarif.part_matiere + tarif.part_composant + tarif.part_emballage
                pu_amt = tarif.amortissement_moule
                pu_pf = tarif.prix_vente - pu_mp - pu_amt
                res['price_unit'] = tarif.prix_vente
                res['is_pu_mp'] = pu_mp
                res['is_pu_amt'] = pu_amt
                res['is_pu_pf'] = pu_pf
        return res
