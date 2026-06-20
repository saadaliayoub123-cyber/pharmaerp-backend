from django.contrib import admin
from .models import (
    Pharmacie, Categorie, Fournisseur, Medicament, LotStock, 
    Client, Vente, LigneVente, BonCommande, LigneCommande,
    Distribution, LigneDistribution
)

admin.site.register(Pharmacie)
admin.site.register(Categorie)
admin.site.register(Fournisseur)
admin.site.register(Medicament)
admin.site.register(LotStock)
admin.site.register(Client)
admin.site.register(Vente)
admin.site.register(LigneVente)
admin.site.register(BonCommande)
admin.site.register(LigneCommande)
admin.site.register(Distribution)
admin.site.register(LigneDistribution)

from .models import Inventaire, LigneInventaire
admin.site.register(Inventaire)
admin.site.register(LigneInventaire)

from .models import Alerte
admin.site.register(Alerte)
