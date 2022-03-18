from decimal import Decimal
from math import acos, cos, degrees, fabs, pi, radians, sin

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.template.defaultfilters import slugify

from geonames.admin2_stopwords import trim_stopwords, admin2_stopwords

GIS_LIBRARIES = getattr(settings, 'GIS_LIBRARIES', False)
if GIS_LIBRARIES:
    from django.contrib.gis.geos import Point
    from django.contrib.gis.db import models
    from django.contrib.gis.measure import D

EARTH_R = 3959


class GeoManager(models.Manager):
    def area(self, min_latlon, max_latlon):
        min_lat, min_lon = min_latlon  # south-west corner (lower left)
        max_lat, max_lon = max_latlon  # north-east corner
        return self.filter(lat__gte=min_lat, lon__gte=min_lon)\
                   .filter(lat__lte=max_lat, lon__lte=max_lon)

    def near(self, lat, lon, radius=20, sector='', limit=100, sort=True):
        """With SQL version of the Haversine formula"""
        if not lat:
            return []

        table = self.model._meta.db_table
        pk = self.model._meta.pk.name
        if sector:
            sector = f'AND sector_id = "{sector}"'

        bbox = near_places_rough(self.model, lat, lon, miles=radius, sql=True)
        # coords = ST_GeomFromText(CONCAT('POINT(',lat ,' ', lon, ')'), 4326)
        # ST_Distance_Sphere(coords, ST_GeomFromText('POINT({lat} {lon})', 4326), {EARTH_R} ) AS distance

        qs = self.raw(f"""
            SELECT {pk},
              ({EARTH_R} * acos(cos(radians({lat})) * cos(radians(lat)) * cos(radians(lon) - radians({lon}))
                                + sin(radians({lat})) * sin(radians(lat)))) AS distance
            FROM {table} WHERE {bbox} lat IS NOT NULL {sector}
            GROUP BY {pk}
            HAVING distance < {radius} ORDER BY distance
            LIMIT {limit}
        """)
        pks = [o.pk for o in qs]
        distances = {o.pk: round(o.distance, 1) for o in qs}

        qs = self.filter(pk__in=pks)
        only = getattr(self.model, 'only', [])
        if only:
            only = self.model.only + ['urn', 'name', 'postcode']
            qs = qs.only(*only)
        for o in qs:
            setattr(o, 'distance', distances[o.pk])
        if sort:
            qs = sorted(list(qs), key=lambda x: x.distance)
        return qs


class BaseManager(GeoManager):
    """
    Additional methods / constants to Base's objects manager - using a GeoManager is fine even for plain models:

    ``BaseManager.objects.public()`` - all instances that are asccessible through front end
    """
    # Model (db table) wide constants - we put these and not in model definition to avoid circular imports.
    # one can access these constants through <foo>.objects.STATUS_DISABLED or ImageManager.STATUS_DISABLED
    STATUS_DISABLED = 0
    STATUS_ENABLED = 100
    STATUS_ARCHIVED = 500
    STATUS_CHOICES = (
        (STATUS_DISABLED, "Disabled"),
        (STATUS_ENABLED, "Enabled"),
        (STATUS_ARCHIVED, "Archived"),
    )
    # We keep status field and custom queries naming a little different as it is not always one-to-one mapping
    QUERYSET_PUBLIC_KWARGS = {'status__gte': STATUS_ENABLED}
    # We provide access this way because you can't yet chain custom manager filters e.g. 'public().open()'
    # workaround - http://stackoverflow.com/questions/2163151/custom-queryset-and-manager-without-breaking-dry
    QUERYSET_ACTIVE_KWARGS = {'status': STATUS_ENABLED}

    def public(self):
        """Returns all entries someway accessible through front end site"""
        return self.filter(**self.QUERYSET_PUBLIC_KWARGS)

    def active(self):
        """Returns all entries that are considered active, i.e. available in forms, selections, choices, etc"""
        return self.filter(**self.QUERYSET_ACTIVE_KWARGS)


# Some constants for the geo maths
EARTH_RADIUS_MI = 3959.0
KM_TO_MI = 0.621371192
DEGREES_TO_RADIANS = pi / 180.0


class GeonamesUpdate(models.Model):
    """Log the geonames updates"""
    update_date = models.DateField(auto_now_add=True)


class Timezone(models.Model):
    """Timezone information"""
    class Meta:
        ordering = ['gmt_offset', 'name']

    def __str__(self):
        if self.gmt_offset >= 0:
            sign = '+'
        else:
            sign = '-'

        gmt = fabs(self.gmt_offset)
        hours = int(gmt)
        minutes = int((gmt - hours) * 60)
        return f"{self.name} UTC{sign}{hours:02d}:{minutes:02d}"

    objects = BaseManager()

    status = models.IntegerField(blank=False, default=BaseManager.STATUS_ENABLED,
                                 choices=BaseManager.STATUS_CHOICES)
    name = models.CharField(max_length=200, primary_key=True)
    gmt_offset = models.DecimalField(max_digits=4, decimal_places=2)
    dst_offset = models.DecimalField(max_digits=4, decimal_places=2)


class Language(models.Model):
    """Language information"""
    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    status = models.IntegerField(blank=False, default=BaseManager.STATUS_ENABLED,
                                 choices=BaseManager.STATUS_CHOICES)
    name = models.CharField(max_length=200, primary_key=True)
    iso_639_1 = models.CharField(max_length=50, blank=True)

    objects = BaseManager()


class Currency(models.Model):
    """Currency related information"""
    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Currencies'

    def __str__(self):
        return f"{self.code} - {self.name}"

    objects = BaseManager()

    status = models.IntegerField(blank=False, default=BaseManager.STATUS_ENABLED,
                                 choices=BaseManager.STATUS_CHOICES)
    code = models.CharField(max_length=3, primary_key=True)
    name = models.CharField(max_length=200)
    # TODO add a symbol field!


class Country(models.Model):
    """Country information"""
    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Countries'

    def __str__(self):
        return self.name

    def search_locality(self, locality_name):
        if len(locality_name) == 0:
            return []
        q = Q(country_id=self.code)
        q &= (Q(name__iexact=locality_name) | Q(alternatenames__name__iexact=locality_name))
        return Locality.objects.filter(q).distinct()

    objects = BaseManager()

    status = models.IntegerField(blank=False, default=BaseManager.STATUS_ENABLED,
                                 choices=BaseManager.STATUS_CHOICES)
    code = models.CharField(max_length=2, primary_key=True)
    name = models.CharField(max_length=200, unique=True, db_index=True)
    languages = models.ManyToManyField(Language, related_name="country_set")
    currency = models.ForeignKey(Currency, related_name="country_set", on_delete=models.CASCADE)


class Admin1Code(models.Model):
    """Administrative subdivision"""
    class Meta:
        unique_together = (("country", "name"),)
        ordering = ['country', 'name']

    def __str__(self):
        return f'{self.country.name} > {self.name}'

    def save(self, *args, **kwargs):
        # Call the "real" save() method.
        super(Admin1Code, self).save(*args, **kwargs)

        # Update child localities long name
        for loc in self.localities.all():
            loc.save()

    objects = BaseManager()

    status = models.IntegerField(blank=False, default=BaseManager.STATUS_ENABLED,
                                 choices=BaseManager.STATUS_CHOICES)
    geonameid = models.PositiveIntegerField(primary_key=True)
    code = models.CharField(max_length=20)
    name = models.CharField(max_length=200)
    country = models.ForeignKey(Country, related_name="admin1_set", on_delete=models.CASCADE)


class Admin2Code(models.Model):
    """Administrative subdivision"""
    class Meta:
        unique_together = (('country', 'admin1', 'name'),)
        ordering = ['country', 'admin1', 'name']

    def __str__(self):
        admin1_name = ''
        if self.admin1:
            admin1_name = f'{self.admin1.name} > '
        return f'{self.country.name} > {admin1_name}{self.name}'

    def get_absolute_url(self, segment=''):
        url = f'/{self.slug}/'
        if segment:
            return f'/{segment}{url}'
        return url

    def save(self, update_localities_longname=True, update_handle=False, *args, **kwargs):
        # Check consistency
        if self.admin1 is not None and self.admin1.country != self.country:
            raise ValueError(
                f"""The country '{self.admin1.country}'
                from the Admin1 '{self.admin1}' is different
                than the country '{self.country}'
                from the Admin2 '{self.name}'
                and geonameid {self.geonameid}"""
            )
        if update_handle or not self.slug:
            self.slug = slugify(trim_stopwords(self.name, admin2_stopwords))[:35]

        # Call the "real" save() method.
        super(Admin2Code, self).save(*args, **kwargs)

        # Update child localities long name
        if update_localities_longname:
            for loc in self.locality_set.all():
                loc.save()

    objects = BaseManager()

    status = models.IntegerField(blank=False, default=BaseManager.STATUS_ENABLED,
                                 choices=BaseManager.STATUS_CHOICES)
    geonameid = models.PositiveIntegerField(primary_key=True)
    code = models.CharField(max_length=30)
    name = models.CharField(max_length=200)
    country = models.ForeignKey(Country, related_name="admin2_set", on_delete=models.CASCADE)
    admin1 = models.ForeignKey(Admin1Code, null=True, blank=True, related_name="admin2_set", on_delete=models.CASCADE)
    slug = models.CharField(max_length=35, db_index=True, blank=True, null=True)


def near_places_rough(place_type_model, lat, lon, miles, sql=None):
    """
    Rough calculation of the places at 'miles' miles of this place.
    Is rough because calculates a square instead of a circle and the earth
    is considered as an sphere, but this calculation is fast! And we don't
    need precision.
    """
    diff_lat = Decimal(degrees(miles / EARTH_RADIUS_MI))
    lat = Decimal(lat)
    lon = Decimal(lon)
    max_lat = lat + diff_lat
    min_lat = lat - diff_lat
    diff_long = Decimal(degrees(miles / EARTH_RADIUS_MI / cos(radians(lat))))
    max_long = lon + diff_long
    min_long = lon - diff_long
    if sql:
        return f"""
            lat >= {min_lat:.6f} AND lon >= {min_long:.6f} AND
            lat <= {max_lat:.6f} AND lon <= {max_long:.6f} AND"""
    return place_type_model.objects.filter(lat__gte=min_lat, lon__gte=min_long)\
                                   .filter(lat__lte=max_lat, lon__lte=max_long)


def calc_dist_nogis(la1, lo1, la2, lo2):
    # Convert lat/lon to
    # spherical coordinates in radians.
    # phi = 90 - lat
    phi1 = (90.0 - float(la1)) * DEGREES_TO_RADIANS
    phi2 = (90.0 - float(la2)) * DEGREES_TO_RADIANS

    # theta = lon
    theta1 = float(lo1) * DEGREES_TO_RADIANS
    theta2 = float(lo2) * DEGREES_TO_RADIANS

    # Compute spherical distance from spherical coordinates.
    # For two localities in spherical coordinates
    # (1, theta, phi) and (1, theta, phi)
    # cosine( arc length ) =
    #    sin phi sin phi' cos(theta-theta') + cos phi cos phi'
    # distance = rho * arc length
    cosinus = sin(phi1) * sin(phi2) * cos(theta1 - theta2) + cos(phi1) * cos(phi2)
    cosinus = round(cosinus, 14)  # to avoid math domain error in acos
    arc = acos(cosinus)

    # Multiply arc by the radius of the earth
    return arc * EARTH_RADIUS_MI


class Locality(models.Model):
    """Localities - cities, towns, villages, etc"""
    class Meta:
        # unique_together = ('country', 'admin1', 'admin2', 'slug')
        ordering = ['country', 'admin1', 'admin2', 'long_name']
        verbose_name_plural = 'Localities'

    def __str__(self):
        admin1_name, admin2_name = '', ''
        if self.admin1:
            admin1_name = f'{self.admin1.name} > '
        if self.admin2:
            admin2_name = f'{self.admin2.name} > '
        return f'{self.country.name} > {admin1_name}{admin2_name}{self.name}'

    def get_absolute_url(self, segment='', admin2_slug=None):
        url = f'/{admin2_slug or self.admin2.slug}/{self.slug}'
        if segment:
            return f'/{segment}{url}'
        return url

    def save(self, check_duplicated_longname=True, update_handle=False, *args, **kwargs):
        # Update long_name
        self.long_name = self.generate_long_name()

        if check_duplicated_longname is True:
            # and check if already exists other locality with the same long name
            other_localities = Locality.objects.filter(long_name=self.long_name)
            other_localities = other_localities.exclude(geonameid=self.geonameid)

            if other_localities.count() > 0:
                raise ValueError(f"Duplicated locality long name '{self.long_name}'")

        # Check consistency
        if self.admin1 is not None and self.admin1.country != self.country:
            raise ValueError(f"""The country '{self.admin1.country}'
                from the Admin1 '{self.admin1}' is different
                than the country '{self.country}'
                from the locality '{self.long_name}'""")

        if self.admin2 is not None and self.admin2.country != self.country:
            raise ValueError(f"""The country '{self.admin2.country}'
                from the Admin2 '{self.admin2}'
                is different than the country '{self.country}'
                from the locality '{self.long_name}'""")

        if GIS_LIBRARIES:
            self.point = Point(float(self.lon), float(self.lat))

        if update_handle or not self.slug:
            self.slug = slugify(self.name)[:35]

        # Call the "real" save() method.
        super(Locality, self).save(*args, **kwargs)

    def generate_long_name(self):
        long_name = self.name
        try:
            if self.admin2 is not None:
                long_name = f"{long_name}, {self.admin2.name}"
        except Admin2Code.DoesNotExist:
            pass

        if self.admin1 is not None:
            long_name = f"{long_name}, {self.admin1.name}"

        return long_name

    @property
    def title(self):
        return self.generate_long_name()

    def near_localities_rough(self, miles):
        return near_places_rough(Locality, self.lat, self.lon, miles)

    def near_locals_nogis(self, miles):
        ids = []
        for loc in self.near_localities_rough(miles).values_list(
                "geonameid", "lat", "lon"):
            other_geonameid = loc[0]
            if self.geonameid == other_geonameid:
                distance = 0
                ids.append(other_geonameid)
            else:
                distance = self.calc_distance_nogis(loc[1], loc[2])
                if distance <= miles:
                    ids.append(other_geonameid)
        return ids

    def calc_distance_nogis(self, la2, lo2):
        return calc_dist_nogis(self.lat, self.lon, la2, lo2)

    def near_localities(self, miles):
        if not GIS_LIBRARIES:
            raise NotImplementedError
        localities = self.near_localities_rough(miles)
        localities = localities.filter(point__distance_lte=(self.point, D(mi=miles)))
        return localities.values_list("geonameid", flat=True)

    objects = BaseManager()

    status = models.IntegerField(blank=False, default=BaseManager.STATUS_ENABLED,
                                 choices=BaseManager.STATUS_CHOICES)
    geonameid = models.PositiveIntegerField(primary_key=True)
    name = models.CharField(max_length=200, db_index=True)
    long_name = models.CharField(max_length=200)
    country = models.ForeignKey(Country, related_name="locality_set", on_delete=models.CASCADE)
    admin1 = models.ForeignKey(Admin1Code, null=True, blank=True, related_name="locality_set", on_delete=models.CASCADE)
    admin2 = models.ForeignKey(Admin2Code, null=True, blank=True, related_name="locality_set", on_delete=models.CASCADE)
    timezone = models.ForeignKey(Timezone, related_name="locality_set", null=True, on_delete=models.CASCADE)
    population = models.PositiveIntegerField()
    lat = models.DecimalField(max_digits=9, decimal_places=6, null=True)
    lon = models.DecimalField(max_digits=9, decimal_places=6, null=True)
    if GIS_LIBRARIES:
        point = models.PointField(geography=False, srid=4326)
    modification_date = models.DateField()
    slug = models.CharField(max_length=35, db_index=True, blank=True, null=True)


class AlternateName(models.Model):
    """Other names for localities for example in different languages etc."""
    class Meta:
        # unique_together = (("locality", "name"),)  # doesn't work on MySQL due to index encoding?
        ordering = ['locality__pk', 'name']

    def __str__(self):
        return f'{self.locality.name} > {self.name}'

    status = models.IntegerField(blank=False, default=BaseManager.STATUS_ENABLED,
                                 choices=BaseManager.STATUS_CHOICES)
    alternatenameid = models.PositiveIntegerField(primary_key=True)
    locality = models.ForeignKey(Locality, related_name="alternatename_set", on_delete=models.CASCADE)
    name = models.CharField(max_length=200, db_index=True)
    # TODO include localization code

    objects = BaseManager()


class Postcode(models.Model):
    """Postcodes"""
    country = models.ForeignKey(Country, related_name="postcode_set", on_delete=models.CASCADE)
    postal_code = models.CharField(max_length=20, db_index=True)
    place_name = models.CharField(max_length=180)
    admin_name1 = models.CharField(blank=True, null=True, max_length=100, verbose_name='state')
    admin_code1 = models.CharField(blank=True, null=True, max_length=20,  verbose_name='state')
    admin_name2 = models.CharField(blank=True, null=True, max_length=100, verbose_name='county/province')
    admin_code2 = models.CharField(blank=True, null=True, max_length=20,  verbose_name='county/province')
    admin_name3 = models.CharField(blank=True, null=True, max_length=100, verbose_name='community')
    admin_code3 = models.CharField(blank=True, null=True, max_length=20,  verbose_name='community')
    lat = models.DecimalField(max_digits=9, decimal_places=6, null=True)
    lon = models.DecimalField(max_digits=9, decimal_places=6, null=True)
    if GIS_LIBRARIES:
        point = models.PointField(geography=False, srid=4326)

    # accuracy of lat/lng from 1=estimated, 4=geonameid, 6=centroid of addresses or shape
    accuracy = models.IntegerField(blank=True, null=True)
    objects = GeoManager()

    def near_localities_rough(self, miles):
        return near_places_rough(Locality, self.lat, self.lon, miles)

    def title(self):
        return f'{self.postal_code}, {self.place_name}'

    @property
    def name(self):
        return self.title()

    @property
    def slug(self):
        return slugify(self.postal_code)

    def __str__(self):
        return f'{self.country.name} > {self.postal_code}'

    def get_absolute_url(self):
        return f'/search?q_key={slugify(self.postal_code).upper()}&q_typ=p'
