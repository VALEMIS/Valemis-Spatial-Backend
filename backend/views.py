from rest_framework.viewsets import ModelViewSet
from .models import LandInventory
from .serializers import LandInventorySerializer

class LandInventoryViewSet(ModelViewSet):
    queryset = LandInventory.objects.all()
    serializer_class = LandInventorySerializer
    
