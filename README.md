django-geonames 
===============

### (a django-cities + django-currencies alternative) ###

django-geonames is a Django app that allows you to leverage the geographical city/town/village (locality), 
country (ISO 3166), province/state (admin level 1 code), county/district (admin level 2 code),
currency, timezone (GMT/DST), language (ISO 639) and postcode (including UK)
public data information available from [GeoNames](http://www.geonames.org)
and not only in a geo-django enabled project.

Unlike the 'django-cities' app the models are defined to be straightforward representation
of geonames.org's data hierarchy structure which aims to simplify the overall complexity. 

<img style='margin-left: auto; margin-right: auto' height=300 
src="https://raw.github.com/fmalina/django-geonames/master/docs/geonames-model-graph.png"> 

Please note the original author 'django-geonames' appears to be MIA (as of Jun 2013) and so that is the reason this 
repository is now stand alone and no longer a fork. Furthermore, there has been various bug fixes and improvements 
that make it no longer compatible with the original.

Quick start
-----------

* `GIS_LIBRARIES = False` setting to disable requirement for geodjango is a default as the author
  finds geodjango libs too heavy, difficult to install and run in production due to
  random warnings in the logs. Queryset managers to do without native spatial SQL tooling are provided
* Database table for postcodes is added and full UK postcodes are loaded by default too
* To enable Gis in your DB see https://docs.djangoproject.com/en/dev/ref/contrib/gis/tutorial/
  If you're using Postgresql DB, a script to set up PostGis is available in the 'scripts' folder
* Add "geonames" to your INSTALLED_APPS setting like this::

      INSTALLED_APPS = (
          ...
          'geonames',
      )
* Run `python manage.py migrate` to create the geonames DB tables.
* Run `python manage.py loadgeonames` to import the data from geonames.org
  (This process takes about 40 minutes on author's machine).

You can also read suggestions on [tailoring](docs/TAILORING.md)
and [TODO](docs/TODO.md) from one of the authors.
