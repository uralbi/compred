import json, requests
from django.utils.deprecation import MiddlewareMixin
from django.core.exceptions import PermissionDenied
from django.conf import settings

def writer(word):
    with open('allowedips.txt', 'a') as file:
        file.write(word + '\n')

def reader():
    try:
        with open('allowedips.txt', 'r') as file:
            for line in file:
                print(line)
                yield line.strip()
    except Exception as e:
        print(e)
        return None
 
            
class FilterRequestsMiddleware(MiddlewareMixin):
    
    def process_request(self, request):
        if settings.DEBUG:
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(',')[0].strip()
            else:
                ip_address = request.META.get('REMOTE_ADDR')
            
            for archive in reader():
                if ip_address in archive:
                    return None
                
            city = self.get_city_from_ip(ip_address)
            allowed_cities = ['bishkek', 'osh', 'kara-kol', 'cholpon-ata', 'kemin']
            
            if city.lower() in allowed_cities:
                writer(ip_address)
                return None
            else:
                raise PermissionDenied
            
        return None


    def process_response(self, request, response):
                
        return response

    def get_city_from_ip(self, ip_address):
        url = f'https://ip.city/?ip={ip_address}'
        response = requests.get(url)
        dec_response = response.content.decode('utf-8')
        
        idx = dec_response.find('Your city is detected as')
        res1 = dec_response[idx+25:]
        idx2 = res1.find('based on your IP address')
        city = res1[:idx2].strip()
        if city:
            return city
        else:
            return 'undef'