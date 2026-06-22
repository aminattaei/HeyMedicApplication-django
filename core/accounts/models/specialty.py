from django.db import models
from .users import User
from django.utils.text import slugify


class Specialty(models.Model):
    title = models.CharField(max_length=100, verbose_name="عنوان تخصص")
    slug = models.SlugField(unique=True, blank=True, verbose_name="متن جایگزین",help_text="If you don't enter anything in this field, it will automatically fill it in.")


    class Meta:
        ordering = ['title']
        verbose_name = "specialty"
        verbose_name_plural = "specialties"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title