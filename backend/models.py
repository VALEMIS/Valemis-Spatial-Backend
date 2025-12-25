from django.contrib.gis.db import models


# Create your models here.
class LandAcquisitionProject(models.Model):
    id_project = models.AutoField(primary_key=True)
    nama_project = models.TextField(null=False)
    owner_project = models.TextField()
    tanggal_dibuat = models.DateField()
    class meta:
        db_table = 'tbl_land_acquisition_project'
        verbose_name = 'Land Acquisition Project'
        verbose_name_plural = 'Land Acquisition Projects'
class Acquisition(models.Model):
    id_parcel = models.AutoField(primary_key=True)
    id_project = models.ForeignKey(LandAcquisitionProject,on_delete=models.CASCADE,related_name="AcquisitonProject",null=True,blank=True)
    kode_parcel = models.TextField()
    nama_pemilik = models.TextField()
    desa = models.TextField()
    luas = models.FloatField()
    status = models.TextField()
    jumlah_bebas = models.FloatField()
    biaya_pembebasan = models.IntegerField()
    tanggal_negosiasi = models.DateField()
    geom = models.PolygonField(srid=4326)

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
        related_name="histories"
    )
    status = models.TextField()
    deskripsi = models.TextField()

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
    kode_lahan = models.CharField(max_length=50)
    nama_lokasi = models.TextField()
    kategori =  models.ForeignKey(
        LandKategori,
        on_delete=models.PROTECT,
        related_name='kateogri'
    )
    status =  models.ForeignKey(
        LandStatus,
        on_delete=models.PROTECT,
        related_name='status'
    )
    no_sertif = models.TextField()
    geom = models.PointField()
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
    file = models.FileField(upload_to="landInventoryDocument")

    class Meta:
        db_table = 'ref_land_inventory_document'
        verbose_name = 'Land Inventory Document'
        verbose_name_plural = 'Land Inventory Documents'




# UPlOAD DATA LAND INVENTORY

class LandInventoryThemeMap(models.Model):
    id_theme_map = models.AutoField(primary_key=True)
    # uuid = models.
    nama_map = models.TextField()
    tbl_name = models.TextField()
    class Meta:
        db_table = 'tbl_land_inventory_theme_map'
        verbose_name = 'Land Inventory Theme Map'
        verbose_name_plural = 'Land Inventory Theme Maps'

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