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
from .models import LandInventory,Acquisition,LandInventoryThemeMap,Project,LandInventoryDocument,LandInventoryRaster,HistoryAcquisition
from .serializers import LandInventorySerializer,AcquisitionSerializer,ProjectSerializer,LandInventoryDocumentSerializer,LandInventoryRasterSerializer,LandInventoryThemeMapSerializer,HistoryAcquisitionSerializer

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
class LandAcquisitionHistoryViewSet(ModelViewSet):
    queryset = HistoryAcquisition.objects.all()
    serializer_class = HistoryAcquisitionSerializer
    def get_queryset(self):
        queryset = super().get_queryset()

        id_parcel = self.request.query_params.get("id_parcel")

        if id_parcel is not None:
            queryset = queryset.filter(id_parcel=id_parcel)

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
            SELECT ST_AsText(geom) AS wkt_geom FROM \"{table}\"
        """)

        columns = [col[0] for col in cursor.description]
        rows = cursor.fetchall()

    records = []

    for row in rows:
        rec = dict(zip(columns, row))
        geom_wkt = rec.pop("wkt_geom", None)
        rec["geometry"] = wkt.loads(geom_wkt) if geom_wkt else None
        records.append(rec)
    engine = create_engine(db_connection_url)
    gdf = gpd.read_postgis()
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
def validate_tables(cursor, tables):
    cursor.execute("""
        SELECT f_table_name
        FROM geometry_columns
    """)
    valid = {row[0] for row in cursor.fetchall()}
    return [t for t in tables if t in valid]

def analyze_table(cursor, table, wkt_geom):
    sql = f"""
    WITH input AS (
        SELECT ST_SetSRID(ST_GeomFromText(%s), 4326) AS geom
    )
    SELECT
        COUNT(*) AS jumlah_fitur,
        COALESCE(SUM(
            ST_Area(
                ST_Transform(
                    ST_Intersection(t.geom, input.geom),
                    3857
                )
            )
        ), 0) AS luas_m2,
        ST_AsGeoJSON(
            ST_Collect(
                ST_Intersection(t.geom, input.geom)
            )
        ) AS geojson
    FROM "{table}" t, input
    WHERE ST_Intersects(t.geom, input.geom)
    """
    cursor.execute(sql, [wkt_geom])
    return cursor.fetchone()

@csrf_exempt
def api_analyze(request):
    body = json.loads(request.body)
    wkt_geom = body["geometry"]
    tables = body["tables"]

    results = []
    layers = {}

    with connection.cursor() as cursor:
        tables = validate_tables(cursor, tables)

        for table in tables:
            jumlah, luas_m2, geojson = analyze_table(cursor, table, wkt_geom)

            layers[table] = json.loads(geojson) if geojson else None

            results.append({
                "layer": table,
                "jumlah_fitur": jumlah,
                "luas_m2": round(luas_m2, 2),
                "luas_ha": round(luas_m2 / 10000, 4)
            })

    return JsonResponse({
        "input": wkt_geom,
        "layers": layers,
        "stats": results
    })

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
