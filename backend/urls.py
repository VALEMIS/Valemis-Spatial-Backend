from rest_framework.routers import DefaultRouter
from .views import LandInventoryViewSet

router = DefaultRouter()
router.register(r'lands', LandInventoryViewSet, basename='land')

urlpatterns = router.urls
