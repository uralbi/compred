from django.db import models

class DictionaryEntry(models.Model):
    kyrgyz_word = models.CharField(max_length=110, unique=True)
    russian_translation = models.CharField(max_length=120, db_index=True)
    part_of_speech = models.CharField(max_length=50, blank=True)
    example_sentence_ky = models.TextField(blank=True)
    example_sentence_ru = models.TextField(blank=True)
    pronunciation = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.kyrgyz_word

