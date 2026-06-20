from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import rapports

router = DefaultRouter()
router.register(r"pharmacies", views.PharmacieViewSet)
router.register(r"categories", views.CategorieViewSet)
router.register(r"fournisseurs", views.FournisseurViewSet)
router.register(r"medicaments", views.MedicamentViewSet)
router.register(r"lots", views.LotStockViewSet)
router.register(r"clients", views.ClientViewSet)
router.register(r"ventes", views.VenteViewSet)
router.register(r"bons-commande", views.BonCommandeViewSet)
router.register(r"distributions", views.DistributionViewSet)
router.register(r"inventaires", views.InventaireViewSet)
router.register(r"alertes", views.AlerteViewSet)
router.register(r"retours", views.RetourViewSet)
router.register(r"logs", views.LogActiviteViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("dashboard/stats/", views.dashboard_stats, name="dashboard-stats"),
        path("rapports/stock/", rapports.rapport_stock, name="rapport-stock"),
    path("rapports/ventes/", rapports.rapport_ventes, name="rapport-ventes"),
    path("rapports/inventaire/", rapports.rapport_inventaire, name="rapport-inventaire"),
    path("rapports/fefo/", rapports.rapport_fefo, name="rapport-fefo"),
    path("rapports/facture/<int:vente_id>/", rapports.facture_vente, name="facture-vente"),
]





