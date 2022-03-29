from django.core.management.base import BaseCommand
from django.db import connection

from blocl.utils import spoonfeed
from geonames.models import Locality, Admin2Code


def admin2_save(o):
    o.save(update_localities_longname=False, update_handle=True)
    print(o.name.ljust(50), o.slug)


def loc_save(o):
    o.save(check_duplicated_longname=False, update_handle=True)
    print(o.name.ljust(40), o.slug)


def spaceless_gb_postcodes():
    q = "UPDATE geonames_postcode SET postal_code = REPLACE(postal_code, ' ', '') "\
        "WHERE country_id='GB';"
    cursor = connection.cursor()
    cursor.execute(q)


class Command(BaseCommand):
    def handle(self, *args, **options):
        print('GENERATING ADMIN2 HANDLES...')
        spoonfeed(Admin2Code.objects.all(), admin2_save)
        print('GENERATING LOCALITY HANDLES...')
        spoonfeed(Locality.objects.all(), loc_save)
        print('NORMALISING GB POSTCODES')
        spaceless_gb_postcodes()
