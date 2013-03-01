===============
django-geonames
===============

django-geonames is a Django app to easily include in your project the geographic data available in http://www.geonames.org It also provides a management command to import this data.

Quick start
-----------

* Enable Gis in your DB https://docs.djangoproject.com/en/dev/ref/contrib/gis/tutorial/
    In case you're using Postgresql as your DB, in the folder 'scripts' is available a script to set up PostGis.

* Add "geonames" to your INSTALLED_APPS setting like this::

      INSTALLED_APPS = (
          ...
          'geonames',
      )

* Run `python manage.py syncdb` to create the geonames models.

* Run `python manage.py loadGeonames` to import the data from geonames.org (This process can take long).

