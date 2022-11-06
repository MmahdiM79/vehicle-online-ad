from typing import Type
from hashlib import sha256

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
