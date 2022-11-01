import boto3
import botocore
import logging
from typing import Type

from django.conf import settings

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

    def put(self, path: str, file: bytes, acl: str = settings.AWS_DEFAULT_ACL) -> str:
        if file is None:
            raise ValueError("file must be provided")

        try:
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


ObjectStorage = Type[_ObjectStorageClient]

object_storage = _ObjectStorageClient(
    key=settings.AWS_ACCESS_KEY_ID,
    secret=settings.AWS_SECRET_ACCESS_KEY,
    bucket=settings.AWS_STORAGE_BUCKET_NAME,
    url=settings.AWS_S3_ENDPOINT_URL
)
