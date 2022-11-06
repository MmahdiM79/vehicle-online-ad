from django.http.response import HttpResponse
from django.views.decorators.http import require_http_methods
from apis.clients import object_storage

# Create your views here.

@require_http_methods(["POST"])
def new_vehicle_ad(request):
    try:
        __check_keys(request)
        __check_image_file(request)
        
        object_storage.put(
            path=request.FILES['image'].name,
            file=request.FILES['image']
        )

        return HttpResponse(status=200)
        
    except Exception as e:
        return HttpResponse(f"Error: {e}", status=500)



def __check_keys(request):
    keys = ['description', 'email']
    for key in keys:
        if key not in request.POST:
            raise Exception(f"Missing key: {key}")
      
def __check_image_file(request):
    if 'image' not in request.FILES or request.FILES['image'] is None:
        raise Exception("Missing image file")
