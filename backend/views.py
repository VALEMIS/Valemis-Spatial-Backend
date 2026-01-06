import os
import json
import tempfile
import zipfile


from .serializers import LandInventoryRasterSerializer
import geopandas as gpd
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import connection
from shapely import wkt
from django.db import transaction, connection
from django.utils.text import slugify
from rest_framework.viewsets import ModelViewSet
from rest_framework.parsers import MultiPartParser, FormParser
from .models import LandInventory,Acquisition,LandInventoryThemeMap,Project,LandInventoryDocument,LandInventoryRaster
from .serializers import LandInventorySerializer,AcquisitionSerializer,ProjectSerializer,LandInventoryDocumentSerializer,LandInventoryRasterSerializer,LandInventoryThemeMapSerializer

class LandInventoryViewSet(ModelViewSet):
    queryset = LandInventory.objects.all()
    serializer_class = LandInventorySerializer
    def get_queryset(self):
        queryset = super().get_queryset()

        id_project = self.request.query_params.get("id_project")

        if id_project is not None:
            queryset = queryset.filter(id_project=id_project)

        return queryset
class LandAcquisitionViewSet(ModelViewSet):
    queryset = Acquisition.objects.all()
    serializer_class = AcquisitionSerializer
    def get_queryset(self):
        queryset = super().get_queryset()

        id_project = self.request.query_params.get("id_project")

        if id_project is not None:
            queryset = queryset.filter(id_project=id_project)

        return queryset

class ProjectViewSet(ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
class LandInventoryDocumentViewSet(ModelViewSet):
    queryset = LandInventoryDocument.objects.all()
    serializer_class = LandInventoryDocumentSerializer
    parser_classes = [MultiPartParser, FormParser]

class LandInventoryRasterViewSet(ModelViewSet):
    queryset = LandInventoryRaster.objects.all().order_by("-id_raster")
    serializer_class = LandInventoryRasterSerializer
    parser_classes = [MultiPartParser, FormParser]
    def get_queryset(self):
        queryset = super().get_queryset()

        id_project = self.request.query_params.get("id_project")

        if id_project is not None:
            queryset = queryset.filter(id_project=id_project)

        return queryset
class LandInventoryThemeMapViewSet(ModelViewSet):
    queryset = LandInventoryThemeMap.objects.all()
    serializer_class = LandInventoryThemeMapSerializer
    parser_classes = [MultiPartParser, FormParser]
    def get_queryset(self):
        queryset = super().get_queryset()

        id_project = self.request.query_params.get("id_project")

        if id_project is not None:
            queryset = queryset.filter(id_project=id_project)

        return queryset


def ProcessThemeMap(request):
    uploaded_file = request.FILE.get("uploaded File")


def load_layer_from_db(table):
    with connection.cursor() as cursor:
        # print(cursor)
        cursor.execute(f"""
            SELECT geom.geometry.STAsText() AS wkt_geom FROM \"{table}\"
        """)

        columns = [col[0] for col in cursor.description]
        rows = cursor.fetchall()

    records = []

    for row in rows:
        rec = dict(zip(columns, row))
        geom_wkt = rec.pop("wkt_geom", None)
        rec["geometry"] = wkt.loads(geom_wkt) if geom_wkt else None
        records.append(rec)

    gdf = gpd.GeoDataFrame(records, geometry="geometry", crs="EPSG:4326")
    # print(records)
    return gdf

# ==============================
# Helper: parse uploaded file
# ==============================
def read_uploaded_file(uploaded_file, tmpdir):
    upload_path = os.path.join(tmpdir, uploaded_file.name)

    with open(upload_path, "wb+") as f:
        for chunk in uploaded_file.chunks():
            f.write(chunk)

    if zipfile.is_zipfile(upload_path):
        with zipfile.ZipFile(upload_path, "r") as z:
            z.extractall(tmpdir)

        for f in os.listdir(tmpdir):
            if f.lower().endswith((".shp", ".geojson", ".json", ".kml", ".gpkg")):
                return os.path.join(tmpdir, f)
    else:
        return upload_path

    return None

# ==============================
# MAIN API
# ==============================
@csrf_exempt
def api_analyze(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST supported"}, status=405)

    try:
        body = json.loads(request.body.decode("utf-8"))

        wkt_geom = body.get("geometry")
        table_list = body.get("tables", [])

        if not wkt_geom:
            return JsonResponse({"error": "geometry (WKT) required"}, status=400)

        if not isinstance(table_list, list) or not table_list:
            return JsonResponse({"error": "tables must be non-empty array"}, status=400)

        # ==============================
        # INPUT GEOMETRY (WKT → GDF)
        # ==============================
        geom = wkt.loads(wkt_geom)

        gdf_input = gpd.GeoDataFrame(
            [{"id": 1}],
            geometry=[geom],
            crs="EPSG:4326"
        )

        results = []
        geojson_layers = {}

        # ==============================
        # PROCESS EACH TABLE
        # ==============================
        for table in table_list:
            gdf_layer = load_layer_from_db(table)

            if gdf_layer.empty:
                geojson_layers[table] = None
                results.append({
                    "layer": table,
                    "jumlah_fitur": 0,
                    "luas_m2": 0,
                    "luas_ha": 0
                })
                continue

            # pastikan layer CRS 4326
            gdf_layer = gdf_layer.to_crs("EPSG:4326")

            # overlay di 4326
            clipped = gpd.overlay(gdf_layer, gdf_input, how="intersection")

            if clipped.empty:
                geojson_layers[table] = None
                area_m2 = 0
            else:
                # ==============================
                # AREA CALCULATION → 3857
                # ==============================
                clipped_3857 = clipped.to_crs("EPSG:3857")
                area_m2 = clipped_3857.geometry.area.sum()

                geojson_layers[table] = json.loads(
                    clipped.to_json()
                )

            results.append({
                "layer": table,
                "jumlah_fitur": len(clipped),
                "luas_m2": round(area_m2, 2),
                "luas_ha": round(area_m2 / 10000, 4)
            })

        # ==============================
        # INPUT GEOJSON
        # ==============================
        input_geojson = json.loads(gdf_input.to_json())

        return JsonResponse({
            "input": input_geojson,
            "layers": geojson_layers,
            "stats": results
        }, safe=False)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
def ProcessThemeMap(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    uploaded_file = request.FILES.get("uploaded_file")
    nama_map = request.POST.get("nama_map")

    if not uploaded_file or not nama_map:
        return JsonResponse(
            {"error": "uploaded_file dan nama_map wajib"},
            status=400
        )

    # ===============================
    # TRANSACTION = AMAN DARI GAGAL TENGAH JALAN
    # ===============================
    with transaction.atomic():
        # 1️⃣ Buat metadata dulu → dapat UUID
        theme = LandInventoryThemeMap.objects.create(
            nama_map=nama_map,
            tbl_name=""  # diisi setelah table sukses dibuat
        )

        # 2️⃣ Nama table UNIK (UUID based)
        table_name = f"theme_{theme.uuid.hex}"

        # 3️⃣ Temp dir untuk file
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, uploaded_file.name)

            with open(file_path, "wb+") as f:
                for chunk in uploaded_file.chunks():
                    f.write(chunk)

            # ===============================
            # HANDLE ZIP (SHAPEFILE)
            # ===============================
            if uploaded_file.name.lower().endswith(".zip"):
                with zipfile.ZipFile(file_path, "r") as zip_ref:
                    zip_ref.extractall(tmpdir)

                shp_files = [
                    os.path.join(tmpdir, f)
                    for f in os.listdir(tmpdir)
                    if f.lower().endswith(".shp")
                ]

                if not shp_files:
                    raise ValueError("ZIP tidak mengandung file .shp")

                data_path = shp_files[0]

            # ===============================
            # NON ZIP (GeoJSON, KML, dll)
            # ===============================
            else:
                data_path = file_path

            # ===============================
            # READ GEODATA
            # ===============================
            try:
                gdf = gpd.read_file(data_path)
            except Exception as e:
                raise ValueError(f"Gagal membaca data spasial: {str(e)}")

            if gdf.empty:
                raise ValueError("Data kosong")

            # ===============================
            # WRITE KE POSTGIS
            # ===============================
            gdf.to_postgis(
                name=table_name,
                con=connection,
                if_exists="fail",   # PENTING: cegah overwrite
                index=False
            )

        # 4️⃣ Simpan nama table (FINAL)
        theme.tbl_name = table_name
        theme.save(update_fields=["tbl_name"])

    # ===============================
    # RESPONSE
    # ===============================
    return JsonResponse({
        "message": "Theme map berhasil diupload",
        "id_theme_map": theme.id_theme_map,
        "uuid": str(theme.uuid),
        "table_name": theme.tbl_name,
        "feature_count": len(gdf)
    }, status=201)
