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
