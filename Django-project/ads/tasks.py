from time import sleep
from celery import shared_task

from ads.models import VehicleAD
from apis.clients import (
    rabbitmq,
    imagga_client,
    email_client
)

from django.conf import settings


                
@shared_task
def validate_ad() -> None:
    while True:
        print("waiting for new ads")
        ad_id = rabbitmq.pop()
        if ad_id == '':
            print("no new ads")
            break
        
        ad_id = int(ad_id)
        print(f"validating ad with id: {ad_id}")
        ad = VehicleAD.objects.get(pk=ad_id)
        
        print(f"add image url: {ad.image}")
        try:
            result = imagga_client.get_tags(ad.image)
            print(f"imagga result for ad with id: {ad_id} is: {result}")
        except ValueError as e:
            print(f"imagga error for ad with id: {ad_id} is: {e}")
            ad.status = VehicleAD.REJECTED
            ad.save()
            continue

        for tag in result['result']['tags']:
            if tag['tag']['en'] in settings.VALID_CATEGORIES:
                ad.state = VehicleAD.StateAD.ACCEPTED
                ad.category = tag['tag']['en']
                ad.save()
                email_client.send_success_message(ad.email, ad.pk)
                print(f"ad with id: {ad_id} is accepted")
                break
        else:
            ad.state = VehicleAD.StateAD.REJECTED
            ad.category = None
            email_client.send_failure_message(ad.email, ad.pk)
            print(f"ad with id: {ad_id} is rejected")
            ad.save()

