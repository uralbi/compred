# serializers.py in your dictionary app directory

from rest_framework import serializers
from .models import DictionaryEntry

class DictionaryEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = DictionaryEntry
        fields = ['id', 'kyrgyz_word', 'russian_translation', 'part_of_speech', 'example_sentence_ky', 'example_sentence_ru', 'pronunciation']
