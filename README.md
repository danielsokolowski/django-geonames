django-geonames 
===============

### (a django-cities + django-currencies alternative) ###

django-geonames is a Django app that allows you in your geo-django enabled project to leverage the geographical city, 
country (ISO 3166), province/state, currency, timezone (GMT/DST) and language (ISO 639) public data information 
available from [GeoNames](http://www.geonames.org). 

Unlike the 'django-cities' app the models are defined to be straightforward representation of geonames.org's data 
hierarchy structure which aims to simplify the overall complexity. 

<img style='margin-left: auto; margin-right: auto' height=300 
src="https://raw.github.com/danielsokolowski/django-geonames/master/geonames-model-graph.png"> 

Please note the original author 'django-geonames' appears to be MIA (as of Jun 2013) and so that is the reason this 
repository is now stand alone and no longer a fork. Furthermore there has been various bug fixes and improvements 
that make it no longer compatible with the original. 

Quick start
-----------

* Enable Gis in your DB https://docs.djangoproject.com/en/dev/ref/contrib/gis/tutorial/
    In case you're using Postgresql as your DB, in the folder 'scripts' is available a script to set up PostGis.

* Add "geonames" to your INSTALLED_APPS setting like this::

      INSTALLED_APPS = (
          ...
          'geonames',
      )

* Run `python manage.py makemigrations` & `python manage.py migrate` to create the geonames models.

* Run `python manage.py loadgeonames` to import the data from geonames.org (This process can take long).

Customizations
--------------

I recommend you rename the root folder to 'geonames-tailored' and include that in your project and modify/hack it
as needed. Yes, there are drawbacks to this approach and one could have a lengthy discussion about it but there
are benefits and it's just my suggestion to you based on personal experience; so your directory layout might end up:

	/site-domain-name.com/
	/site-domain-name.com/source-assets/							-> images/psd/etc
	/site-domain-name.com/src/
	...
	/site-domain-name.com/src/geonames-tailroed/ 					-> tailored and modified version
	/site-domain-name.com/src/geonames-tailroed/geonames 
	...
	/site-domain-name.com/src/django-project						-> your site's code
	/site-domain-name.com/virtualenv/	

If you do wish to keep this as a seperate app you can create a 'geonames_ext' app inside your django project and
extend the code base through subclassing, monkeypatching, etc. - your directory layout might be:

	/site-domain-name.com/
	/site-domain-name.com/source-assets/							-> images/psd/etc
	/site-domain-name.com/src/
	...
	/site-domain-name.com/src/django-project						
	/site-domain-name.com/src/django-project/home				
	/site-domain-name.com/src/django-project/geonames_ext/			-> your app modification code here
	...
	/site-domain-name.com/src/django-project/contactus/home
	...
	/site-domain-name.com/virtualenv/

FYI: I prefer to be explicit and in the tailored example would have named the folder 
	 'github-danielsokolowski-django-geonames-tailored' 
 
