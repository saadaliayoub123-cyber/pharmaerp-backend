import django, os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pharmaerp.settings")
django.setup()

from pharmacy.models import *
from datetime import date, timedelta
from decimal import Decimal
import random

print("=== ADD URGENT DATA ===")

# 1. Marquer 5 medicaments sur ordonnance
print("1. Sur ordonnance...")
meds = list(Medicament.objects.all()[:5])
for m in meds:
    m.sur_ordonnance = True
    m.save()
print(f"   OK: {len([m for m in Medicament.objects.all() if m.sur_ordonnance])} medicaments sur ordonnance")

# 2. Créer lots avec expiration proche
print("2. Lots expiration proche...")
depot = Pharmacie.objects.filter(type="depot").first()
meds_urgent = list(Medicament.objects.all()[:3])

for i, med in enumerate(meds_urgent):
    LotStock.objects.create(
        medicament=med,
        pharmacie=depot,
        numero_lot=f"LOT-URGENT-{i+1}",
        quantite=random.randint(20, 100),
        quantite_initiale=100,
        date_fabrication=date.today() - timedelta(days=300),
        date_expiration=date.today() + timedelta(days=random.randint(3, 25)),
        prix_achat=med.prix_achat,
    )
print(f"   OK: 3 lots avec expiration proche crees")

print("=== DONE ===")
print(f"Total lots: {LotStock.objects.count()}")
print(f"Sur ordonnance: {Medicament.objects.filter(sur_ordonnance=True).count()}")
