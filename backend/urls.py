from rest_framework.routers import DefaultRouter
from .views import LandInventoryViewSet,LandAcquisitionViewSet,LandAcquisitionProjectViewSet

router = DefaultRouter()
router.register(r'LandInventory', LandInventoryViewSet, basename='LandInventory')
router.register(r'LandAcquisition', LandAcquisitionViewSet, basename='LandAcquisition')
router.register(r'LandAcquisitionProject', LandAcquisitionProjectViewSet, basename='LandAcquisitionProject ')


urlpatterns = router.urls
