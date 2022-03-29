#TODO: tests
# from django.test import TestCase
# from geonames.models import Timezone, Language, Currency, Country, Admin1Code, Admin2Code, Locality,\
#     AlternateName
# 
# 
# class SimpleTest(TestCase):
#     def setUp(self):
#         # Timezones
#         self.tz1 = Timezone.objects.create(name="tz1", gmt_offset=0.0, dst_offset=0.0)
#         self.tz2 = Timezone.objects.create(name="tz2", gmt_offset=2.0, dst_offset=1.0)
# 
#         # Languages
#         self.language1 = Language.objects.create(name="English", iso_639_1="EN")
#         self.language2 = Language.objects.create(name="Spanish", iso_639_1="ES")
# 
#         # Currencies
#         self.currency1 = Currency.objects.create(code="GBP", name="Great Britain Pound")
#         self.currency2 = Currency.objects.create(code="EUR", name="Euro")
# 
#         # Countries
#         self.country1 = Country.objects.create(code='C1', name="Country1", currency=self.currency1)
#         self.country1.languages.add(self.language1)
#         self.country2 = Country.objects.create(code='C2', name="Country2", currency=self.currency2)
#         self.country2.languages.add(self.language1)
#         self.country2.languages.add(self.language2)
# 
#         # Admin1Codes
#         self.admin1code1 = Admin1Code.objects.create(geonameid=1, code="a1c1", name="a1c1 name", country=self.country1)
#         self.admin1code2 = Admin1Code.objects.create(geonameid=2, code="a1c2", name="a1c2 name", country=self.country1)
#         self.admin1code3 = Admin1Code.objects.create(geonameid=3, code="a1c3", name="a1c3 name", country=self.country2)
#         self.admin1code4 = Admin1Code.objects.create(geonameid=4, code="a1c4", name="a1c4 name", country=self.country2)
# 
#         # Admin2Codes
#         self.admin2code1 = Admin2Code.objects.create(geonameid=5, code="a2c1", name="a2c1 name", country=self.country1, admin1=self.admin1code1)
#         self.admin2code2 = Admin2Code.objects.create(geonameid=6, code="a2c2", name="a2c2 name", country=self.country1, admin1=self.admin1code1)
#         self.admin2code3 = Admin2Code.objects.create(geonameid=7, code="a2c3", name="a2c3 name", country=self.country1, admin1=self.admin1code2)
#         self.admin2code4 = Admin2Code.objects.create(geonameid=8, code="a2c4", name="a2c4 name", country=self.country1, admin1=self.admin1code2)
#         self.admin2code5 = Admin2Code.objects.create(geonameid=9, code="a2c5", name="a2c5 name", country=self.country2, admin1=self.admin1code3)
#         self.admin2code6 = Admin2Code.objects.create(geonameid=10, code="a2c6", name="a2c6 name", country=self.country2, admin1=self.admin1code3)
#         self.admin2code7 = Admin2Code.objects.create(geonameid=11, code="a2c7", name="a2c7 name", country=self.country2, admin1=self.admin1code4)
#         self.admin2code8 = Admin2Code.objects.create(geonameid=12, code="a2c8", name="a2c8 name", country=self.country2, admin1=self.admin1code4)
# 
#         # Localities
#         self.locality1 = Locality.objects.create(geonameid=13, name="Loc1", country=self.country1, admin1=self.admin1code1, admin2=self.admin2code1, timezone=self.tz1, population=1, lat=1, lon=1, modification_date="2012-1-1")
#         self.locality2 = Locality.objects.create(geonameid=14, name="Loc2", country=self.country1, admin1=self.admin1code1, admin2=self.admin2code1, timezone=self.tz1, population=1, lat=1, lon=2, modification_date="2012-1-1")
#         self.locality3 = Locality.objects.create(geonameid=15, name="Loc3", country=self.country1, admin1=self.admin1code1, admin2=self.admin2code1, timezone=self.tz1, population=1, lat=1, lon=3, modification_date="2012-1-1")
# 
#         # Alternate names
#         self.altName1 = AlternateName.objects.create(locality=self.locality1, name="Loc1 alt")
# 
#     def test_country_deleted(self):
#         country3 = Country.objects.create(code='C3', name="Country3", currency=self.currency1, deleted=True)
#         all_countries = Country.objects.all()
#         self.assertEqual(all_countries.count(), 2)
#         self.assertNotIn(country3, all_countries)
#         all_w_deleted = Country.objects_deleted_inc.all()
#         self.assertEqual(all_w_deleted.count(), 3)
# 
#     def test_change_adm1_name(self):
#         # The long_name of the countries change if we change the name of their adm1
#         self.assertEqual(u"Loc1, a2c1 name, a1c1 name", self.locality1.long_name)
#         self.admin1code1.name = "another adm1 name"
#         self.admin1code1.save()
#         self.locality1 = Locality.objects.get(pk=self.locality1.geonameid)
#         self.assertEqual(u"Loc1, a2c1 name, another adm1 name", self.locality1.long_name)
# 
#     def test_adm2_country_consistency(self):
#         # if country in adm1 is not the same than the one in adm2 then exception is raised
#         adm2 = Admin2Code(geonameid=12, code="a2c8", name="a2c8 name", country=self.country1, admin1=self.admin1code4)
#         self.assertRaises(StandardError, adm2.save)
#         # Everything is OK if no adm1 is set
#         adm3 = Admin2Code(geonameid=12, code="a2c8", name="a2c8 name", country=self.country1)
#         adm3.save()
# 
#     def test_change_adm2_name(self):
#         # The long_name of the countries change if we change the name of their adm2
#         self.assertEqual(u"Loc1, a2c1 name, a1c1 name", self.locality1.long_name)
#         self.admin2code1.name = "another adm2 name"
#         self.admin2code1.save()
#         self.locality1 = Locality.objects.get(pk=self.locality1.geonameid)
#         self.assertEqual(u"Loc1, another adm2 name, a1c1 name", self.locality1.long_name)
# 
#     def test_save_locations(self):
#         # Cannot be duplicated long names
#         self.assertRaisesMessage(StandardError, "Duplicated locality long name 'Loc1, a2c1 name, a1c1 name'", Locality.objects.create, geonameid=1300, name="Loc1", country=self.country1, admin1=self.admin1code1, admin2=self.admin2code1, timezone=self.tz1, population=1, lat=1, lon=1, modification_date="2012-1-1")
#         # Check country and adm zones consistency
#         self.assertRaisesMessage(StandardError, "The country 'Country2' from the Admin1 'a1c3 name, Country2' is different than the country 'Country1' from the locality 'Loc1, a2c1 name, a1c3 name'", Locality.objects.create, geonameid=1300, name="Loc1", country=self.country1, admin1=self.admin1code3, admin2=self.admin2code1, timezone=self.tz1, population=1, lat=1, lon=1, modification_date="2012-1-1")
#         self.assertRaisesMessage(StandardError, "The country 'Country2' from the Admin2 'a2c5 name, a1c3 name, Country2' is different than the country 'Country1' from the locality 'Loc1, a2c5 name, a1c1 name'", Locality.objects.create, geonameid=1300, name="Loc1", country=self.country1, admin1=self.admin1code1, admin2=self.admin2code5, timezone=self.tz1, population=1, lat=1, lon=1, modification_date="2012-1-1")
# 
#     def test_localities_deleted(self):
#         locality = Locality.objects.create(geonameid=1300, name="Loc1_deleted", country=self.country1, admin1=self.admin1code1, admin2=self.admin2code1, timezone=self.tz1, population=1, lat=1, lon=1, modification_date="2012-1-1", deleted=True)
#         all_localitites = Locality.objects.all()
#         self.assertEqual(all_localitites.count(), 3)
#         self.assertNotIn(locality, all_localitites)
#         all_w_deleted = Locality.objects_deleted_inc.all()
#         self.assertEqual(all_w_deleted.count(), 4)
# 
#     def test_locality_search(self):
#         # Search by name
#         result = self.country1.search_locality("Loc1")
#         self.assertIn(self.locality1, result)
#         self.assertEquals(1, result.count())
# 
#         # Search by alternate name
#         result = self.country1.search_locality("Loc1 alt")
#         self.assertIn(self.locality1, result)
#         self.assertEquals(1, result.count())
# 
#         # The search is only in the cities of the country
#         locality = Locality.objects.create(geonameid=1300, name="Loc1", country=self.country2, admin1=self.admin1code3, admin2=self.admin2code5, timezone=self.tz1, population=1, lat=1, lon=1, modification_date="2012-1-1")
#         result = self.country1.search_locality("Loc1")
#         self.assertIn(self.locality1, result)
#         self.assertNotIn(locality, result)
# 
#     def test_gis(self):
#         # Three localities set in a diagonal, dist(l1, l2)=20 and dist(l1,l3)=21
#         # So if we filter locations at 20 mi from l1, only l1 and l2 will be fetched
#         l1 = Locality.objects.create(geonameid=13001, name="Loc1_gis", country=self.country1, admin1=self.admin1code1, admin2=self.admin2code1, timezone=self.tz1, population=1, lat=57.15, lon=-2.10, modification_date="2012-1-1")
#         l2 = Locality.objects.create(geonameid=13002, name="Loc2_gis", country=self.country2, admin1=self.admin1code3, admin2=self.admin2code5, timezone=self.tz1, population=1, lat=57.32, lon=-2.53, modification_date="2012-1-1")
#         l3 = Locality.objects.create(geonameid=13003, name="Loc3_gis", country=self.country2, admin1=self.admin1code3, admin2=self.admin2code5, timezone=self.tz1, population=1, lat=57.33, lon=-2.54, modification_date="2012-1-1")
#         near_localities = l1.near_localities(20)
#         self.assertIn(l1.geonameid, near_localities)
#         self.assertIn(l2.geonameid, near_localities)
#         self.assertNotIn(l3.geonameid, near_localities)
