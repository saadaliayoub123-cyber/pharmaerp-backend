import django, os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pharmaerp.settings")
django.setup()

from pharmacy.models import *
from datetime import date, timedelta
from django.utils import timezone
from decimal import Decimal
import random

print("=== SEED DATA ===")

print("1. Categories...")
cats_data = [
    ("Antibiotique", "#10B981", "P"),
    ("Antalgique", "#3B82F6", "P"),
    ("Anti-inflammatoire", "#F59E0B", "P"),
    ("Vitamine", "#EAB308", "P"),
    ("Antihypertenseur", "#EF4444", "P"),
    ("Antidiabetique", "#8B5CF6", "P"),
    ("Gastro", "#06B6D4", "P"),
    ("Dermato", "#EC4899", "P"),
]
for nom, couleur, icone in cats_data:
    Categorie.objects.get_or_create(nom=nom, defaults={"couleur": couleur, "icone": icone})
print("  OK:", Categorie.objects.count(), "categories")

print("2. Fournisseurs...")
fourn_data = [
    ("FRN-001", "Pharma Maroc", "Ahmed Bennani", "0522111111", "Casablanca"),
    ("FRN-002", "Medistock SARL", "Fatima Zahra", "0537222222", "Rabat"),
    ("FRN-003", "Cooper Pharma", "Karim Alaoui", "0524333333", "Marrakech"),
    ("FRN-004", "Sothema", "Said Idrissi", "0535444444", "Fes"),
]
for code, nom, contact, tel, ville in fourn_data:
    Fournisseur.objects.get_or_create(code=code, defaults={"nom": nom, "contact": contact, "telephone": tel, "ville": ville, "delai_livraison_jours": random.randint(3, 10), "score_qualite": random.randint(3, 5)})
print("  OK:", Fournisseur.objects.count(), "fournisseurs")

print("3. Medicaments...")
meds_data = [
    ("MED002", "Amoxicilline", "Amoxicilline trihydrate", "Antibiotique", "Comprime", "500mg", 25.50, 35.00),
    ("MED003", "Augmentin", "Amoxicilline + Acide clavulanique", "Antibiotique", "Comprime", "1g", 75.00, 95.00),
    ("MED004", "Doliprane Forte", "Paracetamol", "Antalgique", "Comprime", "1000mg", 18.00, 25.00),
    ("MED005", "Ibuprofene", "Ibuprofene", "Anti-inflammatoire", "Comprime", "400mg", 15.00, 22.00),
    ("MED006", "Vitamine C", "Acide ascorbique", "Vitamine", "Comprime", "1000mg", 30.00, 45.00),
    ("MED007", "Vitamine D3", "Cholecalciferol", "Vitamine", "Gouttes", "10000UI", 55.00, 75.00),
    ("MED008", "Aspegic", "Acide acetylsalicylique", "Antalgique", "Sachet", "1000mg", 22.00, 32.00),
    ("MED009", "Ventoline", "Salbutamol", "Anti-inflammatoire", "Spray", "100mcg", 45.00, 65.00),
    ("MED010", "Amlor", "Amlodipine", "Antihypertenseur", "Comprime", "5mg", 35.00, 50.00),
    ("MED011", "Coversyl", "Perindopril", "Antihypertenseur", "Comprime", "10mg", 65.00, 85.00),
    ("MED012", "Glucophage", "Metformine", "Antidiabetique", "Comprime", "1000mg", 28.00, 40.00),
    ("MED013", "Lantus", "Insuline glargine", "Antidiabetique", "Stylo", "100UI/ml", 380.00, 450.00),
    ("MED014", "Inexium", "Esomeprazole", "Gastro", "Comprime", "40mg", 85.00, 110.00),
    ("MED015", "Gaviscon", "Alginate", "Gastro", "Suspension", "500ml", 45.00, 65.00),
    ("MED016", "Hexomedine", "Hexamidine", "Dermato", "Solution", "0.1%", 35.00, 50.00),
]
for code, nom, dci, cat_nom, forme, dosage, pa, pv in meds_data:
    cat = Categorie.objects.filter(nom=cat_nom).first()
    Medicament.objects.get_or_create(code=code, defaults={"nom": nom, "dci": dci, "categorie": cat, "forme": forme, "dosage": dosage, "prix_achat": Decimal(str(pa)), "prix_vente": Decimal(str(pv)), "seuil_alerte": random.randint(10, 30), "seuil_depot": random.randint(200, 500), "delai_securite_pharmacie": 7, "delai_securite_depot": 30})
print("  OK:", Medicament.objects.count(), "medicaments")

print("4. Lots Stock...")
depot = Pharmacie.objects.filter(type="depot").first()
pharmacies_normales = list(Pharmacie.objects.filter(type="pharmacie"))
if depot:
    for med in Medicament.objects.all():
        LotStock.objects.get_or_create(medicament=med, pharmacie=depot, numero_lot="LOT-" + med.code + "-DEP", defaults={"quantite": random.randint(500, 2000), "quantite_initiale": 2000, "date_fabrication": date.today() - timedelta(days=random.randint(30, 180)), "date_expiration": date.today() + timedelta(days=random.randint(180, 730)), "prix_achat": med.prix_achat, "fournisseur": Fournisseur.objects.order_by("?").first()})
        for ph in pharmacies_normales:
            LotStock.objects.get_or_create(medicament=med, pharmacie=ph, numero_lot="LOT-" + med.code + "-" + ph.code[-3:], defaults={"quantite": random.randint(20, 150), "quantite_initiale": 150, "date_fabrication": date.today() - timedelta(days=random.randint(30, 180)), "date_expiration": date.today() + timedelta(days=random.randint(180, 730)), "prix_achat": med.prix_achat})
print("  OK:", LotStock.objects.count(), "lots")

print("5. Patients...")
patients_data = [
    ("PAT-001", "Bennani", "Mohamed", "AB123456", "0661111111", "M"),
    ("PAT-002", "Alaoui", "Fatima", "BB234567", "0662222222", "F"),
    ("PAT-003", "Idrissi", "Karim", "CC345678", "0663333333", "M"),
    ("PAT-004", "Tazi", "Aicha", "DD456789", "0664444444", "F"),
    ("PAT-005", "Fassi", "Youssef", "EE567890", "0665555555", "M"),
    ("PAT-006", "Bouazza", "Khadija", "FF678901", "0666666666", "F"),
    ("PAT-007", "Chraibi", "Hassan", "GG789012", "0667777777", "M"),
    ("PAT-008", "Hakimi", "Salma", "HH890123", "0668888888", "F"),
    ("PAT-009", "Lamrini", "Omar", "II901234", "0669999999", "M"),
    ("PAT-010", "Berrada", "Nadia", "JJ012345", "0660000000", "F"),
]
for code, nom, prenom, cin, tel, genre in patients_data:
    ph = random.choice(pharmacies_normales) if pharmacies_normales else None
    Client.objects.get_or_create(code=code, defaults={"nom": nom, "prenom": prenom, "cin": cin, "telephone": tel, "genre": genre, "pharmacie": ph})
print("  OK:", Client.objects.count(), "patients")

print("6. Ventes...")
ventes_before = Vente.objects.count()
for i in range(40):
    ph = random.choice(pharmacies_normales) if pharmacies_normales else None
    if not ph: continue
    client = random.choice(list(Client.objects.filter(pharmacie=ph))) if Client.objects.filter(pharmacie=ph).exists() else None
    jours_ago = random.randint(0, 60)
    date_v = timezone.now() - timedelta(days=jours_ago, hours=random.randint(0, 23))
    code_v = "VTE-AUTO-" + str(ventes_before + i + 1).zfill(3)
    lots_ph = list(LotStock.objects.filter(pharmacie=ph, quantite__gt=10))
    if not lots_ph: continue
    selected_lots = random.sample(lots_ph, min(random.randint(1, 3), len(lots_ph)))
    total = Decimal("0")
    lignes_v = []
    for lot in selected_lots:
        qte = random.randint(1, 5)
        if lot.quantite < qte: continue
        prix = lot.medicament.prix_vente
        total += Decimal(str(qte)) * prix
        lignes_v.append((lot, qte, prix))
        lot.quantite -= qte
        lot.save()
    if not lignes_v: continue
    vente = Vente.objects.create(code=code_v, numero=code_v, pharmacie=ph, client=client, date_vente=date_v, total_ht=total / Decimal("1.20"), total_tva=total - (total / Decimal("1.20")), total_ttc=total, mode_paiement=random.choice(["especes", "carte", "cheque"]), statut="validee")
    for lot, qte, prix in lignes_v:
        LigneVente.objects.create(vente=vente, medicament=lot.medicament, lot=lot, quantite=qte, prix_unitaire=prix, total=Decimal(str(qte)) * prix)
print("  OK:", Vente.objects.count(), "ventes")

print("7. Achats...")
for i in range(10):
    fourn = random.choice(list(Fournisseur.objects.all()))
    jours_ago = random.randint(0, 90)
    date_a = date.today() - timedelta(days=jours_ago)
    code_a = "ACH-AUTO-" + str(i+1).zfill(3)
    meds_a = random.sample(list(Medicament.objects.all()), random.randint(2, 5))
    total = Decimal("0")
    bon = BonCommande.objects.create(code=code_a, numero=code_a, pharmacie=depot, fournisseur=fourn, date_commande=date_a, statut="recue", date_livraison=date_a + timedelta(days=fourn.delai_livraison_jours))
    for med in meds_a:
        qte = random.randint(50, 500)
        prix = med.prix_achat
        ligne_total = Decimal(str(qte)) * prix
        total += ligne_total
        LigneCommande.objects.create(bon_commande=bon, medicament=med, quantite=qte, prix_unitaire=prix, total=ligne_total, numero_lot="LOT-" + med.code + "-A" + str(i+1), date_expiration=date.today() + timedelta(days=random.randint(180, 730)))
    bon.total_ttc = total
    bon.total_ht = total / Decimal("1.20")
    bon.total_tva = total - bon.total_ht
    bon.save()
print("  OK:", BonCommande.objects.count(), "achats")

print("8. Distributions...")
for i in range(8):
    if not pharmacies_normales: break
    ph_dest = random.choice(pharmacies_normales)
    jours_ago = random.randint(0, 30)
    date_d = timezone.now() - timedelta(days=jours_ago)
    code_d = "DIST-AUTO-" + str(i+1).zfill(3)
    statut = random.choice(["demande", "valide", "expedie", "recu", "recu", "recu"])
    dist = Distribution.objects.create(code=code_d, pharmacie_source=depot, pharmacie_destination=ph_dest, date_demande=date_d, statut=statut, date_validation=date_d + timedelta(hours=2) if statut != "demande" else None, date_expedition=date_d + timedelta(days=1) if statut in ["expedie", "recu"] else None, date_reception=date_d + timedelta(days=2) if statut == "recu" else None)
    meds_d = random.sample(list(Medicament.objects.all()), random.randint(2, 4))
    for med in meds_d:
        qte = random.randint(20, 100)
        LigneDistribution.objects.create(distribution=dist, medicament=med, quantite_demandee=qte, quantite_envoyee=qte if statut in ["expedie", "recu"] else 0)
print("  OK:", Distribution.objects.count(), "distributions")

print("=== DONE ===")
