from rest_framework import serializers
from .models import (
    Pharmacie, Categorie, Fournisseur, Medicament, LotStock,
    Client, Vente, LigneVente, BonCommande, LigneCommande,
    Distribution, LigneDistribution, Inventaire, LigneInventaire,
    Alerte, RetourClient, LigneRetour, LogActivite
)


class PharmacieSerializer(serializers.ModelSerializer):
    dateCreation = serializers.DateTimeField(source="created_at", read_only=True)
    class Meta:
        model = Pharmacie
        fields = ["id", "code", "nom", "type", "adresse", "ville", "telephone",
                  "email", "responsable", "ice", "rc", "actif", "dateCreation"]


class CategorieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categorie
        fields = ["id", "nom", "description", "couleur", "icone"]


class FournisseurSerializer(serializers.ModelSerializer):
    delaiLivraisonJours = serializers.IntegerField(source="delai_livraison_jours", required=False, default=7)
    scoreQualite = serializers.IntegerField(source="score_qualite", required=False, default=3)
    dateCreation = serializers.DateTimeField(source="created_at", read_only=True)
    class Meta:
        model = Fournisseur
        fields = ["id", "code", "nom", "contact", "telephone", "email", "adresse", 
                  "ville", "ice", "delaiLivraisonJours", "scoreQualite", "actif", "dateCreation"]


class LotStockSerializer(serializers.ModelSerializer):
    medicamentId = serializers.IntegerField(source="medicament_id")
    pharmacieId = serializers.IntegerField(source="pharmacie_id", required=False, allow_null=True)
    numeroLot = serializers.CharField(source="numero_lot")
    dateExpiration = serializers.DateField(source="date_expiration")
    dateFabrication = serializers.DateField(source="date_fabrication", required=False, allow_null=True)
    quantiteActuelle = serializers.IntegerField(source="quantite")
    quantiteInitiale = serializers.IntegerField(source="quantite_initiale", required=False)
    prixAchat = serializers.DecimalField(source="prix_achat", max_digits=10, decimal_places=2)
    fournisseurId = serializers.IntegerField(source="fournisseur_id", required=False, allow_null=True)
    dateCreation = serializers.DateTimeField(source="created_at", read_only=True)
    class Meta:
        model = LotStock
        fields = ["id", "medicamentId", "pharmacieId", "numeroLot", "dateExpiration", 
                  "dateFabrication", "quantiteActuelle", "quantiteInitiale", "prixAchat", 
                  "fournisseurId", "bloque", "dateCreation"]


class MedicamentSerializer(serializers.ModelSerializer):
    nomCommercial = serializers.CharField(source="nom")
    nomScientifique = serializers.CharField(source="dci", required=False, allow_blank=True)
    categorieId = serializers.IntegerField(source="categorie_id", allow_null=True, required=False)
    prixVente = serializers.DecimalField(source="prix_vente", max_digits=10, decimal_places=2)
    prixAchat = serializers.DecimalField(source="prix_achat", max_digits=10, decimal_places=2, required=False, default=0)
    seuilAlerte = serializers.IntegerField(source="seuil_alerte")
    seuilDepot = serializers.IntegerField(source="seuil_depot", required=False, default=500)
    delaiSecuritePharmacie = serializers.IntegerField(source="delai_securite_pharmacie", required=False, default=7)
    delaiSecuriteDepot = serializers.IntegerField(source="delai_securite_depot", required=False, default=30)
    necessiteOrdonnance = serializers.BooleanField(source="sur_ordonnance", required=False, default=False)
    dateCreation = serializers.DateTimeField(source="created_at", read_only=True)
    fournisseurPrincipalId = serializers.SerializerMethodField()
    class Meta:
        model = Medicament
        fields = ["id", "code", "nomCommercial", "nomScientifique", "categorieId",
                  "forme", "dosage", "laboratoire", "prixVente", "prixAchat", "tva",
                  "seuilAlerte", "seuilDepot", "delaiSecuritePharmacie", "delaiSecuriteDepot", "necessiteOrdonnance", "actif", "dateCreation",
                  "fournisseurPrincipalId"]
    def get_fournisseurPrincipalId(self, obj):
        return None


class ClientSerializer(serializers.ModelSerializer):
    dateNaissance = serializers.DateField(source="date_naissance", required=False, allow_null=True)
    pharmacieId = serializers.IntegerField(source="pharmacie_id", required=False, allow_null=True)
    dateCreation = serializers.DateTimeField(source="created_at", read_only=True)
    class Meta:
        model = Client
        fields = ["id", "code", "nom", "prenom", "cin", "type_client", "genre",
                  "dateNaissance", "telephone", "email", "adresse", "ville", "ice",
                  "pharmacieId", "actif", "dateCreation"]


class LigneVenteSerializer(serializers.ModelSerializer):
    venteId = serializers.IntegerField(source="vente_id", read_only=True)
    medicamentId = serializers.IntegerField(source="medicament_id")
    lotStockId = serializers.IntegerField(source="lot_id", required=False, allow_null=True)
    prixUnitaire = serializers.DecimalField(source="prix_unitaire", max_digits=10, decimal_places=2)
    montantTotal = serializers.DecimalField(source="total", max_digits=10, decimal_places=2)
    class Meta:
        model = LigneVente
        fields = ["id", "venteId", "medicamentId", "lotStockId", "quantite", "prixUnitaire", "montantTotal"]


class VenteSerializer(serializers.ModelSerializer):
    patientId = serializers.IntegerField(source="client_id", allow_null=True, required=False)
    clientId = serializers.IntegerField(source="client_id", allow_null=True, required=False)
    pharmacieId = serializers.IntegerField(source="pharmacie_id", required=False, allow_null=True)
    userId = serializers.IntegerField(source="user_id", required=False, default=1)
    dateVente = serializers.DateTimeField(source="date_vente")
    montantTotal = serializers.DecimalField(source="total_ttc", max_digits=10, decimal_places=2)
    modePaiement = serializers.CharField(source="mode_paiement")
    lignes = LigneVenteSerializer(many=True, read_only=True)
    class Meta:
        model = Vente
        fields = ["id", "code", "numero", "patientId", "clientId", "pharmacieId", "userId",
                  "dateVente", "total_ht", "total_tva", "montantTotal", "modePaiement", 
                  "statut", "notes", "lignes"]


class LigneCommandeSerializer(serializers.ModelSerializer):
    achatId = serializers.IntegerField(source="bon_commande_id", read_only=True)
    medicamentId = serializers.IntegerField(source="medicament_id")
    prixUnitaire = serializers.DecimalField(source="prix_unitaire", max_digits=10, decimal_places=2)
    montantTotal = serializers.DecimalField(source="total", max_digits=10, decimal_places=2)
    numeroLot = serializers.CharField(source="numero_lot", required=False, allow_blank=True)
    dateFabrication = serializers.SerializerMethodField()
    dateExpiration = serializers.SerializerMethodField()
    medicament_nom = serializers.CharField(source="medicament.nom", read_only=True)
    
    class Meta:
        model = LigneCommande
        fields = ["id", "achatId", "medicamentId", "medicament_nom", "quantite", 
                  "prixUnitaire", "montantTotal", "numeroLot", "dateFabrication", "dateExpiration"]
    
    def get_dateFabrication(self, obj):
        if obj.date_fabrication:
            return str(obj.date_fabrication).split("T")[0] if "T" in str(obj.date_fabrication) else str(obj.date_fabrication)
        return None
    
    def get_dateExpiration(self, obj):
        if obj.date_expiration:
            return str(obj.date_expiration).split("T")[0] if "T" in str(obj.date_expiration) else str(obj.date_expiration)
        return None


class BonCommandeSerializer(serializers.ModelSerializer):
    pharmacieId = serializers.IntegerField(source="pharmacie_id", required=False, allow_null=True)
    fournisseurId = serializers.IntegerField(source="fournisseur_id")
    fournisseur_nom = serializers.CharField(source="fournisseur.nom", read_only=True)
    userId = serializers.IntegerField(source="user_id", required=False, default=1)
    dateCommande = serializers.SerializerMethodField()
    dateLivraison = serializers.SerializerMethodField()
    montantTotal = serializers.DecimalField(source="total_ttc", max_digits=10, decimal_places=2, required=False)
    lignes = LigneCommandeSerializer(many=True, read_only=True)
    
    class Meta:
        model = BonCommande
        fields = ["id", "code", "numero", "pharmacieId", "fournisseurId", "fournisseur_nom",
                  "userId", "dateCommande", "dateLivraison", "statut", "total_ht", "total_tva",
                  "montantTotal", "notes", "lignes"]
    
    def get_dateCommande(self, obj):
        if obj.date_commande:
            return str(obj.date_commande).split("T")[0] if "T" in str(obj.date_commande) else str(obj.date_commande)
        return None
    
    def get_dateLivraison(self, obj):
        if obj.date_livraison:
            return str(obj.date_livraison).split("T")[0] if "T" in str(obj.date_livraison) else str(obj.date_livraison)
        return None


class LigneDistributionSerializer(serializers.ModelSerializer):
    medicamentId = serializers.IntegerField(source="medicament_id")
    lotStockId = serializers.IntegerField(source="lot_id", required=False, allow_null=True)
    quantiteDemandee = serializers.IntegerField(source="quantite_demandee")
    quantiteEnvoyee = serializers.IntegerField(source="quantite_envoyee", required=False, default=0)
    class Meta:
        model = LigneDistribution
        fields = ["id", "medicamentId", "lotStockId", "quantiteDemandee", "quantiteEnvoyee"]


class DistributionSerializer(serializers.ModelSerializer):
    pharmacieSourceId = serializers.IntegerField(source="pharmacie_source_id")
    pharmacieDestinationId = serializers.IntegerField(source="pharmacie_destination_id")
    depotId = serializers.IntegerField(source="pharmacie_source_id", read_only=True)
    pharmacieId = serializers.IntegerField(source="pharmacie_destination_id", read_only=True)
    dateCreation = serializers.SerializerMethodField()
    dateDemande = serializers.SerializerMethodField()
    dateValidation = serializers.SerializerMethodField()
    dateExpedition = serializers.SerializerMethodField()
    dateReception = serializers.SerializerMethodField()
    lignes = LigneDistributionSerializer(many=True, read_only=True)
    
    class Meta:
        model = Distribution
        fields = ["id", "code", "pharmacieSourceId", "pharmacieDestinationId",
                  "depotId", "pharmacieId", "dateCreation",
                  "dateDemande", "dateValidation", "dateExpedition", "dateReception",
                  "statut", "notes", "lignes"]
    
    def get_dateCreation(self, obj):
        return obj.created_at.isoformat() if obj.created_at else None
    
    def get_dateDemande(self, obj):
        return obj.date_demande.isoformat() if obj.date_demande else None
    
    def get_dateValidation(self, obj):
        return obj.date_validation.isoformat() if obj.date_validation else None
    
    def get_dateExpedition(self, obj):
        return obj.date_expedition.isoformat() if obj.date_expedition else None
    
    def get_dateReception(self, obj):
        return obj.date_reception.isoformat() if obj.date_reception else None




class LigneInventaireSerializer(serializers.ModelSerializer):
    inventaireId = serializers.IntegerField(source="inventaire_id", read_only=True)
    medicamentId = serializers.IntegerField(source="medicament_id")
    lotStockId = serializers.IntegerField(source="lot_id")
    stockSysteme = serializers.IntegerField(source="stock_systeme")
    stockReel = serializers.IntegerField(source="stock_reel")
    ajustementApplique = serializers.BooleanField(source="ajustement_applique")
    
    class Meta:
        model = LigneInventaire
        fields = ["id", "inventaireId", "medicamentId", "lotStockId", 
                  "stockSysteme", "stockReel", "ecart", "ajustementApplique"]


class InventaireSerializer(serializers.ModelSerializer):
    pharmacieId = serializers.IntegerField(source="pharmacie_id")
    userId = serializers.IntegerField(source="user_id", required=False, default=1)
    dateCreation = serializers.SerializerMethodField()
    dateFinalisation = serializers.SerializerMethodField()
    lignes = LigneInventaireSerializer(many=True, read_only=True)
    
    class Meta:
        model = Inventaire
        fields = ["id", "code", "pharmacieId", "userId", "dateCreation", 
                  "dateFinalisation", "statut", "notes", "lignes"]
    
    def get_dateCreation(self, obj):
        return obj.date_creation.isoformat() if obj.date_creation else None
    
    def get_dateFinalisation(self, obj):
        return obj.date_finalisation.isoformat() if obj.date_finalisation else None



class AlerteSerializer(serializers.ModelSerializer):
    typeAlerte = serializers.CharField(source="type_alerte")
    medicamentId = serializers.IntegerField(source="medicament_id", required=False, allow_null=True)
    lotId = serializers.IntegerField(source="lot_id", required=False, allow_null=True)
    pharmacieId = serializers.IntegerField(source="pharmacie_id", required=False, allow_null=True)
    dateCreation = serializers.SerializerMethodField()
    medicament_nom = serializers.CharField(source="medicament.nom", read_only=True, default="")
    pharmacie_nom = serializers.CharField(source="pharmacie.nom", read_only=True, default="")
    
    class Meta:
        model = Alerte
        fields = ["id", "typeAlerte", "niveau", "titre", "message", 
                  "medicamentId", "lotId", "pharmacieId", "lu", "dateCreation",
                  "medicament_nom", "pharmacie_nom"]
    
    def get_dateCreation(self, obj):
        return obj.date_creation.isoformat() if obj.date_creation else None


class LigneRetourSerializer(serializers.ModelSerializer):
    retourId = serializers.IntegerField(source="retour_id", read_only=True)
    medicamentId = serializers.IntegerField(source="medicament_id")
    lotStockId = serializers.IntegerField(source="lot_id", required=False, allow_null=True)
    quantiteRetournee = serializers.IntegerField(source="quantite_retournee")
    prixUnitaire = serializers.DecimalField(source="prix_unitaire", max_digits=10, decimal_places=2)
    
    class Meta:
        model = LigneRetour
        fields = ["id", "retourId", "medicamentId", "lotStockId", "quantiteRetournee", "prixUnitaire", "montant"]


class RetourSerializer(serializers.ModelSerializer):
    venteId = serializers.IntegerField(source="vente_id")
    patientId = serializers.IntegerField(source="client_id", required=False, allow_null=True)
    pharmacieId = serializers.IntegerField(source="pharmacie_id", required=False, allow_null=True)
    dateRetour = serializers.SerializerMethodField()
    montantRembourse = serializers.DecimalField(source="montant_rembourse", max_digits=10, decimal_places=2)
    lignes = LigneRetourSerializer(many=True, read_only=True)
    
    class Meta:
        model = RetourClient
        fields = ["id", "code", "venteId", "patientId", "pharmacieId", "dateRetour", "motif", "notes", "montantRembourse", "lignes"]
    
    def get_dateRetour(self, obj):
        return obj.date_retour.isoformat() if obj.date_retour else None


class LogActiviteSerializer(serializers.ModelSerializer):
    userId = serializers.IntegerField(source="user_id")
    userNom = serializers.CharField(source="user_nom")
    pharmacieId = serializers.IntegerField(source="pharmacie_id", required=False, allow_null=True)
    pharmacieNom = serializers.CharField(source="pharmacie.nom", read_only=True, default="")
    dateAction = serializers.SerializerMethodField()
    
    class Meta:
        model = LogActivite
        fields = ["id", "userId", "userNom", "action", "module", "details", 
                  "pharmacieId", "pharmacieNom", "ip_address", "dateAction"]
    
    def get_dateAction(self, obj):
        return obj.date_action.isoformat() if obj.date_action else None


