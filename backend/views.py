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
    geom_col = "ogr_geometry"
    # print(table )
    with connection.cursor() as cursor:
        # print(cursor)
        cursor.execute(f"""
            SELECT ogr_geometry.STAsText() AS wkt_geom FROM \"{table}\"
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
        uploaded_file = request.FILES.get("file")
        layer_list = request.FILE.get("layer_list")
        if not uploaded_file:
            return JsonResponse({"error": "No file uploaded"}, status=400)

        # Save & read input file
        with tempfile.TemporaryDirectory() as tmpdir:
            spatial_path = read_uploaded_file(uploaded_file, tmpdir)

            if not spatial_path:
                return JsonResponse({"error": "Unsupported spatial file"}, status=400)

            gdf_input = gpd.read_file(spatial_path)

        # CRS standardization
        gdf_input = gdf_input.to_crs("EPSG:3857")

        # ==============================
        # Load layers from DB
        # ==============================
        layers = {
            "APL": load_layer_from_db("apl"),
            "HGB": load_layer_from_db("hgb"),
            "IPPKH": load_layer_from_db("ippkh"),
            "IUPK": load_layer_from_db("iupk"),
            "KKPR": load_layer_from_db("kkpr"),
            "Kawasan Hutan": load_layer_from_db("kawasan hutan"),
            "Lahan Bebas": load_layer_from_db("lahan_bebas"),
        }

        results = []
        geojson_layers = {}

        # ==============================
        # Spatial intersect
        # ==============================
        for name, gdf in layers.items():
            gdf = gdf.to_crs("EPSG:32751")

            clipped = gpd.overlay(gdf, gdf_input, how="intersection")

            if clipped.empty:
                area_m2 = 0
                geojson_layers[name] = None
            else:
                clipped["area_m2"] = clipped.geometry.area
                area_m2 = clipped["area_m2"].sum()

                geojson_layers[name] = json.loads(
                    clipped.to_crs("EPSG:4326").to_json()
                )

            results.append({
                "layer": name,
                "jumlah_fitur": len(clipped),
                "luas_m2": round(area_m2, 2),
                "luas_ha": round(area_m2 / 10000, 4)
            })

        # Input outline (user uploaded geometry)
        input_geojson = json.loads(gdf_input.to_crs("EPSG:4326").to_json())

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
