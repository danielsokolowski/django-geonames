from django.contrib import admin
from geonames.models import (
    GeonamesUpdate, Timezone, Language, Currency, Country,
    Admin1Code, Admin2Code, Locality, AlternateName, Postcode
)


class PostcodeAdmin(admin.ModelAdmin):
    search_fields = ['postal_code']


class LocalityAdmin(admin.ModelAdmin):
    search_fields = ['name']
    raw_id_fields = ['admin1', 'admin2']


class AlternateNameAdmin(admin.ModelAdmin):
    search_fields = ['name']
    raw_id_fields = ['locality']


class Admin1CodeAdmin(admin.ModelAdmin):
    search_fields = ['name']
    raw_id_fields = ['locality']


admin.site.register(GeonamesUpdate)
admin.site.register(Timezone)
admin.site.register(Language)
admin.site.register(Currency)
admin.site.register(Country)
admin.site.register(Admin1Code)
admin.site.register(Admin2Code)
admin.site.register(Locality, LocalityAdmin)
admin.site.register(AlternateName, AlternateNameAdmin)
admin.site.register(Postcode, PostcodeAdmin)
