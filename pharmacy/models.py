from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Pharmacie(models.Model):
    TYPE_CHOICES = [
        ("pharmacie", "Pharmacie"),
        ("depot", "Depot Central"),
        ("clinique", "Clinique"),
        ("hopital", "Hopital"),
    ]
    code = models.CharField(max_length=50, unique=True, default="PHA-000")
    nom = models.CharField(max_length=200)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default="pharmacie")
    adresse = models.TextField(blank=True)
    ville = models.CharField(max_length=100, blank=True)
    telephone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    responsable = models.CharField(max_length=200, blank=True)
    ice = models.CharField(max_length=50, blank=True)
    rc = models.CharField(max_length=50, blank=True)
    actif = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["nom"]

    def __str__(self):
        return self.nom


class Categorie(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    couleur = models.CharField(max_length=20, default="#3B82F6")
    icone = models.CharField(max_length=10, default="P")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["nom"]

    def __str__(self):
        return self.nom


class Fournisseur(models.Model):
    code = models.CharField(max_length=50, unique=True, default="FRN-000")
    nom = models.CharField(max_length=200)
    contact = models.CharField(max_length=100, blank=True)
    telephone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    adresse = models.TextField(blank=True)
    ville = models.CharField(max_length=100, blank=True)
    ice = models.CharField(max_length=50, blank=True)
    delai_livraison_jours = models.IntegerField(default=7)
    score_qualite = models.IntegerField(default=3)
    actif = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["nom"]

    def __str__(self):
        return self.nom


class Medicament(models.Model):
    code = models.CharField(max_length=50, unique=True)
    nom = models.CharField(max_length=200)
    dci = models.CharField(max_length=200, blank=True)
    categorie = models.ForeignKey(Categorie, on_delete=models.SET_NULL, null=True, related_name="medicaments")
    forme = models.CharField(max_length=50, blank=True)
    dosage = models.CharField(max_length=100, blank=True)
    laboratoire = models.CharField(max_length=200, blank=True)
    prix_achat = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    prix_vente = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tva = models.DecimalField(max_digits=5, decimal_places=2, default=20)
    seuil_alerte = models.IntegerField(default=10, help_text="Seuil pour pharmacies")
    seuil_depot = models.IntegerField(default=500, help_text="Seuil pour depot central")
    delai_securite_pharmacie = models.IntegerField(default=7, help_text="Jours stock securite pharmacie")
    delai_securite_depot = models.IntegerField(default=30, help_text="Jours stock securite depot")
    sur_ordonnance = models.BooleanField(default=False)
    actif = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["nom"]

    def __str__(self):
        return self.nom


class LotStock(models.Model):
    medicament = models.ForeignKey(Medicament, on_delete=models.CASCADE, related_name="lots")
    pharmacie = models.ForeignKey(Pharmacie, on_delete=models.CASCADE, related_name="lots", null=True, blank=True)
    numero_lot = models.CharField(max_length=100)
    quantite = models.IntegerField(default=0)
    quantite_initiale = models.IntegerField(default=0)
    date_fabrication = models.DateField(null=True, blank=True)
    date_expiration = models.DateField()
    prix_achat = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fournisseur = models.ForeignKey(Fournisseur, on_delete=models.SET_NULL, null=True, blank=True)
    bloque = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["date_expiration"]

    def __str__(self):
        return f"{self.medicament.nom} - {self.numero_lot}"


class Client(models.Model):
    GENRE_CHOICES = [("M", "Homme"), ("F", "Femme")]
    code = models.CharField(max_length=50, unique=True, default="PAT-000")
    nom = models.CharField(max_length=200)
    prenom = models.CharField(max_length=200, blank=True)
    cin = models.CharField(max_length=50, blank=True)
    type_client = models.CharField(max_length=50, default="particulier")
    genre = models.CharField(max_length=1, choices=GENRE_CHOICES, default="M")
    date_naissance = models.DateField(null=True, blank=True)
    telephone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    adresse = models.TextField(blank=True)
    ville = models.CharField(max_length=100, blank=True)
    ice = models.CharField(max_length=50, blank=True)
    pharmacie = models.ForeignKey(Pharmacie, on_delete=models.SET_NULL, related_name="patients", null=True, blank=True)
    actif = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["nom"]

    def __str__(self):
        return f"{self.prenom} {self.nom}"


class Vente(models.Model):
    code = models.CharField(max_length=50, unique=True, default="VTE-000")
    numero = models.CharField(max_length=50, blank=True)
    pharmacie = models.ForeignKey(Pharmacie, on_delete=models.PROTECT, related_name="ventes", null=True, blank=True)
    client = models.ForeignKey(Client, on_delete=models.SET_NULL, null=True, blank=True)
    user_id = models.IntegerField(default=1)
    date_vente = models.DateTimeField(default=timezone.now)
    total_ht = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_tva = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_ttc = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    mode_paiement = models.CharField(max_length=20, default="especes")
    statut = models.CharField(max_length=20, default="validee")
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date_vente"]

    def __str__(self):
        return f"Vente {self.code}"


class LigneVente(models.Model):
    vente = models.ForeignKey(Vente, on_delete=models.CASCADE, related_name="lignes")
    medicament = models.ForeignKey(Medicament, on_delete=models.PROTECT)
    lot = models.ForeignKey(LotStock, on_delete=models.SET_NULL, null=True, blank=True)
    quantite = models.IntegerField(default=1)
    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)


class BonCommande(models.Model):
    STATUT_CHOICES = [
        ("brouillon", "Brouillon"),
        ("commande", "Commandee"),
        ("recue", "Recue"),
        ("annulee", "Annulee"),
    ]
    code = models.CharField(max_length=50, unique=True, default="ACH-000")
    numero = models.CharField(max_length=50, blank=True)
    pharmacie = models.ForeignKey(Pharmacie, on_delete=models.SET_NULL, related_name="commandes", null=True, blank=True)
    fournisseur = models.ForeignKey(Fournisseur, on_delete=models.PROTECT)
    user_id = models.IntegerField(default=1)
    date_commande = models.DateField(default=timezone.now)
    date_livraison = models.DateField(null=True, blank=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="brouillon")
    total_ht = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_tva = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_ttc = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date_commande"]

    def __str__(self):
        return f"Achat {self.code}"


class LigneCommande(models.Model):
    bon_commande = models.ForeignKey(BonCommande, on_delete=models.CASCADE, related_name="lignes")
    medicament = models.ForeignKey(Medicament, on_delete=models.PROTECT)
    quantite = models.IntegerField(default=1)
    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    numero_lot = models.CharField(max_length=100, blank=True)
    date_fabrication = models.DateField(null=True, blank=True)
    date_expiration = models.DateField(null=True, blank=True)


class Distribution(models.Model):
    STATUT_CHOICES = [
        ("demande", "Demandee"),
        ("valide", "Validee"),
        ("expedie", "Expediee"),
        ("recu", "Recue"),
        ("annule", "Annulee"),
    ]
    code = models.CharField(max_length=50, unique=True, default="DIST-000")
    pharmacie_source = models.ForeignKey(Pharmacie, on_delete=models.PROTECT, related_name="distributions_envoyees")
    pharmacie_destination = models.ForeignKey(Pharmacie, on_delete=models.PROTECT, related_name="distributions_recues")
    date_demande = models.DateTimeField(default=timezone.now)
    date_validation = models.DateTimeField(null=True, blank=True)
    date_expedition = models.DateTimeField(null=True, blank=True)
    date_reception = models.DateTimeField(null=True, blank=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="demande")
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date_demande"]

    def __str__(self):
        return f"Distribution {self.code}"


class LigneDistribution(models.Model):
    distribution = models.ForeignKey(Distribution, on_delete=models.CASCADE, related_name="lignes")
    medicament = models.ForeignKey(Medicament, on_delete=models.PROTECT)
    lot = models.ForeignKey(LotStock, on_delete=models.SET_NULL, null=True, blank=True)
    quantite_demandee = models.IntegerField(default=1)
    quantite_envoyee = models.IntegerField(default=0)


class Inventaire(models.Model):
    STATUT_CHOICES = [
        ("en_cours", "En cours"),
        ("finalise", "Finalise"),
        ("annule", "Annule"),
    ]
    code = models.CharField(max_length=50, unique=True, default="INV-000")
    pharmacie = models.ForeignKey(Pharmacie, on_delete=models.CASCADE, related_name="inventaires")
    user_id = models.IntegerField(default=1)
    date_creation = models.DateTimeField(default=timezone.now)
    date_finalisation = models.DateTimeField(null=True, blank=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="en_cours")
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date_creation"]

    def __str__(self):
        return f"Inventaire {self.code}"


class LigneInventaire(models.Model):
    inventaire = models.ForeignKey(Inventaire, on_delete=models.CASCADE, related_name="lignes")
    medicament = models.ForeignKey(Medicament, on_delete=models.PROTECT)
    lot = models.ForeignKey(LotStock, on_delete=models.CASCADE, related_name="inventaire_lignes")
    stock_systeme = models.IntegerField(default=0)
    stock_reel = models.IntegerField(default=0)
    ecart = models.IntegerField(default=0)
    ajustement_applique = models.BooleanField(default=False)


class Alerte(models.Model):
    TYPE_CHOICES = [
        ("rupture", "Rupture de stock"),
        ("stock_faible", "Stock faible"),
        ("expiration_proche", "Expiration proche"),
        ("expire", "Produit expire"),
        ("point_commande", "Point de commande atteint"),
    ]
    NIVEAU_CHOICES = [
        ("info", "Info"),
        ("warning", "Avertissement"),
        ("danger", "Critique"),
    ]
    
    type_alerte = models.CharField(max_length=30, choices=TYPE_CHOICES)
    niveau = models.CharField(max_length=20, choices=NIVEAU_CHOICES, default="warning")
    titre = models.CharField(max_length=200)
    message = models.TextField()
    medicament = models.ForeignKey(Medicament, on_delete=models.CASCADE, null=True, blank=True)
    lot = models.ForeignKey(LotStock, on_delete=models.CASCADE, null=True, blank=True)
    pharmacie = models.ForeignKey(Pharmacie, on_delete=models.CASCADE, null=True, blank=True)
    lu = models.BooleanField(default=False)
    date_creation = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-date_creation"]

    def __str__(self):
        return self.titre


class RetourClient(models.Model):
    MOTIF_CHOICES = [
        ("defectueux", "Produit defectueux"),
        ("expire", "Produit expire"),
        ("erreur", "Erreur de commande"),
        ("allergie", "Allergie"),
        ("autre", "Autre"),
    ]
    code = models.CharField(max_length=50, unique=True, default="RET-000")
    vente = models.ForeignKey(Vente, on_delete=models.PROTECT, related_name="retours")
    client = models.ForeignKey(Client, on_delete=models.SET_NULL, null=True, blank=True)
    pharmacie = models.ForeignKey(Pharmacie, on_delete=models.PROTECT, null=True, blank=True)
    date_retour = models.DateTimeField(default=timezone.now)
    motif = models.CharField(max_length=20, choices=MOTIF_CHOICES, default="autre")
    notes = models.TextField(blank=True)
    montant_rembourse = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date_retour"]

    def __str__(self):
        return f"Retour {self.code}"


class LigneRetour(models.Model):
    retour = models.ForeignKey(RetourClient, on_delete=models.CASCADE, related_name="lignes")
    medicament = models.ForeignKey(Medicament, on_delete=models.PROTECT)
    lot = models.ForeignKey(LotStock, on_delete=models.SET_NULL, null=True, blank=True)
    quantite_retournee = models.IntegerField(default=1)
    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=2)
    montant = models.DecimalField(max_digits=10, decimal_places=2)


class LogActivite(models.Model):
    MODULE_CHOICES = [
        ("Auth", "Auth"),
        ("Medicaments", "Medicaments"),
        ("Categories", "Categories"),
        ("Fournisseurs", "Fournisseurs"),
        ("Patients", "Patients"),
        ("Pharmacies", "Pharmacies"),
        ("Stock", "Stock"),
        ("Ventes", "Ventes"),
        ("Achats", "Achats"),
        ("Distributions", "Distributions"),
        ("Inventaires", "Inventaires"),
        ("Retours", "Retours"),
        ("Alertes", "Alertes"),
        ("Systeme", "Systeme"),
    ]
    
    user_id = models.IntegerField(default=1)
    user_nom = models.CharField(max_length=200, default="System")
    action = models.CharField(max_length=200)
    module = models.CharField(max_length=50, choices=MODULE_CHOICES, default="Systeme")
    details = models.TextField(blank=True)
    pharmacie = models.ForeignKey(Pharmacie, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.CharField(max_length=50, blank=True)
    date_action = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-date_action"]

    def __str__(self):
        return f"{self.module}: {self.action}"


