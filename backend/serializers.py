from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer
from .models import *

class PolygonPersilSerializer(serializers.ModelSerializer):
    class Meta:
        model = PolygonPersil
        fields = ['id_persil', 'geom']

class HistoryAcquisitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = HistoryAcquisition
        fields = [
            'id_history',
            'status',
            'deskripsi'
        ]
class AcquisitionSerializer(serializers.ModelSerializer):
    id_persil = PolygonPersilSerializer()

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
            'id_persil'
        ]

    def create(self, validated_data):
        persil_data = validated_data.pop('id_persil')
        persil = PolygonPersil.objects.create(**persil_data)

        return Acquisition.objects.create(
            id_persil=persil,
            **validated_data
        )


class LandAcquisitionProjectSerializer(serializers.ModelSerializer):
    id_persil = PolygonPersilSerializer()
    acquisitions = AcquisitionSerializer(
        many=True,
        source='AcquisitonProject',
        required=False
    )

    class Meta:
        model = LandAcquisitionProject
        fields = [
            'id_project',
            'nama_project',
            'owner_project',
            'tanggal_dibuat',
            'id_persil',
            'acquisitions'
        ]
        read_only_fields = ['tanggal_dibuat']

    def create(self, validated_data):
        acquisitions_data = validated_data.pop('AcquisitonProject', [])
        persil_data = validated_data.pop('id_persil')

        persil = PolygonPersil.objects.create(**persil_data)

        project = LandAcquisitionProject.objects.create(
            id_persil=persil,
            **validated_data
        )

        for acq in acquisitions_data:
            acq_persil_data = acq.pop('id_persil')
            acq_persil = PolygonPersil.objects.create(**acq_persil_data)

            Acquisition.objects.create(
                id_project=project,
                id_persil=acq_persil,
                **acq
            )

        return project


class LandKategoriSerializer(serializers.ModelSerializer):
    class Meta:
        model = LandKategori
        fields = ('id', 'code', 'label')


class LandStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = LandStatus
        fields = ('id', 'code', 'label')


class LandInventorySerializer(serializers.ModelSerializer):
    id_persil = PolygonPersilSerializer()

    kategori_detail = LandKategoriSerializer(
        source='kategori',
        read_only=True
    )
    status_detail = LandStatusSerializer(
        source='status',
        read_only=True
    )

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
            'id_persil',
        ]

    def create(self, validated_data):
        persil_data = validated_data.pop('id_persil')
        persil = PolygonPersil.objects.create(**persil_data)

        return LandInventory.objects.create(
            id_persil=persil,
            **validated_data
        )
