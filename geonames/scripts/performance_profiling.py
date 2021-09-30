from geonames.models import Country
import datetime

MAX_LOCATIONS = 500


def profile_search_location(country):
    # Normal search
    start_time = datetime.datetime.now()
    for loc in country.locations.values('name')[:MAX_LOCATIONS]:
        size = country.search_location(loc['name']).count()

    return datetime.datetime.now() - start_time


def profile_near_locations_rough(country, distance):
    # Normal search
    start_time = datetime.datetime.now()
    for loc in country.locations.all()[:MAX_LOCATIONS]:
        size = loc.near_locations_rough(distance).count()

    return datetime.datetime.now() - start_time


def profile_near_locations_nogis(country, distance):
    # Normal search
    start_time = datetime.datetime.now()
    for loc in country.locations.all()[:MAX_LOCATIONS]:
        size = len(loc.near_locations_nogis(distance))

    return datetime.datetime.now() - start_time


def profile_near_locations_gis(country, distance):
    # Normal search
    start_time = datetime.datetime.now()
    for loc in country.locations.all()[:MAX_LOCATIONS]:
        size = len(loc.near_locations_gis(distance))

    return datetime.datetime.now() - start_time

if __name__ == "__main__":
    # Name search
    country = Country.objects.get(code="GB")
    time = profile_search_location(country)
    print(f'Locations search completed in {time} for all the locations in {country}')

    # Distances
    country = Country.objects.get(code="GB")
    distance = 200

    time = profile_near_locations_rough(country, distance)
    print(f'Near locations rough search completed in {time} for cities in {country} at {distance} miles')

    time = profile_near_locations_nogis(country, distance)
    print(f'Near locations NO GIS search completed in {time} for cities in {country} at {distance} miles')

    time = profile_near_locations_gis(country, distance)
    print(f'Near locations with GIS search completed in {time} for cities in {country} at {distance} miles')
