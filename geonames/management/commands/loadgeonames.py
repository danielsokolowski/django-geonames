from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count
from django.conf import settings
import traceback
from geonames.models import Timezone, Language, Country, Currency, Locality, \
    Admin1Code, Admin2Code, AlternateName, GeonamesUpdate, Postcode
import datetime
import os
import sys
import tempfile
import shutil
import glob


FILES = [
    'http://download.geonames.org/export/dump/timeZones.txt',
    'http://download.geonames.org/export/dump/iso-languagecodes.txt',
    'http://download.geonames.org/export/dump/countryInfo.txt',
    'http://download.geonames.org/export/dump/admin1CodesASCII.txt',
    'http://download.geonames.org/export/dump/admin2Codes.txt',
    'http://download.geonames.org/export/dump/cities500.zip',
    'http://download.geonames.org/export/dump/alternateNames.zip',
    # postcodes
    'https://download.geonames.org/export/zip/allCountries.zip',
    'https://download.geonames.org/export/zip/GB_full.csv.zip',
]

# See http://www.geonames.org/export/codes.html
city_types = ['PPL', 'PPLA', 'PPLC', 'PPLA2', 'PPLA3', 'PPLA4', 'PPLG']
geo_models = [Timezone, Language, Country, Currency,
              Admin1Code, Admin2Code, Locality, AlternateName, Postcode]


class Command(BaseCommand):
    help = "Geonames import command."
    if settings.DEBUG:
        download_dir = os.path.join(os.getcwd(), 'downloads')
    else:
        download_dir = os.path.join(tempfile.gettempdir(), 'django-geonames-downloads')


    countries = {}
    localities = set()

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Delete data first and redownload',
        )

    def handle(self, *args, **options):
        start_time = datetime.datetime.now()

        if options['force']:
            self.load(clear=True)
        else:
            self.load()
        print('\nCompleted in {}'.format(datetime.datetime.now() - start_time))

    @transaction.atomic
    def load(self, clear=False):
        if clear:
            # self.cleanup_files()

            print("Deleting data")
            for member in geo_models:
                print(f" - {member._meta.verbose_name}")
                member.objects.all().delete()

        for member in geo_models:
            if member.objects.all().count() is not 0:
                print(f'ERROR: there are {member._meta.verbose_name_plural} in the database')
                sys.exit(1)

        self.download_files()
        self.unzip_files()
        self.load_timezones()
        self.load_languagecodes()
        self.load_countries()
        self.load_postcodes()
        self.load_postcodes('GB_full.txt')
        self.load_admin1()
        self.load_admin2()
        self.load_localities()
        self.cleanup()
        self.load_altnames()
        self.check_errors()

        # Save the time when the load happened
        GeonamesUpdate.objects.create()

    def download_files(self):
        # make the temp folder if it dosen't exist
        try:
            os.mkdir(self.download_dir)
        except OSError:
            pass
        os.chdir(self.download_dir)
        print()
        print(f'Downloading files to {self.download_dir}')
        print()
        for f in FILES:
            # --timestamping (-N) will overwrite files rather then appending .1, .2 ...
            # see http://stackoverflow.com/a/16840827/913223
            if os.system('wget --timestamping %s' % f) != 0:
                print(f"ERROR fetching {os.path.basename(f)}. Perhaps you are missing the 'wget' utility.")
                sys.exit(1)

    def unzip_files(self):
        os.chdir(self.download_dir)
        print("Unzipping downloaded files as needed: ''." % glob.glob('*.zip'))
        for f in glob.glob('*.zip'):
            if os.system('unzip -o %s' % f) != 0:
                print(f"ERROR unzipping {f}. Perhaps you are missing the 'unzip' utility.")
                sys.exit(1)

    def cleanup_files(self):
        try:
            print('Deleting files')
            shutil.rmtree(self.download_dir)
        except FileNotFoundError:
            print('Files not present')
            pass

    def load_timezones(self):
        print('Loading Timezones')
        objects = []
        os.chdir(self.download_dir)
        with open('timeZones.txt', 'r', encoding="utf8") as fd:
            try:
                fd.readline()
                for line in fd:
                    fields = [field.strip() for field in line[:-1].split('\t')]
                    name, gmt_offset, dst_offset = fields[1:4]
                    objects.append(Timezone(name=name, gmt_offset=gmt_offset, dst_offset=dst_offset))
            except Exception as inst:
                traceback.print_exc(inst)
                raise Exception(f"ERROR parsing:\n {line}\n The error was: {inst}")

        Timezone.objects.bulk_create(objects)
        print('{0:8d} Timezones loaded'.format(Timezone.objects.all().count()))

    def load_languagecodes(self):
        print('Loading Languages')
        objects = []
        os.chdir(self.download_dir)
        with open('iso-languagecodes.txt', 'r', encoding="utf8") as fd:
            try:
                fd.readline()  # skip the head
                for line in fd:
                    fields = [field.strip() for field in line.split('\t')]
                    iso_639_1, name = fields[2:4]
                    if iso_639_1 != '':
                        objects.append(Language(iso_639_1=iso_639_1,
                                                name=name))
            except Exception as inst:
                traceback.print_exc(inst)
                raise Exception(f"ERROR parsing:\n {line}\n The error was: {inst}")

        Language.objects.bulk_create(objects)
        print('{0:8d} Languages loaded'.format(Timezone.objects.all().count()))
        self.fix_languagecodes()

    def fix_languagecodes(self):
        print('Fixing Language codes')
        corrections = {
            'km': 'Khmer',
            'ia': 'Interlingua',
            'ms': 'Malay',
            'el': 'Greek',
            'se': 'Sami',
            'oc': 'Occitan',
            'st': 'Sotho',
            'sw': 'Swahili',
            'to': 'Tonga',
            'fy': 'Frisian',
        }
        for iso_code, name in corrections.items():
            Language.objects.filter(iso_639_1=iso_code).update(name=name)

    def load_countries(self):
        print('Loading Countries')
        objects = []
        langs_dic = {}
        dollar = Currency.objects.create(code='USD', name='Dollar')
        os.chdir(self.download_dir)
        with open('countryInfo.txt', encoding="utf8") as fd:
            try:
                for line in fd:
                    if line[0] == '#':
                        continue

                    fields = [field.strip() for field in line[:-1].split('\t')]
                    code = fields[0]
                    self.countries[code] = {}
                    name = fields[4]
                    currency_code = fields[10]
                    currency_name = fields[11]
                    langs_dic[code] = fields[15]
                    if currency_code == '':
                        currency = dollar
                    else:
                        currency, created = Currency.objects.get_or_create(
                                code=currency_code, defaults={'name': currency_name})

                    objects.append(Country(code=code,
                                           name=name,
                                           currency=currency))
            except Exception as inst:
                traceback.print_exc(inst)
                raise Exception(f"ERROR parsing:\n {line}\n The error was: {inst}")

        Country.objects.bulk_create(objects)
        print('{0:8d} Countries loaded'.format(Country.objects.all().count()))

        print('Adding Languages to Countries')
        default_lang = Language.objects.get(iso_639_1='en')
        for country in Country.objects.all():
            for code in langs_dic[country.code].split(','):
                iso_639_1 = code.split("-")[0]
                if len(iso_639_1) < 2:
                    continue

                languages = Language.objects.filter(iso_639_1=iso_639_1)
                if languages.count() == 1:
                    country.languages.add(languages[0])

            if country.languages.count() == 0:
                country.languages.add(default_lang)

    def load_admin1(self):
        print('Loading Admin1Codes')
        objects = []
        os.chdir(self.download_dir)
        with open('admin1CodesASCII.txt', encoding="utf8") as fd:
            try:
                for line in fd:
                    fields = [field.strip() for field in line[:-1].split('\t')]
                    codes, name = fields[0:2]
                    country_code, admin1_code = codes.split('.')
                    geonameid = fields[3]
                    self.countries[country_code][admin1_code] = {'geonameid': geonameid, 'admins2': {}}
                    objects.append(Admin1Code(geonameid=geonameid,
                                              code=admin1_code,
                                              name=name,
                                              country_id=country_code))
            except Exception as inst:
                traceback.print_exc(inst)
                raise Exception(f"ERROR parsing:\n {line}\n The error was: {inst}")

        Admin1Code.objects.bulk_create(objects)
        print('{0:8d} Admin1Codes loaded'.format(Admin1Code.objects.all().count()))

    def load_admin2(self):
        print('Loading Admin2Codes')
        objects = []
        admin2_list = []  # to find duplicated
        skipped_duplicated = 0
        os.chdir(self.download_dir)
        with open('admin2Codes.txt', encoding="utf8") as fd:
            try:
                for line in fd:
                    fields = [field.strip() for field in line[:-1].split('\t')]
                    codes, name = fields[0:2]
                    country_code, admin1_code, admin2_code = codes.split('.')

                    # if there is a duplicated
                    long_code = f"{country_code}.{admin1_code}.{name}"
                    if long_code in admin2_list:
                        skipped_duplicated += 1
                        continue

                    admin2_list.append(long_code)

                    geonameid = fields[3]
                    admin1_dic = self.countries[country_code].get(admin1_code)

                    # if there is not admin1 level we save it but we don't keep it for the localities
                    if admin1_dic is None:
                        admin1_id = None
                    else:
                        # If not, we get the id of admin1 and we save geonameid for filling in Localities later
                        admin1_id = admin1_dic['geonameid']
                        admin1_dic['admins2'][admin2_code] = geonameid

                    name = name  # unicode(name, 'utf-8')
                    objects.append(Admin2Code(geonameid=geonameid,
                                              code=admin2_code,
                                              name=name,
                                              country_id=country_code,
                                              admin1_id=admin1_id))
            except Exception as inst:
                traceback.print_exc(inst)
                raise Exception(f"ERROR parsing:\n {line}\n The error was: {inst}")

        Admin2Code.objects.bulk_create(objects, ignore_conflicts=True)
        print('{0:8d} Admin2Codes loaded'.format(Admin2Code.objects.all().count()))
        print('{0:8d} Admin2Codes skipped because duplicated'.format(skipped_duplicated))

    def load_localities(self):
        print('Loading Localities')
        objects = []
        batch = 10000
        processed = 0
        os.chdir(self.download_dir)
        with open('cities500.txt', 'r', encoding="utf8") as fd:
            for line in fd:
                try:
                    fields = [field.strip() for field in line[:-1].split('\t')]
                    type = fields[7]
                    if type not in city_types:
                        continue
                    population = int(fields[14])
                    country_code = fields[8]
                    geonameid, name = fields[:2]
                    admin1_code = fields[10]
                    admin2_code = fields[11]
                    admin1_dic = self.countries[country_code].get(admin1_code)
                    if admin1_dic:
                        admin1_id = admin1_dic['geonameid']
                        admin2_id = admin1_dic['admins2'].get(admin2_code)
                    else:
                        admin1_id = None
                        admin2_id = None
                    timezone_name = fields[17]
                    latitude = float(fields[4])
                    longitude = float(fields[5])
                    modification_date = fields[18]
                    locality = Locality(
                        geonameid=geonameid,
                        name=name,
                        country_id=country_code,
                        admin1_id=admin1_id,
                        admin2_id=admin2_id,
                        latitude=latitude,
                        longitude=longitude,
                        point=Point(longitude, latitude),
                        timezone_id=timezone_name,
                        population=population,
                        modification_date=modification_date
                    )
                    locality.long_name = locality.generate_long_name()
                    objects.append(locality)
                    processed += 1
                    self.localities.add(geonameid)
                except Exception as inst:
                    traceback.print_exc(inst)
                    raise Exception(f"ERROR parsing:\n {line}\n The error was: {inst}")

                if processed % batch == 0:
                    Locality.objects.bulk_create(objects, ignore_conflicts=True)
                    print("{0:8d} Localities loaded".format(processed))
                    objects = []

        Locality.objects.bulk_create(objects)
        print("{0:8d} Localities loaded".format(processed))

        print('Filling missed timezones in localities')
        # Try to find the missing timezones
        for locality in Locality.objects.filter(timezone__isnull=True):
            # We assign the time zone of the most populated locality in the same admin2
            near_localities = Locality.objects.filter(admin2=locality.admin2)
            near_localities = near_localities.exclude(timezone__isnull=True)
            if not near_localities.exists():
                # We assign the time zone of the most populated locality in the same admin1
                near_localities = Locality.objects.filter(admin1=locality.admin1)
                near_localities = near_localities.exclude(timezone__isnull=True)

            if not near_localities.exists():
                # We assign the time zone of the most populated locality in the same country
                near_localities = Locality.objects.filter(country=locality.country)
                near_localities = near_localities.exclude(timezone__isnull=True)

            if near_localities.exists():
                near_localities = near_localities.order_by('-population')
                locality.timezone = near_localities[0].timezone
                locality.save()
            else:
                print(f"ERROR locality with no timezone {locality}")
                raise Exception()

    def cleanup(self):
        self.delete_empty_countries()
        self.delete_duplicated_localities()

    def delete_empty_countries(self):
        print('Setting as deleted empty Countries')
        # Countries
        countries = Country.objects.annotate(Count("locality_set")).filter(locality_set__count=0)
        for c in countries:
            c.status = Country.objects.STATUS_DISABLED
            c.save()

        print(" {0:8d} Countries set status 'STATUS_DISABLED'".format(countries.count()))

    def delete_duplicated_localities(self):
        print("Setting as deleted duplicated localities")
        total = 0
        for c in Country.objects.all():
            prev_name = ""
            for loc in c.locality_set.order_by("long_name", "-population"):
                if loc.long_name == prev_name:
                    loc.status = Locality.objects.STATUS_DISABLED
                    loc.save(check_duplicated_longname=False)
                    total += 1

                prev_name = loc.long_name

        print(" {0:8d} localities set as 'STATUS_DISABLED'".format(total))

    def load_altnames(self):
        print('Loading alternate names')
        objects = []
        allobjects = {}
        batch = 10000
        processed = 0
        os.chdir(self.download_dir)
        with open('alternateNames.txt', 'r', encoding="utf8") as fd:
            for line in fd:
                try:
                    fields = [field.strip() for field in line.split('\t')]
                    alternatenameid = fields[0]
                    locality_geonameid = fields[1]
                    if locality_geonameid not in self.localities:
                        continue

                    name = fields[3]
                    if locality_geonameid in allobjects:
                        if name in allobjects[locality_geonameid]:
                            continue
                    else:
                        allobjects[locality_geonameid] = set()

                    allobjects[locality_geonameid].add(name)
                    objects.append(AlternateName(alternatenameid=alternatenameid,
                                                 locality_id=locality_geonameid,
                                                 name=name))
                    processed += 1
                except Exception as inst:
                    traceback.print_exc(inst)
                    raise Exception(f"ERROR parsing:\n {line}\n The error was: {inst}")

                if processed % batch == 0:
                    AlternateName.objects.bulk_create(objects, ignore_conflicts=True)
                    print("{0:8d} AlternateNames loaded".format(processed))
                    objects = []

        AlternateName.objects.bulk_create(objects, ignore_conflicts=True)
        print("{0:8d} AlternateNames loaded".format(processed))

    def load_postcodes(self, fn='allCountries.txt'):
        """Load postcode files: allCountries.txt and GB_full.txt"""
        print(f"Loading postcodes from {fn}.")
        objects = []
        batch = 20000
        processed = 0
        os.chdir(self.download_dir)

        with open(fn, 'r', encoding="utf8") as fd:
            for line in fd:
                fields = [field.strip() for field in line.split('\t')]
                (
                    country_code, postal_code, place_name,
                    admin_name1, admin_code1,
                    admin_name2, admin_code2,
                    admin_name3, admin_code3,
                    latitude, longitude, accuracy
                ) = fields

                latitude = float(latitude)
                longitude = float(longitude)

                postcode = Postcode(
                    country_id=country_code,
                    postal_code=postal_code,
                    place_name=place_name,
                    admin_name1=admin_name1,
                    admin_code1=admin_code1,
                    admin_name2=admin_name2,
                    admin_code2=admin_code2,
                    admin_name3=admin_name3,
                    admin_code3=admin_code3,
                    latitude=latitude,
                    longitude=longitude,
                    point=Point(longitude, latitude),
                    accuracy=accuracy or None
                )
                objects.append(postcode)
                processed += 1

                if processed % batch == 0:
                    Postcode.objects.bulk_create(objects, ignore_conflicts=True)
                    print("{0:8d} Postcodes loaded".format(processed))
                    objects = []

    def check_errors(self):
        print('Checking errors')

        print('Checking empty country')
        if Country.objects.public().annotate(Count("locality_set")).filter(locality_set__count=0):
            print("ERROR Countries with no locality_set")
            raise Exception()

        print('Checking all Localities with timezone')
        if Locality.objects.filter(timezone__isnull=True):
            print("ERROR Localities with no timezone")
            raise Exception()

        print('Checking duplicated localities per country')
        for country in Country.objects.all():
            duplicated = country.locality_set.public().values('long_name')\
                .annotate(Count('long_name')).filter(long_name__count__gt=1)
            if len(duplicated) != 0:
                print(f"ERROR Duplicated localities in {country}: {duplicated}")
                print(duplicated)
                # raise Exception()
