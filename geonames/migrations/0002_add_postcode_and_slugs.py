import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('geonames', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Postcode',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('postal_code', models.CharField(db_index=True, max_length=20)),
                ('place_name', models.CharField(max_length=180)),
                ('admin_name1', models.CharField(blank=True, max_length=100, null=True, verbose_name='state')),
                ('admin_code1', models.CharField(blank=True, max_length=20, null=True, verbose_name='state')),
                ('admin_name2', models.CharField(blank=True, max_length=100, null=True, verbose_name='county/province')),
                ('admin_code2', models.CharField(blank=True, max_length=20, null=True, verbose_name='county/province')),
                ('admin_name3', models.CharField(blank=True, max_length=100, null=True, verbose_name='community')),
                ('admin_code3', models.CharField(blank=True, max_length=20, null=True, verbose_name='community')),
                ('lat', models.DecimalField(max_digits=9, decimal_places=6, null=True)),
                ('lon', models.DecimalField(max_digits=9, decimal_places=6, null=True)),
                # ('point', django.contrib.gis.db.models.fields.PointField(srid=4326)),
                ('accuracy', models.IntegerField(blank=True, null=True)),
                ('country', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='postcode_set', to='geonames.Country')),
            ],
        ),
        migrations.AddField(
            model_name='admin2code',
            name='slug',
            field=models.CharField(blank=True, db_index=True, max_length=35, null=True),
        ),
        migrations.AddField(
            model_name='locality',
            name='slug',
            field=models.CharField(blank=True, db_index=True, max_length=35, null=True),
        ),
    ]
