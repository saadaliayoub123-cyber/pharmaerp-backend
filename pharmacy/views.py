from rest_framework import viewsets, status
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta, date

from .models import (
    Pharmacie, Categorie, Fournisseur, Medicament, LotStock,
    Client, Vente, LigneVente, BonCommande, LigneCommande,
    Distribution, LigneDistribution, Inventaire, LigneInventaire,
    Alerte, RetourClient, LigneRetour, LogActivite
)
from .serializers import (
    PharmacieSerializer, CategorieSerializer, FournisseurSerializer,
    MedicamentSerializer, LotStockSerializer, ClientSerializer,
    VenteSerializer, LigneVenteSerializer, BonCommandeSerializer,
    LigneCommandeSerializer, DistributionSerializer, LigneDistributionSerializer,
    InventaireSerializer, LigneInventaireSerializer, AlerteSerializer,
    RetourSerializer, LigneRetourSerializer, LogActiviteSerializer
)



def _add_log(action, module, details, user_id=1, pharmacie_id=None):
    """Helper pour creer un log d'activite"""
    try:
        LogActivite.objects.create(
            user_id=user_id,
            user_nom="System",
            action=action,
            module=module,
            details=details,
            pharmacie_id=pharmacie_id,
        )
    except Exception:
        pass


class PharmacieViewSet(viewsets.ModelViewSet):
    queryset = Pharmacie.objects.all()
    serializer_class = PharmacieSerializer


class CategorieViewSet(viewsets.ModelViewSet):
    queryset = Categorie.objects.all()
    serializer_class = CategorieSerializer


class FournisseurViewSet(viewsets.ModelViewSet):
    queryset = Fournisseur.objects.all()
    serializer_class = FournisseurSerializer


class MedicamentViewSet(viewsets.ModelViewSet):
    queryset = Medicament.objects.all()
    serializer_class = MedicamentSerializer


class LotStockViewSet(viewsets.ModelViewSet):
    queryset = LotStock.objects.all()
    serializer_class = LotStockSerializer


class ClientViewSet(viewsets.ModelViewSet):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer


class VenteViewSet(viewsets.ModelViewSet):
    queryset = Vente.objects.all()
    serializer_class = VenteSerializer

    @action(detail=False, methods=["post"], url_path="create_with_lines")
    def create_with_lines(self, request):
        data = request.data
        lignes_data = data.get("lignes", [])
        
        if not lignes_data:
            return Response({"error": "Au moins une ligne requise"}, status=status.HTTP_400_BAD_REQUEST)
        
        for ligne in lignes_data:
            try:
                lot = LotStock.objects.get(id=ligne["lotStockId"])
            except LotStock.DoesNotExist:
                return Response({"error": f"Lot {ligne['lotStockId']} introuvable"}, status=status.HTTP_400_BAD_REQUEST)
            if lot.bloque:
                return Response({"error": f"Lot {lot.numero_lot} bloque"}, status=status.HTTP_400_BAD_REQUEST)
            if lot.quantite < ligne["quantite"]:
                return Response({"error": f"Stock insuffisant pour {lot.medicament.nom} (dispo: {lot.quantite})"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            with transaction.atomic():
                last_vente = Vente.objects.order_by("-id").first()
                next_id = (last_vente.id + 1) if last_vente else 1
                code = f"VTE-{str(next_id).zfill(3)}"
                
                total = sum(float(l["quantite"]) * float(l["prixUnitaire"]) for l in lignes_data)
                client_id = data.get("patientId") or data.get("clientId")
                
                vente = Vente.objects.create(
                    code=code, numero=code,
                    pharmacie_id=data.get("pharmacieId", 1),
                    client_id=client_id if client_id else None,
                    user_id=data.get("userId", 1),
                    mode_paiement=data.get("modePaiement", "especes"),
                    notes=data.get("notes", ""),
                    total_ht=total / 1.20,
                    total_tva=total - (total / 1.20),
                    total_ttc=total,
                    statut="validee",
                )
                
                for ligne in lignes_data:
                    LigneVente.objects.create(
                        vente=vente,
                        medicament_id=ligne["medicamentId"],
                        lot_id=ligne["lotStockId"],
                        quantite=ligne["quantite"],
                        prix_unitaire=ligne["prixUnitaire"],
                        total=ligne["quantite"] * float(ligne["prixUnitaire"]),
                    )
                    lot = LotStock.objects.get(id=ligne["lotStockId"])
                    lot.quantite -= ligne["quantite"]
                    lot.save()
                
                _add_log(f"Vente creee {code}", "Ventes", f"Montant: {total} MAD", pharmacie_id=data.get("pharmacieId"))
                serializer = VenteSerializer(vente)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": f"Erreur: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BonCommandeViewSet(viewsets.ModelViewSet):
    queryset = BonCommande.objects.all()
    serializer_class = BonCommandeSerializer

    @action(detail=False, methods=["post"], url_path="create_with_lines")
    def create_with_lines(self, request):
        """Cree un bon d'achat avec ses lignes"""
        data = request.data
        lignes_data = data.get("lignes", [])
        
        if not lignes_data:
            return Response({"error": "Au moins une ligne requise"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            with transaction.atomic():
                last = BonCommande.objects.order_by("-id").first()
                next_id = (last.id + 1) if last else 1
                code = f"ACH-{str(next_id).zfill(3)}"
                
                total = sum(float(l["quantite"]) * float(l["prixUnitaire"]) for l in lignes_data)
                
                bon = BonCommande.objects.create(
                    code=code, numero=code,
                    pharmacie_id=data.get("pharmacieId", 1),
                    fournisseur_id=data.get("fournisseurId"),
                    user_id=data.get("userId", 1),
                    statut=data.get("statut", "brouillon"),
                    notes=data.get("notes", ""),
                    total_ht=total / 1.20,
                    total_tva=total - (total / 1.20),
                    total_ttc=total,
                )
                
                for ligne in lignes_data:
                    date_fab = ligne.get("dateFabrication") or None
                    date_exp = ligne.get("dateExpiration") or None
                    
                    # Convert ISO datetime strings to date if needed
                    if date_fab and "T" in str(date_fab):
                        date_fab = str(date_fab).split("T")[0]
                    if date_exp and "T" in str(date_exp):
                        date_exp = str(date_exp).split("T")[0]
                    
                    LigneCommande.objects.create(
                        bon_commande=bon,
                        medicament_id=ligne["medicamentId"],
                        quantite=ligne["quantite"],
                        prix_unitaire=ligne["prixUnitaire"],
                        total=ligne["quantite"] * float(ligne["prixUnitaire"]),
                        numero_lot=ligne.get("numeroLot", ""),
                        date_fabrication=date_fab,
                        date_expiration=date_exp,
                    )
                
                _add_log(f"Achat cree {code}", "Achats", f"Fournisseur ID: {data.get('fournisseurId')}", pharmacie_id=data.get("pharmacieId"))
                serializer = BonCommandeSerializer(bon)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": f"Erreur: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=["post"], url_path="receive")
    def receive(self, request, pk=None):
        """Receptionne un bon d'achat - cree les lots automatiquement"""
        try:
            bon = self.get_object()
            
            if bon.statut == "recue":
                return Response({"error": "Deja receptionne"}, status=status.HTTP_400_BAD_REQUEST)
            
            with transaction.atomic():
                lots_crees = []
                for ligne in bon.lignes.all():
                    if not ligne.date_expiration:
                        return Response({"error": f"Ligne sans date expiration: {ligne.medicament.nom}"}, status=status.HTTP_400_BAD_REQUEST)
                    
                    lot = LotStock.objects.create(
                        medicament=ligne.medicament,
                        pharmacie=bon.pharmacie,
                        numero_lot=ligne.numero_lot or f"LOT-{bon.code}-{ligne.id}",
                        quantite=ligne.quantite,
                        quantite_initiale=ligne.quantite,
                        date_fabrication=ligne.date_fabrication,
                        date_expiration=ligne.date_expiration,
                        prix_achat=ligne.prix_unitaire,
                        fournisseur=bon.fournisseur,
                        bloque=False,
                    )
                    lots_crees.append(lot.id)
                
                bon.statut = "recue"
                bon.date_livraison = timezone.now().date()
                bon.save()
                _add_log(f"Achat receptionne {bon.code}", "Achats", f"{len(lots_crees)} lots crees", pharmacie_id=bon.pharmacie_id)
                
                return Response({
                    "message": f"{len(lots_crees)} lot(s) cree(s)",
                    "lots_ids": lots_crees,
                    "bon": BonCommandeSerializer(bon).data
                }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"Erreur: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=["post"], url_path="update_statut")
    def update_statut(self, request, pk=None):
        """Met a jour le statut d'un bon"""
        try:
            bon = self.get_object()
            new_statut = request.data.get("statut")
            if new_statut not in ["brouillon", "commande", "recue", "annulee"]:
                return Response({"error": "Statut invalide"}, status=status.HTTP_400_BAD_REQUEST)
            
            if new_statut == "recue":
                # Use receive logic
                return self.receive(request, pk)
            
            bon.statut = new_statut
            bon.save()
            return Response(BonCommandeSerializer(bon).data)
        except Exception as e:
            return Response({"error": f"Erreur: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DistributionViewSet(viewsets.ModelViewSet):
    queryset = Distribution.objects.all()
    serializer_class = DistributionSerializer

    @action(detail=False, methods=["post"], url_path="create_with_lines")
    def create_with_lines(self, request):
        """Cree une demande de distribution avec ses lignes"""
        data = request.data
        lignes_data = data.get("lignes", [])
        
        if not lignes_data:
            return Response({"error": "Au moins une ligne requise"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Support both depotId and pharmacieSourceId
        source_id = data.get("depotId") or data.get("pharmacieSourceId")
        dest_id = data.get("pharmacieId") or data.get("pharmacieDestinationId")
        
        if not source_id or not dest_id:
            return Response({"error": "Pharmacie source et destination requises"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            with transaction.atomic():
                last = Distribution.objects.order_by("-id").first()
                next_id = (last.id + 1) if last else 1
                code = f"DIST-{str(next_id).zfill(3)}"
                
                dist = Distribution.objects.create(
                    code=code,
                    pharmacie_source_id=source_id,
                    pharmacie_destination_id=dest_id,
                    statut=data.get("statut", "demande"),
                    notes=data.get("notes", ""),
                )
                
                for ligne in lignes_data:
                    lot_id = ligne.get("lotStockId") or None
                    
                    # AUTO-FEFO: Si pas de lot specifie, prendre celui qui expire en premier
                    if not lot_id:
                        from datetime import date
                        fefo_lot = LotStock.objects.filter(
                            medicament_id=ligne["medicamentId"],
                            pharmacie_id=source_id,
                            quantite__gte=ligne["quantiteDemandee"],
                            bloque=False,
                            date_expiration__gte=date.today(),
                        ).order_by("date_expiration").first()
                        if fefo_lot:
                            lot_id = fefo_lot.id
                    
                    LigneDistribution.objects.create(
                        distribution=dist,
                        medicament_id=ligne["medicamentId"],
                        lot_id=lot_id,
                        quantite_demandee=ligne["quantiteDemandee"],
                        quantite_envoyee=0,
                    )
                
                _add_log(f"Distribution creee {code}", "Distributions", f"De pharmacie {source_id} vers {dest_id}", pharmacie_id=source_id)
                serializer = DistributionSerializer(dist)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": f"Erreur: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=["post"], url_path="update_statut")
    def update_statut(self, request, pk=None):
        """Met a jour le statut + gere stock"""
        try:
            dist = self.get_object()
            new_statut = request.data.get("statut")
            
            if new_statut not in ["demande", "valide", "expedie", "recu", "annule"]:
                return Response({"error": "Statut invalide"}, status=status.HTTP_400_BAD_REQUEST)
            
            with transaction.atomic():
                # Validation
                if new_statut == "valide" and dist.statut == "demande":
                    dist.statut = "valide"
                    dist.date_validation = timezone.now()
                    dist.save()
                
                # Expedition: nqs stock mn depot source
                elif new_statut == "expedie" and dist.statut == "valide":
                    for ligne in dist.lignes.all():
                        if ligne.lot:
                            if ligne.lot.quantite < ligne.quantite_demandee:
                                return Response({"error": f"Stock insuffisant: {ligne.medicament.nom} (dispo: {ligne.lot.quantite})"}, status=status.HTTP_400_BAD_REQUEST)
                            ligne.lot.quantite -= ligne.quantite_demandee
                            ligne.lot.save()
                            ligne.quantite_envoyee = ligne.quantite_demandee
                            ligne.save()
                    dist.statut = "expedie"
                    dist.date_expedition = timezone.now()
                    dist.save()
                
                # Reception: zid stock f pharmacie destination (cree lot jdid)
                elif new_statut == "recu" and dist.statut == "expedie":
                    for ligne in dist.lignes.all():
                        if ligne.lot and ligne.quantite_envoyee > 0:
                            # Cree lot jdid f pharmacie destination
                            LotStock.objects.create(
                                medicament=ligne.medicament,
                                pharmacie=dist.pharmacie_destination,
                                numero_lot=f"{ligne.lot.numero_lot}-DIST{dist.id}",
                                quantite=ligne.quantite_envoyee,
                                quantite_initiale=ligne.quantite_envoyee,
                                date_fabrication=ligne.lot.date_fabrication,
                                date_expiration=ligne.lot.date_expiration,
                                prix_achat=ligne.lot.prix_achat,
                                fournisseur=ligne.lot.fournisseur,
                                bloque=False,
                            )
                    dist.statut = "recu"
                    dist.date_reception = timezone.now()
                    dist.save()
                
                # Annulation
                elif new_statut == "annule":
                    dist.statut = "annule"
                    dist.save()
                
                else:
                    return Response({"error": f"Transition invalide: {dist.statut} -> {new_statut}"}, status=status.HTTP_400_BAD_REQUEST)
                
                serializer = DistributionSerializer(dist)
                return Response(serializer.data)
        except Exception as e:
            return Response({"error": f"Erreur: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class InventaireViewSet(viewsets.ModelViewSet):
    queryset = Inventaire.objects.all()
    serializer_class = InventaireSerializer

    @action(detail=False, methods=["post"], url_path="create_with_lines")
    def create_with_lines(self, request):
        """Cree inventaire avec lignes auto (tous les lots de la pharmacie)"""
        data = request.data
        pharmacie_id = data.get("pharmacieId")
        
        if not pharmacie_id:
            return Response({"error": "pharmacieId requis"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            with transaction.atomic():
                last = Inventaire.objects.order_by("-id").first()
                next_id = (last.id + 1) if last else 1
                code = f"INV-{str(next_id).zfill(3)}"
                
                inv = Inventaire.objects.create(
                    code=code,
                    pharmacie_id=pharmacie_id,
                    user_id=data.get("userId", 1),
                    statut="en_cours",
                    notes=data.get("notes", ""),
                )
                
                # Auto-genere lignes pour tous les lots de la pharmacie
                lots = LotStock.objects.filter(pharmacie_id=pharmacie_id, quantite__gt=0)
                for lot in lots:
                    LigneInventaire.objects.create(
                        inventaire=inv,
                        medicament=lot.medicament,
                        lot=lot,
                        stock_systeme=lot.quantite,
                        stock_reel=lot.quantite,
                        ecart=0,
                        ajustement_applique=False,
                    )
                
                _add_log(f"Inventaire cree {code}", "Inventaires", f"{lots.count()} lots a controler", pharmacie_id=pharmacie_id)
                serializer = InventaireSerializer(inv)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": f"Erreur: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=["post"], url_path="update_ligne")
    def update_ligne(self, request, pk=None):
        """Update stock_reel d'une ligne d'inventaire"""
        try:
            inv = self.get_object()
            if inv.statut != "en_cours":
                return Response({"error": "Inventaire deja finalise"}, status=status.HTTP_400_BAD_REQUEST)
            
            ligne_id = request.data.get("ligneId")
            stock_reel = request.data.get("stockReel")
            
            ligne = LigneInventaire.objects.get(id=ligne_id, inventaire=inv)
            ligne.stock_reel = int(stock_reel)
            ligne.ecart = ligne.stock_reel - ligne.stock_systeme
            ligne.save()
            
            return Response(LigneInventaireSerializer(ligne).data)
        except Exception as e:
            return Response({"error": f"Erreur: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=["post"], url_path="finaliser")
    def finaliser(self, request, pk=None):
        """Finalise inventaire et applique ajustements stock"""
        try:
            inv = self.get_object()
            if inv.statut == "finalise":
                return Response({"error": "Deja finalise"}, status=status.HTTP_400_BAD_REQUEST)
            
            with transaction.atomic():
                for ligne in inv.lignes.all():
                    if not ligne.ajustement_applique and ligne.lot:
                        # Ajuste stock du lot
                        ligne.lot.quantite = ligne.stock_reel
                        ligne.lot.save()
                        ligne.ajustement_applique = True
                        ligne.save()
                
                inv.statut = "finalise"
                inv.date_finalisation = timezone.now()
                inv.save()
                
                return Response(InventaireSerializer(inv).data)
        except Exception as e:
            return Response({"error": f"Erreur: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AlerteViewSet(viewsets.ModelViewSet):
    queryset = Alerte.objects.all()
    serializer_class = AlerteSerializer

    @action(detail=False, methods=["post"], url_path="generate")
    def generate_alertes(self, request):
        """Genere alertes automatiquement basees sur l'etat du stock"""
        from datetime import date, timedelta
        today = date.today()
        dans_30j = today + timedelta(days=30)
        
        # Supprime anciennes alertes auto-generees
        Alerte.objects.all().delete()
        
        alertes_creees = 0
        
        # 1. Lots expires
        lots_expires = LotStock.objects.filter(date_expiration__lt=today, quantite__gt=0)
        for lot in lots_expires:
            Alerte.objects.create(
                type_alerte="expire",
                niveau="danger",
                titre=f"Lot expire: {lot.medicament.nom}",
                message=f"Le lot {lot.numero_lot} de {lot.medicament.nom} a expire le {lot.date_expiration}. Stock: {lot.quantite} unites a retirer.",
                medicament=lot.medicament,
                lot=lot,
                pharmacie=lot.pharmacie,
            )
            alertes_creees += 1
        
        # 2. Lots qui expirent dans 30 jours
        lots_proche_exp = LotStock.objects.filter(
            date_expiration__gte=today,
            date_expiration__lte=dans_30j,
            quantite__gt=0
        )
        for lot in lots_proche_exp:
            jours = (lot.date_expiration - today).days
            Alerte.objects.create(
                type_alerte="expiration_proche",
                niveau="warning",
                titre=f"Expiration proche: {lot.medicament.nom}",
                message=f"Le lot {lot.numero_lot} de {lot.medicament.nom} expire dans {jours} jours ({lot.date_expiration}). Stock: {lot.quantite} unites.",
                medicament=lot.medicament,
                lot=lot,
                pharmacie=lot.pharmacie,
            )
            alertes_creees += 1
        
        # 3. Stock par medicament
        for med in Medicament.objects.filter(actif=True):
            # Stock global
            stock_total = sum(lot.quantite for lot in med.lots.filter(quantite__gt=0))
            
            if stock_total == 0:
                Alerte.objects.create(
                    type_alerte="rupture",
                    niveau="danger",
                    titre=f"Rupture: {med.nom}",
                    message=f"Le medicament {med.nom} est en rupture de stock totale. Reapprovisionnement urgent requis.",
                    medicament=med,
                )
                alertes_creees += 1
            elif stock_total <= med.seuil_alerte:
                Alerte.objects.create(
                    type_alerte="stock_faible",
                    niveau="warning",
                    titre=f"Stock faible: {med.nom}",
                    message=f"Stock de {med.nom} est de {stock_total} unites, sous le seuil d'alerte ({med.seuil_alerte}). Commande recommandee.",
                    medicament=med,
                )
                alertes_creees += 1
        
        return Response({
            "message": f"{alertes_creees} alertes generees",
            "count": alertes_creees,
        }, status=status.HTTP_200_OK)




class RetourViewSet(viewsets.ModelViewSet):
    queryset = RetourClient.objects.all()
    serializer_class = RetourSerializer

    @action(detail=False, methods=["post"], url_path="create_with_lines")
    def create_with_lines(self, request):
        data = request.data
        lignes_data = data.get("lignes", [])
        
        if not lignes_data:
            return Response({"error": "Au moins une ligne requise"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            with transaction.atomic():
                last = RetourClient.objects.order_by("-id").first()
                next_id = (last.id + 1) if last else 1
                code = f"RET-{str(next_id).zfill(3)}"
                
                total = sum(float(l["quantiteRetournee"]) * float(l["prixUnitaire"]) for l in lignes_data)
                
                retour = RetourClient.objects.create(
                    code=code,
                    vente_id=data.get("venteId"),
                    client_id=data.get("patientId") or data.get("clientId"),
                    pharmacie_id=data.get("pharmacieId"),
                    motif=data.get("motif", "autre"),
                    notes=data.get("notes", ""),
                    montant_rembourse=total,
                )
                
                for ligne in lignes_data:
                    LigneRetour.objects.create(
                        retour=retour,
                        medicament_id=ligne["medicamentId"],
                        lot_id=ligne.get("lotStockId") or None,
                        quantite_retournee=ligne["quantiteRetournee"],
                        prix_unitaire=ligne["prixUnitaire"],
                        montant=ligne["quantiteRetournee"] * float(ligne["prixUnitaire"]),
                    )
                    
                    # Stock+ f lot
                    if ligne.get("lotStockId"):
                        lot = LotStock.objects.get(id=ligne["lotStockId"])
                        lot.quantite += ligne["quantiteRetournee"]
                        lot.save()
                
                _add_log(f"Retour cree {code}", "Retours", f"Montant rembourse: {total} MAD", pharmacie_id=data.get("pharmacieId"))
                return Response(RetourSerializer(retour).data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": f"Erreur: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




class LogActiviteViewSet(viewsets.ModelViewSet):
    queryset = LogActivite.objects.all()[:500]
    serializer_class = LogActiviteSerializer
    
    @action(detail=False, methods=["post"], url_path="log")
    def create_log(self, request):
        try:
            log = LogActivite.objects.create(
                user_id=request.data.get("userId", 1),
                user_nom=request.data.get("userNom", "System"),
                action=request.data.get("action", ""),
                module=request.data.get("module", "Systeme"),
                details=request.data.get("details", ""),
                pharmacie_id=request.data.get("pharmacieId") or None,
            )
            return Response(LogActiviteSerializer(log).data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
def dashboard_stats(request):
    today = date.today()
    debut_mois = today.replace(day=1)
    dans_30_jours = today + timedelta(days=30)

    medicaments_actifs = Medicament.objects.filter(actif=True).count()
    medicaments_rupture = 0
    medicaments_faible = 0
    for med in Medicament.objects.filter(actif=True):
        stock = sum(lot.quantite for lot in med.lots.all())
        if stock == 0:
            medicaments_rupture += 1
        elif stock <= med.seuil_alerte:
            medicaments_faible += 1

    fournisseurs_actifs = Fournisseur.objects.filter(actif=True).count()
    ventes_aujourdhui = Vente.objects.filter(date_vente__date=today, statut="validee")
    total_ventes_jour = ventes_aujourdhui.aggregate(total=Sum("total_ttc"))["total"] or 0
    nb_transactions_jour = ventes_aujourdhui.count()
    ventes_mois = Vente.objects.filter(date_vente__date__gte=debut_mois, statut="validee")
    ca_mensuel = ventes_mois.aggregate(total=Sum("total_ttc"))["total"] or 0
    lots_expires = LotStock.objects.filter(date_expiration__lt=today, quantite__gt=0).count()
    lots_expirent_bientot = LotStock.objects.filter(
        date_expiration__gte=today, date_expiration__lte=dans_30_jours, quantite__gt=0
    ).count()

    return Response({
        "medicaments_actifs": medicaments_actifs,
        "medicaments_rupture": medicaments_rupture,
        "medicaments_faible": medicaments_faible,
        "fournisseurs_actifs": fournisseurs_actifs,
        "ventes_aujourdhui": float(total_ventes_jour),
        "nb_transactions_jour": nb_transactions_jour,
        "ca_mensuel": float(ca_mensuel),
        "lots_expires": lots_expires,
        "lots_expirent_bientot": lots_expirent_bientot,
    })









