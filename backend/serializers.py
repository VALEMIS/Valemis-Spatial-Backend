from rest_framework import serializers
from .models import *

class HistoryAcquisitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = HistoryAcquisition
        fields = [
            'id_history',
            'status',
            'deskripsi'
        ]
class AcquisitionSerializer(serializers.ModelSerializer):
    histories = HistoryAcquisitionSerializer(many=True, read_only=True)

    class Meta:
        model = Acquisition
        fields = [
            'id_parcel',
            'id_project',
            'kode_parcel',
            'nama_pemilik',
            'desa',
            'luas',
            'status',
            'jumlah_bebas',
            'biaya_pembebasan',
            'tanggal_negosiasi',
            'geom',
            'histories'
        ]
class LandAcquisitionProjectSerializer(serializers.ModelSerializer):
    acquisitions = AcquisitionSerializer(
        many=True,
        read_only=True,
        source='AcquisitonProject'
    )

    class Meta:
        model = LandAcquisitionProject
        fields = [
            'id_project',
            'nama_project',
            'tanggal_dibuat',
            'acquisitions'
        ]




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
