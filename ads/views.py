from django.shortcuts import render
from rest_framework import viewsets
from .models import DictionaryEntry
from .srzs import DictionaryEntrySerializer
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

class DictionaryEntryViewSet(viewsets.ModelViewSet):
    queryset = DictionaryEntry.objects.all()
    serializer_class = DictionaryEntrySerializer


@api_view(['GET'])
def search_by_kyrgyz_word(request):
    kyrgyz_word = request.GET.get('word', None)
    if kyrgyz_word is not None:
        entries = DictionaryEntry.objects.filter(kyrgyz_word__icontains=kyrgyz_word)[:20]
        if entries.exists():
            serializer = DictionaryEntrySerializer(entries, many=True)
            return Response(serializer.data)
        else:
            return Response({'message': 'No matching entries found.'}, status=status.HTTP_404_NOT_FOUND)
    return Response({'message': 'Kyrgyz word parameter is missing.'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def search_by_russian_word(request):
    rus_word = request.GET.get('word', None)
    if rus_word is not None:
        entries = DictionaryEntry.objects.filter(russian_translation__icontains=rus_word)[:20]
        if entries.exists():
            serializer = DictionaryEntrySerializer(entries, many=True)
            return Response(serializer.data)
        else:
            return Response({'message': 'No matching entries found.'}, status=status.HTTP_404_NOT_FOUND)
    return Response({'message': 'Kyrgyz word parameter is missing.'}, status=status.HTTP_400_BAD_REQUEST)