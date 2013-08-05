from django.conf import settings
from django.contrib.gis.db import models

class BaseManager(models.GeoManager):
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
    # We keep status field and custom queries naming a little different as it is not one-to-one mapping in all situations
    QUERYSET_PUBLIC_KWARGS = {'status__gte': STATUS_ENABLED} # Because you can't yet chain custom manager filters ex. 
                                                             #'public().open()' we provide access this way.  
                                                             # workaround - http://stackoverflow.com/questions/2163151/custom-queryset-and-manager-without-breaking-dry  
    QUERYSET_ACTIVE_KWARGS = {'status': STATUS_ENABLED}
    
    def public(self):
        """ Returns all entries someway accessible through front end site"""
        return self.filter(**self.QUERYSET_PUBLIC_KWARGS)
    def active(self):
        """ Returns all entries that are considered active, i.e. aviable in forms, selections, choices, etc """
        return self.filter(**self.QUERYSET_ACTIVE_KWARGS)

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
    """ Stores the Timezone information """
    ### model options - "anything that's not a field"
    class Meta:
        ordering = ['gmt_offset', 'name']

    ### Python class methods
    def __unicode__(self):
        if self.gmt_offset >= 0:
            sign = '+'
        else:
            sign = '-'

        gmt = fabs(self.gmt_offset)
        hours = int(gmt)
        minutes = int((gmt - hours) * 60)
        if settings.DEBUG:
            return u"PK{0} UTC{1}{2:02d}:{3:02d}".format('PK' + unicode(self.pk), sign, hours, minutes)
        return u"{0} UTC{1}{2:02d}:{3:02d}".format(self.name, sign, hours, minutes)
    
    ### custom managers
    objects = BaseManager()
    
    ### model DB fields
    status = models.IntegerField(blank=False, default=BaseManager.STATUS_ENABLED, 
                                # specify blank=False default=<value> to avoid form select '-------' rendering 
                                choices=BaseManager.STATUS_CHOICES)
    name = models.CharField(max_length=200, primary_key=True)
    gmt_offset = models.DecimalField(max_digits=4, decimal_places=2)
    dst_offset = models.DecimalField(max_digits=4, decimal_places=2)

class Language(models.Model):
    """ Model to  hold Language information """
    ### model options - "anything that's not a field"
    class Meta:
        ordering = ['name']

    ### Python convention class methods
    def __unicode__(self):
        if settings.DEBUG:
            return u"PK{0}".format(self.name)
        return u"{0}".format(self.name)

    ### model DB fields
    status = models.IntegerField(blank=False, default=BaseManager.STATUS_ENABLED, 
                                # specify blank=False default=<value> to avoid form select '-------' rendering 
                                choices=BaseManager.STATUS_CHOICES)
    name = models.CharField(max_length=200, primary_key=True)
    iso_639_1 = models.CharField(max_length=50, blank=True)

    ### custom managers
    objects = BaseManager()
    
class Currency(models.Model):
    """ Model to hold Currency related information """
    ### model options - "anything that's not a field"
    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Currencies'

    ### Python convention class methods
    def __unicode__(self):
        if settings.DEBUG: 
            return u"PK{0}: {1}".format(self.code, self.name)
        return u"{0} - {1}".format(self.code, self.name)


    ### custom managers
    objects = BaseManager()
    
    ### model DB fields
    status = models.IntegerField(blank=False, default=BaseManager.STATUS_ENABLED, 
                                # specify blank=False default=<value> to avoid form select '-------' rendering 
                                choices=BaseManager.STATUS_CHOICES)
    code = models.CharField(max_length=3, primary_key=True)
    name = models.CharField(max_length=200)
    # TODO add a symbol field!


class Country(models.Model):
    """ Model definition to hold Country information"""
    ### model options - "anything that's not a field"
    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Countries'

    ### Python convention class methods
    def __unicode__(self):
        if settings.DEBUG: 
            return u'PK{0}: {1}'.format(self.code, self.name)
        return u'{0}'.format(self.name)

    ### extra model functions
    def search_locality(self, locality_name):
        if len(locality_name) == 0:
            return []
        q = Q(country_id=self.code)
        q &= (Q(name__iexact=locality_name) | Q(alternatenames__name__iexact=locality_name))
        return Locality.objects.filter(q).distinct()

    ### custom managers
    objects = BaseManager()

    ### model DB fields
    status = models.IntegerField(blank=False, default=BaseManager.STATUS_ENABLED, 
                                # specify blank=False default=<value> to avoid form select '-------' rendering 
                                choices=BaseManager.STATUS_CHOICES)
    code = models.CharField(max_length=2, primary_key=True)
    name = models.CharField(max_length=200, unique=True, db_index=True)
    languages = models.ManyToManyField(Language, related_name="country_set")
    currency = models.ForeignKey(Currency, related_name="country_set")
    

class Admin1Code(models.Model):
    """ Hold information about administrative subdivision """
    ### model options - "anything that's not a field"
    class Meta:
        unique_together = (("country", "name"),)
        ordering = ['country', 'name']

    ### Python convention class methods
    def __unicode__(self):
        if settings.DEBUG:
            return u'PK{0}: {1} > {2}'.format(self.geonameid, self.country.name, self.name)
        return u'{0}, {1}'.format(self.name, self.country.name)

    ### Django established method
    def save(self, *args, **kwargs):
        # Call the "real" save() method.
        super(Admin1Code, self).save(*args, **kwargs)

        # Update child localities long name
        for loc in self.localities.all():
            loc.save()
    
    ### custom managers
    objects = BaseManager()
    
    ### model DB fields
    status = models.IntegerField(blank=False, default=BaseManager.STATUS_ENABLED, 
                                # specify blank=False default=<value> to avoid form select '-------' rendering 
                                choices=BaseManager.STATUS_CHOICES)
    geonameid = models.PositiveIntegerField(primary_key=True)
    code = models.CharField(max_length=7)
    name = models.CharField(max_length=200)
    country = models.ForeignKey(Country, related_name="admin1_set")

class Admin2Code(models.Model):
    """ Hold information about administrative subdivision """
    ### model options - "anything that's not a field"
    class Meta:
        unique_together = (("country", "admin1", "name"),)
        ordering = ['country', 'admin1', 'name']
        
    ### Python convention class methods
    def __unicode__(self):
        admin1_name = None
        if self.admin1: admin1_name = self.admin1.name
        if settings.DEBUG:
            return u'PK{0}: {1}{2} > {3}'.format(self.geonameid, self.country.name, 
                                                    ' > ' + admin1_name if admin1_name else '', 
                                                    self.name)
        return u'{0}, {1}{2}'.format(self.name, 
                                        admin1_name + ', ' if admin1_name else '', 
                                        self.country.name)

    ### Django established method
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
    
    ### custom managers
    objects = BaseManager()
    
    ### model DB fields
    status = models.IntegerField(blank=False, default=BaseManager.STATUS_ENABLED, 
                                # specify blank=False default=<value> to avoid form select '-------' rendering 
                                choices=BaseManager.STATUS_CHOICES)
    geonameid = models.PositiveIntegerField(primary_key=True)
    code = models.CharField(max_length=30)
    name = models.CharField(max_length=200)
    country = models.ForeignKey(Country, related_name="admin2_set")
    admin1 = models.ForeignKey(Admin1Code, null=True, blank=True, related_name="admin2_set")

    

class Locality(models.Model):
    """ Hold locality information - cities, towns, villages, etc """
    ### model options - "anything that's not a field"
    class Meta:
        ordering = ['country', 'admin1', 'admin2', 'long_name']
        verbose_name_plural = 'Localities'

    ### Python class methods
    def __unicode__(self):
        admin1_name = None
        if self.admin1: admin1_name = self.admin1.name
        admin2_name = None 
        if self.admin2: admin2_name = self.admin2.name
        if settings.DEBUG:
            return u'PK{0}: {1}{2}{3} > {4}'.format(self.geonameid, self.country.name, 
                                        ' > ' + admin1_name  if admin1_name else '',
                                        ' > ' + admin2_name + ' > ' if admin2_name else '',
                                        self.name)
        return u'{0}{1}{2}, {3}'.format(self.name, 
                                        ', ' + admin2_name if admin2_name else '',
                                        ', ' + admin1_name if admin1_name else '',
                                        self.country.name)

    ### Python convention class methods
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

    ### extra model functions
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

    ### custom managers
    objects = BaseManager()

    ### model DB fields
    status = models.IntegerField(blank=False, default=BaseManager.STATUS_ENABLED, 
                                # specify blank=False default=<value> to avoid form select '-------' rendering 
                                choices=BaseManager.STATUS_CHOICES)
    geonameid = models.PositiveIntegerField(primary_key=True)
    name = models.CharField(max_length=200, db_index=True)
    long_name = models.CharField(max_length=200)
    country = models.ForeignKey(Country, related_name="locality_set")
    admin1 = models.ForeignKey(Admin1Code, null=True, blank=True, related_name="locality_set")
    admin2 = models.ForeignKey(Admin2Code, null=True, blank=True, related_name="locality_set")
    timezone = models.ForeignKey(Timezone, related_name="locality_set", null=True)
    population = models.PositiveIntegerField()
    latitude = models.DecimalField(max_digits=7, decimal_places=2)
    longitude = models.DecimalField(max_digits=7, decimal_places=2)
    point = models.PointField(geography=False)
    modification_date = models.DateField()


class AlternateName(models.Model):
    """ other names for localities for example in different languages etc. """
    ### model options - "anything that's not a field"
    class Meta:
        unique_together = (("locality", "name"),)
        ordering = ['locality__pk', 'name']
        
    ### Python class methods
    def __unicode__(self):
        if settings.DEBUG:
            return u'PK{0}: {1} ({2})'.format(self.alternatenameid, self.name, self.locality.name)
        return u'{0} ({1})'.format(self.name, self.locality.name)
       
    ### model DB fields
    status = models.IntegerField(blank=False, default=BaseManager.STATUS_ENABLED, 
                                # specify blank=False default=<value> to avoid form select '-------' rendering 
                                choices=BaseManager.STATUS_CHOICES)
    alternatenameid = models.PositiveIntegerField(primary_key=True)
    locality = models.ForeignKey(Locality, related_name="alternatename_set")
    name = models.CharField(max_length=200, db_index=True)
    # TODO include localization code
    
    ### custom managers
    objects = BaseManager()
