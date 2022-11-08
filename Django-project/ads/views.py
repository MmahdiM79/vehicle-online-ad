from django.http.response import HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

from .models import VehicleAD
from apis.clients import (
    object_storage,
    rabbitmq
)

# Create your views here.

@csrf_exempt
@require_http_methods(["POST"])
def new_vehicle_ad(request):
    try:
        __check_keys(request)
        __check_image_file(request)
        
        path = object_storage.put(
            path=request.FILES['image'].name,
            file=request.FILES['image'].read(),
            hash_path=True
        )
        
        new_ad = VehicleAD()
        new_ad.image = path
        new_ad.email = request.POST['email']
        new_ad.description = request.POST['description']
        new_ad.save()
        
        rabbitmq.put(str(new_ad.pk))

        return HttpResponse(status=200)
        
    except Exception as e:
        return HttpResponse(f"Error: {e}", status=500)



def __check_keys(request):
    keys = ['description', 'email']
    for key in keys:
        if key not in request.POST:
            raise Exception(f"Missing key: {key}")
    
    if '@' not in request.POST['email'] or '.' not in request.POST['email']:
        raise Exception("Invalid email") 
    

def __check_image_file(request):
    if 'image' not in request.FILES or request.FILES['image'] is None:
        raise Exception("Missing image file")
