from apps.users.models import User
from apps.weather.models import WeatherData
from django.db import models
from django.utils import timezone


class Diary(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    weather_data = models.ForeignKey(WeatherData, on_delete=models.CASCADE)
    satisfaction = models.IntegerField()
    title = models.CharField(max_length=255)
    notes = models.TextField()
    image_url = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'diary'
        verbose_name = 'Diary'
        verbose_name_plural = 'Diaries'

    def __str__(self):
        return str(self.date)

    def delete(self, using=None, keep_parents=False):
        self.deleted_at = timezone.now()
        self.save()
