from rest_framework.routers import DefaultRouter
from .views import LandInventoryViewSet,LandAcquisitionViewSet

router = DefaultRouter()
router.register(r'LandInventory', LandInventoryViewSet, basename='LandInventory')
router.register(r'LandAcquisition', LandAcquisitionViewSet, basename='LandAcquisition')


urlpatterns = router.urls
