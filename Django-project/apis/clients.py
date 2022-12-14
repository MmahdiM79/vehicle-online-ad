from typing import Type
from hashlib import sha256
from requests import request

import boto3
import botocore
import logging
import pika

from django.conf import settings
from django.utils import timezone


logger = logging.getLogger(__name__)


class _ObjectStorageClient:
    def __init__(self, key: str, secret: str, bucket: str, url: str) -> None:
        self._url = url
        self._bucket = bucket
        try:
            self._resource = boto3.resource(
                's3',
                endpoint_url=url,
                aws_access_key_id=key,
                aws_secret_access_key=secret,
            )
        except ValueError as e:
            logger.warning(e)
            raise e

    def put(
            self, 
            path: str, 
            file: bytes, 
            acl: str = settings.AWS_DEFAULT_ACL, 
            hash_path: bool=False
        ) -> str:
        
        if file is None:
            raise ValueError("file must be provided")

        try:
            if hash_path:
                path = self.__hash_path(path)

            self._resource.Bucket(self._bucket).put_object(
                ACL=acl,
                Body=file,
                Key=path,
            )
            return settings.AWS_S3_GET_URL + path
        except botocore.exceptions.EndpointConnectionError as e:
            logger.critical(e)
            raise ConnectionError("Connection to storage failed")
        except botocore.exceptions.ParamValidationError as e:
            logger.critical(e)
            raise ValueError("Invalid parameters. file must be <class \'bytes\'>. others must be <class \'str\'>")

    def delete(self, path: str) -> None:
        try:
            bucket = self._resource.Bucket(self._bucket)
            obj = bucket.Object(path)
            obj.delete()
        except botocore.exceptions.ClientError as e:
            logger.warning(e)
            raise e

    def is_object_available(self, path: str) -> bool:
        try:
            self._resource.Object(self._bucket, path).load()
            return True
        except botocore.exceptions.ClientError as e:
            logger.critical(e)
            return False
    
    def __hash_path(self, path: str) -> str:
        fname, ftype = path.rsplit('.')
        fname_hash = sha256(f'{timezone.now()}_{fname}'.encode('utf-8')).hexdigest()
        return fname_hash + f'.{ftype}'


class _RabbitMQClient:
    def __init__(self, amqp_url: str, queue_name: str) -> None:
        self._amqp_url = amqp_url
        self._connection = pika.BlockingConnection(pika.URLParameters(amqp_url))
        
        self._channel = self._connection.channel()
        self._queue_name = queue_name
        self._channel.queue_declare(queue=self._queue_name)
        
    def put(self, data: str) -> None:
        self._channel.basic_publish(
            exchange='',
            routing_key=self._queue_name,
            body=data
        )
    
    def pop(self) -> str:
        method_frame, header_frame, body = self._channel.basic_get(queue=self._queue_name)
        if method_frame:
            self._channel.basic_ack(method_frame.delivery_tag)
            return body.decode('utf-8')
        else:
            return ''


class _ImaggaClient:
    def __init__(self, api_key: str, api_secret: str) -> None:
        self._api_key = api_key
        self._api_secret = api_secret

    def get_tags(self, image_url: str, threshold: float = 49) -> dict:
        response = request(
            method='GET',
            url='https://api.imagga.com/v2/tags',
            params={
                'image_url': image_url,
                'threshold': threshold,
            },
            auth=(self._api_key, self._api_secret)
        )
        json_result = response.json()
        if json_result['status']['type'] == 'error':
            raise ValueError(json_result['status']['text'])

        return json_result


class _MailgunClient:
    def __init__(self, api_key: str, domain: str) -> None:
        self._api_key = api_key
        self._domain = domain

    def send(self, to: str, subject: str, text: str) -> None:
        request(
            method='POST',
            url=f'https://api.mailgun.net/v3/{self._domain}/messages',
            auth=('api', self._api_key),
            data={
                'from': f'no-reply@{self._domain}',
                'to': to,
                'subject': subject,
                'text': text,
            }
        )

    def send_received_ad_message(self, to: str) -> None:
        get_added_mail_text = f"""\
        Hi there,

        Thank you for posting your vehicle ad on our website.
        We have received your ad. It will be reviewed by our team.
        We will notify you when your ad is accepted or rejected.

        Best regards,
        The team at {settings.BASE_URL}
        """
        self.send(
            to=to,
            subject='Your ad has been received',
            text=get_added_mail_text
        )

    def send_success_message(self, to: str, ad_id: int) -> None:
        success_mail_text = f"""\
        Hi there,

        Thank you for posting your vehicle ad on our website.
        Your ad has been accepted and is now live on our website.
        You can find it here: {settings.BASE_URL}/vehicle/ads/{ad_id}

        Best regards,
        The team at {settings.BASE_URL}.

        """
        self.send(
            to=to,
            subject='Your ad has been created',
            text=success_mail_text
        )
        
    def send_failure_message(self, to: str) -> None:
        failure_mail_text = f"""\
        Hi there,

        Thank you for posting your vehicle ad on our website.
        Unfortunately, your ad has been rejected.
        This is because the image you uploaded did not contain any vehicle.
        check the image and try again.

        Best regards,
        The team at {settings.BASE_URL}.

        """
        self.send(
            to=to,
            subject='Your ad has been rejected',
            text=failure_mail_text
        )



ObjectStorage = Type[_ObjectStorageClient]
object_storage = _ObjectStorageClient(
    key=settings.AWS_ACCESS_KEY_ID,
    secret=settings.AWS_SECRET_ACCESS_KEY,
    bucket=settings.AWS_STORAGE_BUCKET_NAME,
    url=settings.AWS_S3_ENDPOINT_URL
)

RabbitMQClient = Type[_RabbitMQClient]
rabbitmq = _RabbitMQClient(
    amqp_url=settings.RABBITMQ_AMQP_URL,
    queue_name=settings.RABBITMQ_QUEUE_NAME
)

ImaggaClient = Type[_ImaggaClient]
imagga_client = _ImaggaClient(
    api_key=settings.IMAGGA_API_KEY,
    api_secret=settings.IMAGGA_API_SECRET
)

MailgunClient = Type[_MailgunClient]
email_client = _MailgunClient(
    api_key=settings.MAILGUN_API_KEY,
    domain=settings.MAILGUN_DOMAIN_NAME
)
