from rest_framework.routers import DefaultRouter
from .views import LandInventoryViewSet,LandAcquisitionViewSet,ProjectViewSet,LandInventoryDocumentViewSet,LandInventoryRasterViewSet,LandInventoryThemeMapViewSet

router = DefaultRouter()
router.register(r'LandInventory', LandInventoryViewSet, basename='LandInventory')
router.register(r'LandInventoryThemeMap', LandInventoryThemeMapViewSet, basename='LandInventoryThemeMap')
router.register(r'LandInventoryRaster', LandInventoryRasterViewSet, basename='LandInventoryRaster')
router.register(r'LandInventoryDocument', LandInventoryDocumentViewSet, basename='LandInventoryDocument')
router.register(r'LandAcquisition', LandAcquisitionViewSet, basename='LandAcquisition')
router.register(r'Project', ProjectViewSet, basename='Project ')


urlpatterns = router.urls
