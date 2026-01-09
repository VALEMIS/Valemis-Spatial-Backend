import os
import uuid
import zipfile
import subprocess
import requests
import psycopg2

from django.conf import settings
from rest_framework import serializers
from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer
from .models import *

from django.db import transaction

# class PolygonPersilSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = PolygonPersil
#         fields = ['id_persil', 'geom']
# class PolygonPersilSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = PolygonPersil
#         fields = ['id_persil', 'geom']



# ============================================
# *************LAND ACQUISITION***************
# ============================================
class HistoryAcquisitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = HistoryAcquisition
        fields = [
            'id_history',
            'status',
            'deskripsi',
            'date_created'
        ]
class AcquisitionAssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = AcquisitionAsset
        fields = [
            'id_parcel_asset',
            'id_asset'
        ]
class AcquisitionSerializer(serializers.ModelSerializer):
    # id_persil = PolygonPersilSerializer()
    # id_asset = AcquisitionAssetSerializer()
    
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
            # 'id_asset'
            # 'id_persil'
        ]

    # def create(self, validated_data):
    #     persil_data = validated_data.pop('id_persil')
    #     persil = PolygonPersil.objects.create(**persil_data)

    #     return Acquisition.objects.create(
    #         id_persil=persil,
    #         **validated_data
    #     )
    def create(self, validated_data):
    # buat acquisition utama dulu
        instance = super().create(validated_data)

        # simpan history pertama (status awal)
        HistoryAcquisition.objects.create(
            id_parcel=instance,
            status=instance.status,
            deskripsi=f"Data dibuat dengan status {instance.status}"
        )

        # jika status awal sudah "Bebas", langsung masuk ke LandInventory
        if instance.status == "Bebas":
            LandInventory.objects.create(
                id_project=instance.id_project,
                kode_lahan=instance.kode_parcel,    
                geom=instance.geom
            )

        return instance

    def update(self, instance, validated_data):
        previous_status = instance.status

        # update acquisition dulu
        instance = super().update(instance, validated_data)

        # jika status berubah -> simpan history
        if previous_status != instance.status:
            HistoryAcquisition.objects.create(
                id_parcel=instance,
                status=instance.status,
                deskripsi=f"Status berubah dari {previous_status} ke {instance.status}"
            )

        # jika status berubah menjadi "Bebas"
        if previous_status != "Bebas" and instance.status == "Bebas":

            # 1️⃣ masukkan ke LandInventory
            LandInventory.objects.create(
                id_project=instance.id_project,
                kode_lahan=instance.kode_parcel,
                geom=instance.geom
            )

            # 2️⃣ hapus geometry dari Acquisition
            instance.geom = None
            instance.save(update_fields=["geom"])

        return instance


class ProjectDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectDetail
        fields = "__all__"
class ProjectSerializer(serializers.ModelSerializer):
    project_details = ProjectDetailSerializer(many=True)

    class Meta:
        model = Project
        fields = [
            'id_project',
            'nama_project',
            'owner_project',
            'tanggal_dibuat',
            'basemap',
            'iupk',
            'batas_admin',
            'geom',
            'date_start',
            'date_end',
            'project_details'
        ]
        read_only_fields = ['tanggal_dibuat']

    def create(self, validated_data):
        details_data = validated_data.pop('project_details', [])
        project = Project.objects.create(**validated_data)
        for detail in details_data:
            ProjectDetail.objects.create(id_project=project, **detail)
        return project

    def update(self, instance, validated_data):
        # Update fields Project
        instance.nama_project = validated_data.get('nama_project', instance.nama_project)
        instance.owner_project = validated_data.get('owner_project', instance.owner_project)
        instance.basemap = validated_data.get('basemap', instance.basemap)
        instance.iupk = validated_data.get('iupk', instance.iupk)
        instance.batas_admin = validated_data.get('batas_admin', instance.batas_admin)
        instance.geom = validated_data.get('geom', instance.geom)
        instance.save()

        # Update nested ProjectDetail
        details_data = validated_data.get('project_details')
        if details_data is not None:
            # Hapus semua dulu (opsional, atau bisa update matching id)
            instance.project_details.all().delete()
            for detail in details_data:
                ProjectDetail.objects.create(id_project=instance, **detail)

        return instance

# ============================================
# ***************LAND INVENTORY***************
# ============================================
class LandKategoriSerializer(serializers.ModelSerializer):
    class Meta:
        model = LandKategori
        fields = ('id', 'code', 'label')


class LandStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = LandStatus
        fields = ('id', 'code', 'label')

class LandInventoryDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = LandInventoryDocument
        fields = [
            'id_document',
            'id_lahan',
            'nama_dokumen',
            'file',
        ]

class LandInventorySerializer(serializers.ModelSerializer):
    # id_persil = PolygonPersilSerializer()

    kategori_detail = LandKategoriSerializer(
        source='kategori',
        read_only=True
    )
    status_detail = LandStatusSerializer(
        source='status',
        read_only=True
    )
    documents = LandInventoryDocumentSerializer(
        many=True,
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
            'documents',
            'no_sertif',
            'id_project',
            'geom',
        ]
    
    # def create(self, validated_data):
    #     persil_data = validated_data.pop('id_persil')
    #     persil = PolygonPersil.objects.create(**persil_data)
    # def create(self, validated_data):
    #     persil_data = validated_data.pop('id_persil')
    #     persil = PolygonPersil.objects.create(**persil_data)

        # return LandInventory.objects.create(
        #     id_persil=persil,
        #     **validated_data
        # )

class LandInventoryRasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = LandInventoryRaster
        fields = [
            "id_raster",
            "id_project",
            "store_name",
            "nama",
            'raster_path'
        ]
        read_only_fields = ["id_raster"]

    def create(self, validated_data):
        auth = ("admin", "geoserver")

        with transaction.atomic():
            # 1️⃣ SIMPAN KE DATABASE + FILESYSTEM
            raster_obj = LandInventoryRaster.objects.create(**validated_data)

            file_path = raster_obj.raster_path.path
            store_name = raster_obj.store_name
            nama = raster_obj.nama
            print("Proses 1")
            # 2️⃣ UPLOAD KE GEOSERVER
            upload_url = (
                f"http://103.150.191.85:8888/geoserver/rest/workspaces/"
                f"raster_valemis/coveragestores/"
                f"{store_name}_store/file.geotiff"
            )
            print("Proses 2")
            with open(file_path, "rb") as f:
                resp = requests.put(
                    upload_url,
                    auth=auth,
                    headers={"Content-Type": "image/tiff"},
                    data=f,
                    timeout=120
                )
            print("Proses 1")
            if resp.status_code not in (200, 201):
                raise serializers.ValidationError(
                    {"geoserver store": resp.text}
                )

            # 3️⃣ PUBLISH COVERAGE
            publish_url = (
                f"http://103.150.191.85:8888/geoserver/rest/workspaces/"
                f"raster_valemis/coveragestores/"
                f"{store_name}_store/coverages"
            )

            xml = f"""
            <coverage>
                <name>{store_name}</name>
                <title>{nama}</title>
                <enabled>true</enabled>
            </coverage>
            """

            resp = requests.post(
                publish_url,
                auth=auth,
                headers={"Content-Type": "application/xml"},
                data=xml
            )

            if resp.status_code not in (200, 201):
                raise serializers.ValidationError(
                    {"geoserver publish": resp.text}
                )

        return raster_obj
    
class LandInventoryThemeMapSerializer(serializers.ModelSerializer):
    tbl_name = serializers.CharField(read_only=True)

    class Meta:
        model = LandInventoryThemeMap
        fields = "__all__"
    def generate_table_name():
        return f"theme_{uuid.uuid4().hex[:8]}"

    def create(self, validated_data):
        # GeoServer
        GEOSERVER_URL = "http://103.150.191.85:8888/geoserver/rest"
        GEOSERVER_USER = "admin"
        GEOSERVER_PASS = "geoserver"
        WORKSPACE = "vector_valemis"
        POSTGIS_STORE = "postgis_valemis"

        # PostGIS
        DB_NAME = "valemis"
        DB_USER = "valemis"
        DB_PASS = "Valemis@2025"
        DB_HOST = "103.150.191.85"
        DB_PORT = "5432"

        shp_path = validated_data["shp_path"]
        nama_map = validated_data["nama_map"]

        # 1️⃣ AUTO UNIQUE TABLE NAME
        tbl_name = f"theme_{uuid.uuid4().hex[:8]}"
        validated_data["tbl_name"] = tbl_name

        # 2️⃣ SAVE DJANGO MODEL (DAPAT FILE PATH)
        instance = super().create(validated_data)

        # 3️⃣ EXTRACT ZIP
        extract_dir = os.path.join(
            settings.MEDIA_ROOT,
            "tmp",
            tbl_name
        )
        os.makedirs(extract_dir, exist_ok=True)

        with zipfile.ZipFile(instance.shp_path.path, "r") as z:
            z.extractall(extract_dir)

        shp_files = [f for f in os.listdir(extract_dir) if f.endswith(".shp")]
        if not shp_files:
            instance.delete()
            raise serializers.ValidationError("ZIP tidak berisi file .shp")

        shp_path = os.path.join(extract_dir, shp_files[0])

        # 4️⃣ IMPORT KE POSTGIS (ogr2ogr)
        ogr_cmd = [
            "/usr/bin/ogr2ogr",
            "-f", "PostgreSQL",
            f"PG:host={DB_HOST} port={DB_PORT} user={DB_USER} "
            f"dbname={DB_NAME} password={DB_PASS}",
            shp_path,
            "-nln", tbl_name,
            "-nlt", "PROMOTE_TO_MULTI", 
            "-lco", "GEOMETRY_NAME=geom",
            "-lco", "FID=id",
            "-overwrite"
        ]

        ogr = subprocess.run(
            ogr_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        if ogr.returncode != 0:
            instance.delete()
            raise serializers.ValidationError({
                "postgis_import": ogr.stderr.decode()
            })

        # 5️⃣ PUBLISH KE GEOSERVER (POSTGIS DATASTORE)
        publish_url = (
            f"{GEOSERVER_URL}/workspaces/{WORKSPACE}"
            f"/datastores/{POSTGIS_STORE}/featuretypes"
        )

        xml = f"""
        <featureType>
            <name>{tbl_name}</name>
            <title>{nama_map}</title>
            <enabled>true</enabled>
        </featureType>
        """

        resp = requests.post(
            publish_url,
            auth=(GEOSERVER_USER, GEOSERVER_PASS),
            headers={"Content-Type": "application/xml"},
            data=xml
        )

        if resp.status_code not in (200, 201):
            instance.delete()
            raise serializers.ValidationError({
                "geoserver_publish": resp.text
            })

        return instance