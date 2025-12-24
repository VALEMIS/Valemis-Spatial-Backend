from rest_framework import serializers
from .models import LandInventory,LandKategori,LandStatus,Acquisition,HistoryAcquisition

class LandKategoriSerializer(serializers.ModelSerializer):
    class Meta:
        model = LandKategori
        fields = ('id', 'code', 'label')


class LandStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = LandStatus
        fields = ('id', 'code', 'label')


class LandInventorySerializer(serializers.ModelSerializer):
    kategori_detail = LandKategoriSerializer(source='kategori', read_only=True)
    status_detail = LandStatusSerializer(source='status', read_only=True)

    class Meta:
        model = LandInventory
        fields = [
            'id_lahan',
            'kode_lahan',
            'nama_lokasi',
            'kategori',
            'kategori_detail',
            'status',
            'status_detail',
            'no_sertif',
            'geom',
        ]
