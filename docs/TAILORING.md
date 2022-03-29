Customizations
--------------

I recommend you rename the root folder to 'geonames-tailored' and include that in your project and modify/hack it
as needed. Yes, there are drawbacks to this approach and one could have a lengthy discussion about it but there
are benefits, and it's just my suggestion to you based on personal experience; so your directory layout might end up:

	/example.com/
	/example.com/source-assets/							-> images/psd/etc
	/example.com/src/
	...
	/example.com/src/geonames-tailored/ 				-> tailored and modified version
	/example.com/src/geonames-tailored/geonames 
	...
	/example.com/src/django-project						-> your site's code
	/example.com/virtualenv/	

If you do wish to keep this as a separate app you can create a 'geonames_ext' app inside your django project and
extend the code base through subclassing, monkey-patching, etc. - your directory layout might be:

	/example.com/
	/example.com/source-assets/							-> images/psd/etc
	/example.com/src/
	...
	/example.com/src/django-project						
	/example.com/src/django-project/home				
	/example.com/src/django-project/geonames_ext/		-> your app modification code here
	...
	/example.com/src/django-project/contactus/home
	...
	/example.com/virtualenv/
