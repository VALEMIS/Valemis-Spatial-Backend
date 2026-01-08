from rest_framework.routers import DefaultRouter
from django.urls import path
from .views import LandInventoryViewSet,LandAcquisitionViewSet,ProjectViewSet,LandInventoryDocumentViewSet,LandInventoryRasterViewSet,LandInventoryThemeMapViewSet,api_analyze,LandAcquisitionHistoryViewSet
router = DefaultRouter()
router.register(r'LandInventory', LandInventoryViewSet, basename='LandInventory')
router.register(r'LandInventoryThemeMap', LandInventoryThemeMapViewSet, basename='LandInventoryThemeMap')
router.register(r'LandInventoryRaster', LandInventoryRasterViewSet, basename='LandInventoryRaster')
router.register(r'LandInventoryDocument', LandInventoryDocumentViewSet, basename='LandInventoryDocument')
router.register(r'LandAcquisition', LandAcquisitionViewSet, basename='LandAcquisition')
router.register(r'LandAcquisitionHistory', LandAcquisitionHistoryViewSet, basename='LandAcquisitionHistory')
router.register(r'Project', ProjectViewSet, basename='Project ')


urlpatterns = router.urls
urlpatterns += [
    path("analyze/", api_analyze, name="spatial_analyze"),
]