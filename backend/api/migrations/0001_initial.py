# Generated by Django 5.1.3 on 2025-02-23 02:13

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Studio',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('address', models.TextField()),
                ('is_24h', models.BooleanField(default=False, help_text='24時間営業の場合はTrue')),
                ('opening_time', models.TimeField(blank=True, help_text='開店時間（24時間営業の場合は空）', null=True)),
                ('closing_time', models.TimeField(blank=True, help_text='閉店時間（24時間営業の場合は空）', null=True)),
                ('closes_next_day', models.BooleanField(default=False, help_text='閉店時間が翌日の場合はTrue')),
                ('reservation_url', models.URLField()),
                ('self_practice_reservation_start_date', models.PositiveIntegerField(blank=True, help_text='個人練習の予約開始可能までの日数（例：7日前）', null=True)),
                ('self_practice_reservation_start_time', models.TimeField(blank=True, help_text='個人練習の予約開始時間', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='Todo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100)),
                ('completed', models.BooleanField(default=False)),
                ('attachment', models.FileField(blank=True, null=True, upload_to='uploads/')),
            ],
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_id', models.IntegerField(unique=True)),
                ('name', models.CharField(max_length=100)),
                ('password', models.CharField(max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='FavoriteStudio',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('studio', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='favorited_by', to='api.studio')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='favorite_studios', to='api.user')),
            ],
            options={
                'unique_together': {('user', 'studio')},
            },
        ),
    ]
