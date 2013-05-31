from django.contrib import admin
from django.db import models

# Auto registers all app models with the admin, eventually you will want a tailored admin.py
current_app = models.get_app(__package__) 
for model in models.get_models(current_app):
	admin.site.register(model, admin.ModelAdmin) # we pass admin.ModelAdmin because any monkey patched version does not
												 # get loaded from within admin.site.register method