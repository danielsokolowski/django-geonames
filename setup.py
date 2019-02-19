from setuptools import setup, find_packages
import os

README = open(os.path.join(os.path.dirname(__file__), 'README.md')).read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name = 'django-geonames',
    version = '0.1',
    packages = find_packages(),
    include_package_data = True,
    license = 'BSD License',
    description = 'A Django app to use the information available in http://www.geonames.org',
    long_description = README,
    url = 'https://github.com/dablak/django-geonames',
    author = 'Daniel Blasco Calzada',
    author_email = 'projects@dablak.com',
    zip_safe = False,
    classifiers = [
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
