class Specialty(models.Model):
    title = models.CharField(max_length=100, verbose_name="عنوان تخصص")
    slug = models.SlugField(unique=True, blank=True, verbose_name="متن جایگزین")


    class Meta:
        ordering = ['title']
        verbose_name = "تخصص"
        verbose_name_plural = "تخصص‌ها"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title