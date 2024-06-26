# Generated by Django 4.2.1 on 2023-06-02 16:45

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AuthInfo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('location_id', models.CharField(max_length=300)),
                ('access_token', models.TextField(max_length=500)),
                ('refresh_token', models.TextField(max_length=500)),
                ('expires_in', models.PositiveIntegerField()),
            ],
        ),
    ]
