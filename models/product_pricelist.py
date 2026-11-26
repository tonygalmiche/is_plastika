# -*- coding: utf-8 -*-
from datetime import timedelta
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from .product import societe_comptable_list


# Contexte qui autorise la modification d'une liste de prix Gray générée depuis une liste TND
CONTEXTE_MAJ_LISTE_GRAY = 'is_maj_liste_prix_gray'


def _test_liste_gray_verrouillee(env, pricelists):
    "Bloque la modification manuelle d'une liste de prix Gray générée depuis une liste TND"
    if env.context.get(CONTEXTE_MAJ_LISTE_GRAY):
        return
    for pricelist in pricelists:
        if pricelist.is_pricelist_tnd_id:
            raise ValidationError(
                "La liste de prix « %s » est générée depuis la liste de prix TND « %s » : "
                "modifiez la liste TND puis cliquez sur « Mise à jour liste de prix Gray »"
                % (pricelist.name, pricelist.is_pricelist_tnd_id.name)
            )


def _test_utilisateur_sans_societe_comptable(env):
    """Les listes de prix et lignes de l'autre société sont filtrées pour un utilisateur avec une société comptable :
    une liste TND lue par un utilisateur Plastigray paraîtrait vide et viderait la liste Gray"""
    if env.user.is_societe_comptable:
        raise ValidationError(
            "Action réservée à un utilisateur sans société comptable (il doit voir les listes de prix de Plastigray et de Plasti-ka)"
        )


class product_pricelist(models.Model):
    _inherit = 'product.pricelist'

    is_societe_comptable = fields.Selection(
        societe_comptable_list, "Société comptable",
        compute='_compute_is_societe_comptable', store=True, index=True,
    )
    is_pricelist_tnd_id = fields.Many2one(
        'product.pricelist', 'Liste de prix TND', readonly=True, copy=False,
        help="Liste de prix TND du fournisseur de PK depuis laquelle cette liste de prix Gray est générée (liste non modifiable)",
    )
    is_pricelist_gray_id = fields.Many2one(
        'product.pricelist', 'Liste de prix Gray', compute='_compute_is_pricelist_gray_id',
        help="Liste de prix Gray (€ avec commission) générée depuis cette liste de prix TND",
    )
    is_maj_liste_gray_vsb = fields.Boolean('Mise à jour liste de prix Gray possible', compute='_compute_is_maj_liste_gray_vsb')
    is_creer_liste_tnd_vsb = fields.Boolean('Création liste de prix TND possible', compute='_compute_is_creer_liste_tnd_vsb')

    @api.depends('partner_id.is_societe_comptable')
    def _compute_is_societe_comptable(self):
        for pricelist in self:
            pricelist.is_societe_comptable = pricelist.partner_id.is_societe_comptable


    def _compute_is_pricelist_gray_id(self):
        for obj in self:
            liste = False
            if obj.id:
                liste = self.search([('is_pricelist_tnd_id', '=', obj.id)], limit=1)
            obj.is_pricelist_gray_id = liste


    @api.depends('type', 'currency_id', 'partner_id')
    def _compute_is_maj_liste_gray_vsb(self):
        for obj in self:
            obj.is_maj_liste_gray_vsb = bool(
                not self.env.user.is_societe_comptable
                and obj.type == 'purchase' and obj.currency_id.name == 'TND' and obj.partner_id.is_fournisseur_gray_id
            )


    @api.depends('type', 'currency_id', 'partner_id', 'is_pricelist_tnd_id')
    def _compute_is_creer_liste_tnd_vsb(self):
        for obj in self:
            fournisseur_pk = obj.partner_id.is_fournisseur_pk_id
            obj.is_creer_liste_tnd_vsb = bool(
                not self.env.user.is_societe_comptable
                and obj.type == 'purchase' and obj.currency_id.name == 'EUR' and fournisseur_pk
                and not obj.is_pricelist_tnd_id and not fournisseur_pk.pricelist_purchase_id
            )


    def creer_liste_prix_tnd_action(self):
        """Initialisation : crée la liste de prix TND du fournisseur de PK à partir de cette liste de prix Gray en € :
        versions en cours et futures recopiées avec prix TND = prix € × taux devise dinar / taux de commission
        (taux du tableau de la société valides à la date de début de chaque version)"""
        self.ensure_one()
        _test_utilisateur_sans_societe_comptable(self.env)
        if not self.is_creer_liste_tnd_vsb:
            raise ValidationError(
                "La liste de prix « %s » doit être une liste d'achat en EUR d'un fournisseur de Gray relié à un fournisseur de PK "
                "sans liste de prix d'achat" % self.name
            )
        company = self.env.company
        today = fields.Date.context_today(self)
        fournisseur_pk = self.partner_id.is_fournisseur_pk_id
        versions = self.version_id.filtered(lambda v: v.active and (not v.date_end or v.date_end >= today))
        if not versions:
            raise ValidationError("La liste de prix « %s » n'a pas de version en cours ou future" % self.name)
        taux_par_version = {}
        for version in versions:
            date = version.date_start or today
            ligne_taux = company.get_ligne_taux_facturation_pk(date)
            if not ligne_taux or not ligne_taux.taux_commission:
                raise ValidationError(
                    "Aucun taux devise dinar et taux de commission valide au %s dans le tableau des taux de la société"
                    % date.strftime('%d/%m/%Y')
                )
            taux_par_version[version.id] = ligne_taux
        liste = self.create({
            'name'       : '%s - %s' % (fournisseur_pk.is_code, fournisseur_pk.name),
            'type'       : 'purchase',
            'partner_id' : fournisseur_pk.id,
            'currency_id': self.env['res.currency'].search([('name', '=', 'TND')], limit=1).id,
        })
        fournisseur_pk.pricelist_purchase_id = liste.id
        # Liste Gray reliée (et donc verrouillée) dès la création de la liste TND
        self.is_pricelist_tnd_id = liste.id
        for version in versions.sorted(lambda v: v.date_start or today):
            ligne_taux = taux_par_version[version.id]
            version_tnd = self.env['product.pricelist.version'].create({
                'pricelist_id': liste.id,
                'name'        : str((version.date_start or today).year),
                'date_start'  : version.date_start,
                'date_end'    : version.date_end,
            })
            self.env['product.pricelist.item'].create([{
                'price_version_id': version_tnd.id,
                'pricelist_id'    : liste.id,
                'product_id'      : item.product_id.id,
                'min_quantity'    : item.min_quantity,
                'sequence'        : item.sequence,
                'date_start'      : item.date_start,
                'date_end'        : item.date_end,
                'justification'   : item.justification,
                'price_surcharge' : round(item.price_surcharge * ligne_taux.taux_devise_dinar / ligne_taux.taux_commission, 3),
                'compute_price'   : 'fixed',
                'applied_on'      : '0_product_variant',
            } for item in version.item_ids])
        return {
            'type'     : 'ir.actions.act_window',
            'res_model': 'product.pricelist',
            'res_id'   : liste.id,
            'view_mode': 'form',
            'target'   : 'current',
        }


    def _get_liste_gray(self):
        "Liste de prix d'achat du fournisseur de Gray relié au fournisseur de PK de cette liste TND (créée si besoin)"
        self.ensure_one()
        fournisseur_gray = self.partner_id.is_fournisseur_gray_id
        if not self.is_maj_liste_gray_vsb:
            raise ValidationError(
                "La liste de prix « %s » doit être une liste d'achat en TND d'un fournisseur de PK relié à un fournisseur de Gray" % self.name
            )
        liste = fournisseur_gray.pricelist_purchase_id
        if liste:
            if liste.currency_id.name != 'EUR':
                raise ValidationError(
                    "La liste de prix d'achat « %s » du fournisseur « %s » n'est pas en EUR" % (liste.name, fournisseur_gray.display_name)
                )
            if liste.is_pricelist_tnd_id and liste.is_pricelist_tnd_id != self:
                raise ValidationError(
                    "La liste de prix « %s » est déjà générée depuis la liste TND « %s »" % (liste.name, liste.is_pricelist_tnd_id.name)
                )
        else:
            liste = self.create({
                'name'       : '%s - %s' % (fournisseur_gray.is_code, self.partner_id.name),
                'type'       : 'purchase',
                'partner_id' : fournisseur_gray.id,
                'currency_id': self.env.ref('base.EUR').id,
            })
            fournisseur_gray.pricelist_purchase_id = liste.id
        return liste


    def maj_liste_prix_gray_action(self):
        """Met à jour la liste de prix Gray (€ avec commission) depuis cette liste TND du fournisseur de PK :
        - versions passées de la liste Gray conservées, version en cours arrêtée à hier, versions futures supprimées ;
        - versions recréées à partir d'aujourd'hui, découpées aux changements de version TND et de taux (tableau de la société) ;
        - prix € = prix TND / taux devise dinar × taux de commission"""
        _test_utilisateur_sans_societe_comptable(self.env)
        company = self.env.company
        today = fields.Date.context_today(self)
        for obj in self:
            liste = obj._get_liste_gray().with_context(**{CONTEXTE_MAJ_LISTE_GRAY: True})
            liste.is_pricelist_tnd_id = obj.id
            # Liste TND mise sur la fiche du fournisseur de PK si elle est vide (prix des commandes PK)
            if not obj.partner_id.pricelist_purchase_id:
                obj.partner_id.pricelist_purchase_id = obj.id

            #** Versions TND en cours ou futures *******************************
            versions_tnd = obj.version_id.filtered(lambda v: v.active and (not v.date_end or v.date_end >= today))
            if not versions_tnd:
                raise ValidationError("La liste de prix « %s » n'a pas de version en cours ou future" % obj.name)

            #** Dates de début des périodes : aujourd'hui, changements de version TND et de taux
            dates = {today}
            for version in versions_tnd:
                if version.date_start and version.date_start > today:
                    dates.add(version.date_start)
                if version.date_end:
                    dates.add(version.date_end + timedelta(days=1))
            for ligne in company.is_taux_facturation_pk_ids:
                if ligne.date_debut > today:
                    dates.add(ligne.date_debut)
            dates = sorted(dates)

            #** Contrôle des taux avant de modifier la liste Gray ****************
            periodes = []
            for i, date_debut in enumerate(dates):
                version_tnd = versions_tnd.filtered(
                    lambda v: (not v.date_start or v.date_start <= date_debut) and (not v.date_end or v.date_end >= date_debut)
                )[:1]
                if not version_tnd:
                    continue
                date_fin = dates[i + 1] - timedelta(days=1) if i + 1 < len(dates) else False
                if version_tnd.date_end and (not date_fin or version_tnd.date_end < date_fin):
                    date_fin = version_tnd.date_end
                ligne_taux = company.get_ligne_taux_facturation_pk(date_debut)
                if not ligne_taux or not ligne_taux.taux_devise_dinar:
                    raise ValidationError(
                        "Aucun taux devise dinar et taux de commission valide au %s dans le tableau des taux de la société"
                        % date_debut.strftime('%d/%m/%Y')
                    )
                periodes.append((date_debut, date_fin, version_tnd, ligne_taux))

            if not periodes:
                raise ValidationError("La liste de prix « %s » n'a pas de version en cours ou future" % obj.name)

            #** Versions Gray : avant la 1ère période TND conservées (celle en cours arrêtée la veille), après supprimées
            #   (si la liste TND commence le 01/12, la version Gray en cours reste valable jusqu'au 30/11)
            date_coupure = periodes[0][0]
            for version in liste.with_context(active_test=False).version_id:
                if version.date_end and version.date_end < date_coupure:
                    continue
                if version.date_start and version.date_start < date_coupure:
                    version.date_end = date_coupure - timedelta(days=1)
                else:
                    version.item_ids.unlink()
                    version.unlink()

            #** Création des versions Gray ***************************************
            for date_debut, date_fin, version_tnd, ligne_taux in periodes:
                taux_devise_dinar = ligne_taux.taux_devise_dinar
                taux_commission   = ligne_taux.taux_commission
                version = self.env['product.pricelist.version'].with_context(**{CONTEXTE_MAJ_LISTE_GRAY: True}).create({
                    'pricelist_id': liste.id,
                    'name'        : '%s-%gdt +commission %g%%' % (
                        date_debut.year, round(taux_devise_dinar, 4), round((taux_commission - 1) * 100, 2)
                    ),
                    'date_start'  : date_debut,
                    'date_end'    : date_fin,
                })
                vals_list = []
                for item in version_tnd.item_ids:
                    if item.date_end and item.date_end < date_debut:
                        continue
                    if item.date_start and date_fin and item.date_start > date_fin:
                        continue
                    vals_list.append({
                        'price_version_id': version.id,
                        'pricelist_id'    : liste.id,
                        'product_id'      : item.product_id.id,
                        'min_quantity'    : item.min_quantity,
                        'sequence'        : item.sequence,
                        'date_start'      : max(item.date_start, date_debut) if item.date_start else False,
                        'date_end'        : (min(item.date_end, date_fin) if date_fin else item.date_end) if item.date_end else False,
                        'justification'   : item.justification,
                        'price_surcharge' : round(item.price_surcharge / taux_devise_dinar * taux_commission, 4),
                        'compute_price'   : 'fixed',
                        'applied_on'      : '0_product_variant',
                    })
                self.env['product.pricelist.item'].with_context(**{CONTEXTE_MAJ_LISTE_GRAY: True}).create(vals_list)
        return True


    def write(self, vals):
        if 'version_id' in vals:
            _test_liste_gray_verrouillee(self.env, self)
        return super().write(vals)

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        user = self.env.user
        if user.is_societe_comptable:
            args = args.copy()
            args += ['|', ('is_societe_comptable', '=', False), ('is_societe_comptable', '=', user.is_societe_comptable)]
        return super(product_pricelist, self)._search(args, offset=offset, limit=limit, order=order, count=count, access_rights_uid=access_rights_uid)


class product_pricelist_item(models.Model):
    _inherit = 'product.pricelist.item'

    is_societe_comptable = fields.Selection(
        societe_comptable_list, "Société comptable",
        compute='_compute_is_societe_comptable', store=True, index=True,
    )

    @api.depends('price_version_id.pricelist_id.is_societe_comptable')
    def _compute_is_societe_comptable(self):
        for item in self:
            item.is_societe_comptable = item.price_version_id.pricelist_id.is_societe_comptable

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        user = self.env.user
        # Contexte is_sans_filtre_societe_comptable : prix TND lu à la validation d'une commande Gray par un utilisateur Plastigray
        if user.is_societe_comptable and not self.env.context.get('is_sans_filtre_societe_comptable'):
            args = args.copy()
            args += ['|', ('is_societe_comptable', '=', False), ('is_societe_comptable', '=', user.is_societe_comptable)]
        return super(product_pricelist_item, self)._search(args, offset=offset, limit=limit, order=order, count=count, access_rights_uid=access_rights_uid)


    @api.model_create_multi
    def create(self, vals_list):
        # Contrôle après création : la version peut venir d'une valeur par défaut (default_price_version_id),
        # ajoutée par Odoo après ce create. L'erreur annule la création.
        records = super().create(vals_list)
        _test_liste_gray_verrouillee(self.env, records.mapped('price_version_id.pricelist_id'))
        return records


    def write(self, vals):
        _test_liste_gray_verrouillee(self.env, self.mapped('price_version_id.pricelist_id'))
        if vals.get('price_version_id'):
            version = self.env['product.pricelist.version'].browse(vals['price_version_id'])
            _test_liste_gray_verrouillee(self.env, version.pricelist_id)
        return super().write(vals)


    def unlink(self):
        _test_liste_gray_verrouillee(self.env, self.mapped('price_version_id.pricelist_id'))
        return super().unlink()


class product_pricelist_version(models.Model):
    _inherit = 'product.pricelist.version'

    @api.model_create_multi
    def create(self, vals_list):
        # Contrôle après création : la liste peut venir d'une valeur par défaut. L'erreur annule la création.
        records = super().create(vals_list)
        _test_liste_gray_verrouillee(self.env, records.mapped('pricelist_id'))
        return records


    def write(self, vals):
        _test_liste_gray_verrouillee(self.env, self.mapped('pricelist_id'))
        if vals.get('pricelist_id'):
            _test_liste_gray_verrouillee(self.env, self.env['product.pricelist'].browse(vals['pricelist_id']))
        return super().write(vals)


    def unlink(self):
        _test_liste_gray_verrouillee(self.env, self.mapped('pricelist_id'))
        return super().unlink()
