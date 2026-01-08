from django.contrib.gis.db import models

class geometry(models.Field):
    def db_type(self, connection):
        return "geometry"

class Project(models.Model):
    id_project = models.AutoField(primary_key=True)
    nama_project = models.TextField()
    owner_project = models.TextField()
    tanggal_dibuat = models.DateField(auto_now_add=True)
    basemap = models.TextField(null=True,blank=True)
    iupk = models.TextField(null=True,blank=True)
    batas_admin = models.TextField(null=True,blank=True)
    date_start = models.DateField()
    date_end = models.DateField()
    geom = models.GeometryField(srid=4326,null=True,blank=True)
    class Meta:
        db_table = 'tbl_project'
        verbose_name = 'Project'
        verbose_name_plural = 'Projects'
    def __str__(self):
        return self.nama_project
    
class ProjectDetail(models.Model):
    id_project_detail = models.AutoField(primary_key=True)
    id_project = models.ForeignKey(Project,on_delete=models.PROTECT,related_name="project_details")
    nama_site = models.TextField(null=True,default="Site")
    geom = models.GeometryField(srid=4326)
    class Meta:
        db_table = "tbl_project_detail"

class AcquisitionAsset(models.Model):
    id_parcel_asset = models.AutoField(primary_key=True)
    id_asset = models.TextField(null=True,blank=True)
    class Meta:
        db_table = 'tbl_acquisition_asset'
        verbose_name = 'Acquisition_asset'
        verbose_name_plural = 'Acquisition_assets'
class Acquisition(models.Model):
    # id_
    id_parcel = models.AutoField(primary_key=True)
    id_project = models.ForeignKey(Project,on_delete=models.CASCADE,related_name="ProjectAcquisition",null=True,blank=True)
    kode_parcel = models.TextField(null=True,blank=True)
    nama_pemilik = models.TextField(null=True,blank=True)
    desa = models.TextField(null=True,blank=True)
    luas = models.FloatField(null=True,blank=True,default=0)
    status = models.TextField(null=True,blank=True)
    jumlah_bebas = models.IntegerField(null=True,blank=True,default=0)
    biaya_pembebasan = models.IntegerField(null=True,blank=True,default=0)
    tanggal_negosiasi = models.DateField(null=True,blank=True)
    NIB_Baru = models.CharField(max_length=15,null=True,blank=True)
    id_asset = models.ForeignKey(AcquisitionAsset,on_delete=models.CASCADE,related_name="Acquisition_asset",null=True,blank=True)
    geom = models.GeometryField(srid=4326,null=True,blank=True)
    # id_persil = models.ForeignKey(
    #     PolygonPersil,
    #     on_delete=models.PROTECT,
    #     related_name='acquisition',
    #     null=True,
    #     blank=True
    # )

    class Meta:
        db_table = 'tbl_acquisition'
        verbose_name = 'Acquisition'
        verbose_name_plural = 'Acquisition'

    def __str__(self):
        return self.kode_parcel

class HistoryAcquisition(models.Model):
    id_history = models.AutoField(primary_key=True)
    id_parcel = models.ForeignKey(
        Acquisition,
        on_delete=models.CASCADE,
        related_name="histories",
        null=True,
        blank=True
    )
    status = models.TextField()
    deskripsi = models.TextField()
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tbl_history_acquisition'
        verbose_name = 'History_acquisition'
        verbose_name_plural = 'History_acquisitions'

    def __str__(self):
        return self.status
    
class LandStatus(models.Model):
    code = models.PositiveSmallIntegerField(unique=True)
    label = models.CharField(max_length=30)
    class Meta:
        db_table = 'ref_land_invetory_status'
        verbose_name = 'Ref_land_invetory_status'
        verbose_name_plural = 'Ref_land_invetory_status'

    def __str__(self):
        return self.label


class LandKategori(models.Model):
    code = models.PositiveSmallIntegerField(unique=True)
    label = models.CharField(max_length=30)
    class Meta:
        db_table = 'ref_land_inventory_category'
        verbose_name = 'land_inventory_categories'
        verbose_name_plural = 'land_inventory_categories'

    def __str__(self):
        return self.label
      
class LandInventory(models.Model):
    id_lahan = models.AutoField(primary_key=True)
    id_project = models.ForeignKey(Project,on_delete=models.CASCADE,related_name="ProjectInventory",null=True,blank=True)
    kode_lahan = models.CharField(max_length=50,null=True,blank=True)
    nama_lokasi = models.TextField(null=True,blank=True)
    kategori =  models.ForeignKey(
        LandKategori,
        on_delete=models.PROTECT,
        related_name='kateogri',
        default=1
    )
    status =  models.ForeignKey(
        LandStatus,
        on_delete=models.PROTECT,
        related_name='status',
        default=1
    )
    no_sertif = models.TextField(null=True,blank=True)
    geom = models.GeometryField(srid=4326,null=True,blank=True)
    
    class Meta:
        db_table = 'tbl_land_inventory'
        verbose_name = 'LandInventory'
        verbose_name_plural = 'LandInventories'
    # dokumen = models.ForeignKey(LandInventoryDocument,on_delete=models.P)


class LandInventoryDocument(models.Model):
    id_document = models.AutoField(primary_key=True)
    id_lahan = models.ForeignKey(
        LandInventory,
        on_delete=models.CASCADE,
        related_name='documents'
    )
    nama_dokumen = models.TextField()
    file = models.FileField(upload_to="landInventoryDocument")

    class Meta:
        db_table = 'tbl_land_inventory_document'
        verbose_name = 'Land Inventory Document'
        verbose_name_plural = 'Land Inventory Documents'


# UPlOAD DATA LAND INVENTORY

class LandInventoryThemeMap(models.Model):
    # class TipePeta(modes.Intege)
    id_theme_map = models.AutoField(primary_key=True)
    id_project = models.ForeignKey(Project,on_delete=models.CASCADE,related_name="ProjectThemeMap",null=True,blank=True)
    nama_map = models.TextField()
    tbl_name = models.TextField(unique=True, editable=False)
    shp_path = models.FileField(upload_to="themeMap")
    type = models.TextField()
    style = models.TextField(null=True,blank=True)
    class Meta:
        db_table = 'tbl_land_inventory_theme_map'
        verbose_name = 'Land Inventory Theme Map'
        verbose_name_plural = 'Land Inventory Theme Maps'
class LandInventoryRaster(models.Model):
    id_raster = models.AutoField(primary_key=True)
    id_project = models.ForeignKey(Project,on_delete=models.CASCADE,related_name="ProjectRaster",null=True,blank=True)
    store_name = models.TextField()
    nama = models.TextField()
    raster_path = models.FileField(upload_to="raster/")
    class Meta:
        db_table = 'tbl_land_inventory_raster'
        verbose_name = 'Land Inventory Raster'
        verbose_name_plural = 'Land Inventory Ras`ters'

# INSERT REF DATA
# LandKategori.objects.bulk_create([
#     LandKategori(code=0, label='Vale Owned'),
#     LandKategori(code=1, label='Acquired'),
#     LandKategori(code=2, label='IUPK'),
#     LandKategori(code=3, label='PPKH'),
#     LandKategori(code=4, label='Operational'),
# ])  


# LandStatus.objects.bulk_create([
#     LandStatus(code=0, label='HGU'),
#     LandStatus(code=1, label='SHM'),
#     LandStatus(code=2, label='SHGB'),
# ])    