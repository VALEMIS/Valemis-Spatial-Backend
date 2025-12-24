from django.contrib.gis.db import models


# Create your models here.


class Acquisition(models.Model):
    id_parcel = models.AutoField(primary_key=True)
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
    