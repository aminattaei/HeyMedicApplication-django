# signals.py
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils.text import slugify
from googletrans import Translator
from .models import Specialty

@receiver(pre_save, sender=Specialty)
def create_english_slug(sender, instance, **kwargs):
    """
    This function before saving instance of Specialty model get  its title and translate it to english
    """
    if not instance.slug:  
        translator = Translator()
        try:
            
            translated_title = translator.translate(instance.title, dest='en').text
            
            base_slug = slugify(translated_title)
            
            slug = base_slug
            counter = 1
            while Specialty.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            instance.slug = slug
        except Exception as e:
            instance.slug = slugify(instance.title)