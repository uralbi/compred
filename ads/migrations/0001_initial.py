# Generated by Django 4.2 on 2024-02-12 11:48

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='DictionaryEntry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('kyrgyz_word', models.CharField(max_length=110, unique=True)),
                ('russian_translation', models.CharField(max_length=120)),
                ('part_of_speech', models.CharField(blank=True, max_length=50)),
                ('example_sentence_ky', models.TextField(blank=True)),
                ('example_sentence_ru', models.TextField(blank=True)),
                ('pronunciation', models.CharField(blank=True, max_length=100)),
            ],
        ),
    ]