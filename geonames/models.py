from decimal import Decimal
from django.contrib.gis.db import models
from django.contrib.gis.measure import D
from django.db.models import Q
from math import degrees, radians, cos, sin, acos, pi, fabs
from django.contrib.gis.geos import Point


# Some constants for the geo maths
EARTH_RADIUS_MI = 3959.0
KM_TO_MI = 0.621371192
DEGREES_TO_RADIANS = pi / 180.0


class GeonamesUpdate(models.Model):
    """
    To log the geonames updates
    """
    update_date = models.DateField(auto_now_add=True)


class Timezone(models.Model):
    name = models.CharField(max_length=200, primary_key=True)
    gmt_offset = models.DecimalField(max_digits=4, decimal_places=2)
    dst_offset = models.DecimalField(max_digits=4, decimal_places=2)

    class Meta:
        ordering = ['gmt_offset', 'name']

    def __unicode__(self):
        if self.gmt_offset >= 0:
            sign = '+'
        else:
            sign = '-'

        gmt = fabs(self.gmt_offset)
        hours = int(gmt)
        minutes = int((gmt - hours) * 60)
        return u"(UTC{0}{1:02d}:{2:02d}) {3}".format(sign, hours, minutes, self.name)


class Language(models.Model):
    name = models.CharField(max_length=200, primary_key=True)
    iso_639_1 = models.CharField(max_length=50, blank=True)

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return u"[{}] {}".format(self.iso_639_1, self.name)


class Currency(models.Model):
    code = models.CharField(max_length=3, primary_key=True)
    name = models.CharField(max_length=200)

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return self.name


class ActiveCountryManager(models.Manager):
    def get_query_set(self):
        return super(ActiveCountryManager, self).get_query_set().filter(deleted=False)


class Country(models.Model):
    code = models.CharField(max_length=2, primary_key=True)
    name = models.CharField(max_length=200, unique=True, db_index=True)
    languages = models.ManyToManyField(Language, related_name="countries")
    currency = models.ForeignKey(Currency, related_name="countries")
    # is the website available in this country?
    available = models.BooleanField(default=False)
    deleted = models.BooleanField(default=False)

    objects = ActiveCountryManager()
    objects_deleted_inc = models.Manager()

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return self.name

    def search_locality(self, locality_name):
        if len(locality_name) == 0:
            return []
        q = Q(country_id=self.code)
        q &= (Q(name__iexact=locality_name) | Q(alternatenames__name__iexact=locality_name))
        return Locality.objects.filter(q).distinct()


class Admin1Code(models.Model):
    geonameid = models.PositiveIntegerField(primary_key=True)
    code = models.CharField(max_length=7)
    name = models.CharField(max_length=200)
    country = models.ForeignKey(Country, related_name="admins1")

    class Meta:
        unique_together = (("country", "name"),)

    def __unicode__(self):
        return u"{}, {}".format(self.name, self.country.name)

    def save(self, *args, **kwargs):
        # Call the "real" save() method.
        super(Admin1Code, self).save(*args, **kwargs)

        # Update child localities long name
        for loc in self.localities.all():
            loc.save()


class Admin2Code(models.Model):
    geonameid = models.PositiveIntegerField(primary_key=True)
    code = models.CharField(max_length=30)
    name = models.CharField(max_length=200)
    country = models.ForeignKey(Country, related_name="admins2")
    admin1 = models.ForeignKey(Admin1Code, null=True, blank=True, related_name="admins2")

    class Meta:
        unique_together = (("country", "admin1", "name"),)

    def __unicode__(self):
        s = u"{}".format(self.name)
        if self.admin1 is not None:
            s = u"{}, {}".format(s, self.admin1.name)

        return u"{}, {}".format(s, self.country.name)

    def save(self, *args, **kwargs):
        # Check consistency
        if self.admin1 is not None and self.admin1.country != self.country:
            raise StandardError("The country '{}' from the Admin1 '{}' is different than the country '{}' from the Admin2 '{}' and geonameid {}".format(
                                self.admin1.country, self.admin1, self.country, self.name, self.geonameid))

        # Call the "real" save() method.
        super(Admin2Code, self).save(*args, **kwargs)

        # Update child localities long name
        for loc in self.localities.all():
            loc.save()


class ActiveLocalitiesManager(models.GeoManager):
    def get_query_set(self):
        return super(ActiveLocalitiesManager, self).get_query_set().filter(deleted=False)


class Locality(models.Model):
    geonameid = models.PositiveIntegerField(primary_key=True)
    name = models.CharField(max_length=200, db_index=True)
    long_name = models.CharField(max_length=200)
    country = models.ForeignKey(Country, related_name="localities")
    admin1 = models.ForeignKey(Admin1Code, null=True, blank=True, related_name="localities")
    admin2 = models.ForeignKey(Admin2Code, null=True, blank=True, related_name="localities")
    timezone = models.ForeignKey(Timezone, related_name="localities", null=True)
    population = models.PositiveIntegerField()
    latitude = models.DecimalField(max_digits=7, decimal_places=2)
    longitude = models.DecimalField(max_digits=7, decimal_places=2)
    point = models.PointField(geography=False)
    modification_date = models.DateField()
    deleted = models.BooleanField(default=False)

    objects = ActiveLocalitiesManager()
    objects_deleted_inc = models.GeoManager()

    class Meta:
        ordering = ['long_name']

    def __unicode__(self):
        return self.long_name

    def save(self, check_duplicated_longname=True, *args, **kwargs):
        # Update long_name
        self.long_name = self.generate_long_name()

        if check_duplicated_longname is True:
            # and check if already exists other locality with the same long name
            other_localities = Locality.objects.filter(long_name=self.long_name)
            other_localities = other_localities.exclude(geonameid=self.geonameid)

            if other_localities.count() > 0:
                raise StandardError("Duplicated locality long name '{}'".format(self.long_name))

        # Check consistency
        if self.admin1 is not None and self.admin1.country != self.country:
            raise StandardError("The country '{}' from the Admin1 '{}' is different than the country '{}' from the locality '{}'".format(
                            self.admin1.country, self.admin1, self.country, self.long_name))

        if self.admin2 is not None and self.admin2.country != self.country:
            raise StandardError("The country '{}' from the Admin2 '{}' is different than the country '{}' from the locality '{}'".format(
                            self.admin2.country, self.admin2, self.country, self.long_name))

        self.point = Point(float(self.longitude), float(self.latitude))

        # Call the "real" save() method.
        super(Locality, self).save(*args, **kwargs)

    def generate_long_name(self):
        long_name = u"{}".format(self.name)
        if self.admin2 is not None:
            long_name = u"{}, {}".format(long_name, self.admin2.name)

        if self.admin1 is not None:
            long_name = u"{}, {}".format(long_name, self.admin1.name)

        return long_name

    def near_localities_rough(self, miles):
        """
        Rough calculation of the localities at 'miles' miles of this locality.
        Is rough because calculates a square instead of a circle and the earth
        is considered as an sphere, but this calculation is fast! And we don't
        need precission.
        """
        diff_lat = Decimal(degrees(miles / EARTH_RADIUS_MI))
        latitude = Decimal(self.latitude)
        longitude = Decimal(self.longitude)
        max_lat = latitude + diff_lat
        min_lat = latitude - diff_lat
        diff_long = Decimal(degrees(miles / EARTH_RADIUS_MI / cos(radians(latitude))))
        max_long = longitude + diff_long
        min_long = longitude - diff_long
        near_localities = Locality.objects.filter(latitude__gte=min_lat, longitude__gte=min_long)
        near_localities = near_localities.filter(latitude__lte=max_lat, longitude__lte=max_long)
        return near_localities

    def near_locals_nogis(self, miles):
        ids = []
        for loc in self.near_localities_rough(miles).values_list("geonameid", "latitude", "longitude"):
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
        # Convert latitude and longitude to
        # spherical coordinates in radians.
        # phi = 90 - latitude
        phi1 = (90.0 - float(self.latitude)) * DEGREES_TO_RADIANS
        phi2 = (90.0 - float(la2)) * DEGREES_TO_RADIANS

        # theta = longitude
        theta1 = float(self.longitude) * DEGREES_TO_RADIANS
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

    def near_localities(self, miles):
        localities = self.near_localities_rough(miles)
        localities = localities.filter(point__distance_lte=(self.point, D(mi=miles)))
        return localities.values_list("geonameid", flat=True)


class AlternateName(models.Model):
    locality = models.ForeignKey(Locality, related_name="alternatenames")
    name = models.CharField(max_length=200, db_index=True)
    # TODO include localization code

    class Meta:
        unique_together = (("locality", "name"),)
        ordering = ['name']

    def __unicode__(self):
        return self.name
