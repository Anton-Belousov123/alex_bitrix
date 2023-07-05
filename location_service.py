from geopy.geocoders import Nominatim

def get_address(lat, lon):
    geolocator = Nominatim(user_agent="testing_olegpash")
    print(lat, lon)
    location = geolocator.reverse(f'{lat}, {lon}')
    return location.address

