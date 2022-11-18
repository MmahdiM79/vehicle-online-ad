from typing import Any, Dict, List, Optional

import logging

from django.db import models
from django.http import JsonResponse
from django.db.models.query import QuerySet

from apis.constants import HttpStatusCodes




class ApiResponse(object):
    def __init__(
        self,
        success: bool = True,
        messages: List[str] = None,
        data: Dict[str, Any] = None,
        status_code: int = 200
    ):
        self.status_code = status_code
        self.success = success
        self.messages = messages if messages is not None else []
        self.data = data if data is not None else dict()


    @property
    def status_code(self) -> int:
        return self.__status_code


    @status_code.setter
    def status_code(self, status_code: int) -> None:
        if not ApiResponse.is_status_code_ok(status_code):
            print(f'Invalid status_code: {status_code}')
            raise ValueError(
                'Invalid status code. check utils.vars.HTTP_STATUS_CODES')
        self.__status_code = status_code


    @property
    def success(self) -> bool:
        return self.__success


    @success.setter
    def success(self, success: bool) -> None:
        if not ApiResponse.is_success_ok(success):
            print(f'Invalid success: {success}')
            raise ValueError(
                'Invalid success value. your value must be True or False')
        self.__success = success


    @property
    def messages(self) -> List[str]:
        return self.__messages


    @messages.setter
    def messages(self, messages: List[str]) -> None:
        if not ApiResponse.is_messages_ok(messages):
            print(f'Invalid messages: {messages}')
            raise ValueError(
                'Invalid messages value. your value must be a list of strings')
        self.__messages = messages


    @property
    def data(self) -> Dict[str, Any]:
        return self.__data


    @data.setter
    def data(self, data: Dict[str, Any]) -> None:
        if not ApiResponse.is_data_ok(data):
            print(f'Invalid data: {data}')
            raise ValueError(
                'Invalid body value. your value must be a Dict[str, Any]')
        self.__data = data


    def response(self) -> JsonResponse:
        if not self.__is_valid():
            print(f'Invalid ApiResponse: {self}')
            raise ValueError(\
                'Invalid ApiResponse object.\
                check success, messages, data and status_code.\
                ApiResponse.is... functions may help you.'
            )

        data = {
            'success': self.success,
            'messages': self.messages,
            'data': self.data
        }
        return JsonResponse(data=data, status=self.status_code)


    def __is_valid(self) -> bool:
        cond1 = ApiResponse.is_status_code_ok(self.status_code)
        cond2 = ApiResponse.is_messages_ok(self.messages)
        cond3 = ApiResponse.is_data_ok(self.data)
        cond4 = ApiResponse.is_success_ok(self.success)
        return cond1 and cond2 and cond3 and cond4


    @staticmethod
    def is_status_code_ok(status_code: int) -> bool:
        if not isinstance(status_code, int):
            return False
        return HttpStatusCodes.is_status_code_ok(status_code)


    @staticmethod
    def is_messages_ok(messages: List[str]) -> bool:
        if not isinstance(messages, list):
            return False
        cond1 = type(messages) is not list
        cond2 = any(type(message) is not str for message in messages)
        return not (cond1 or cond2)


    @staticmethod
    def is_data_ok(data: Dict[str, Any]) -> bool:
        if not isinstance(data, dict):
            return False
        cond1 = type(data) is not dict
        cond2 = any(type(key) is not str for key in data.keys())
        return not (cond1 or cond2)


    @staticmethod
    def is_success_ok(success: bool) -> bool:
        return success in [True, False]


    @staticmethod
    def response_from_objects(
        key: str,
        objects: models.Model | QuerySet,
        include: Optional[List[str] | None] = None,
        exclude: Optional[List[str] | None] = None,
        additional_methods: Optional[List[str] | None] = None,
        status_code: int = 200,
        success: bool = True,
        messages: List[str] = None
    ) -> JsonResponse:
        if include is not None and exclude is not None:
            ApiResponse.__raise(
                Exception('only one of the "include" or "exclude" must be given.'))

        ApiResponse.__check_given_fields(include)
        ApiResponse.__check_given_fields(exclude)
        ApiResponse.__check_given_objects(objects)

        r = ApiResponse(status_code=status_code,
                        success=success, messages=messages)

        if isinstance(objects, models.base.Model):
            r.data = {key: ApiResponse.__object_serializer(
                objects, include, exclude)}
            if additional_methods:
                r.data[key].update(ApiResponse.__additional_methods_to_dict(
                    objects, additional_methods))
            return r.response()
        else:
            data = {key: []}
            for obj in objects:
                temp = ApiResponse.__object_serializer(obj, include, exclude)
                if additional_methods:
                    temp.update(ApiResponse.__additional_methods_to_dict(
                        obj, additional_methods))
                data[key].append(temp)

            r.data = data
            return r.response()


    @staticmethod
    def __object_serializer(
        objects: models.base.Model,
        include: Optional[List[str] | None] = None,
        exclude: Optional[List[str] | None] = None,
    ) -> Dict[str, Any]:
        ApiResponse.__check_given_fields(include)
        ApiResponse.__check_given_fields(exclude)
        ApiResponse.__check_given_objects(objects)

        out = ApiResponse.__to_dict(objects)

        if exclude:
            out = ApiResponse.__exclude(objects, out, exclude)
        if include:
            out = ApiResponse.__include(objects, out, include)

        return out


    @staticmethod
    def __to_dict(obj: models.Model) -> Dict[str, Any]:
        ApiResponse.__check_given_objects(obj)

        out = obj.__dict__.copy()
        del out['_state']

        for key in list(out.keys()):
            if '_id' in key:
                key = key.replace('_id', '')
                temp = obj.__getattribute__(key)
                out[key] = ApiResponse.__to_dict(temp)
                del out[key+'_id']

        return out


    @staticmethod
    def __check_given_objects(objects) -> None:
        cond1 = isinstance(objects, models.base.Model)
        cond2 = isinstance(objects, QuerySet)
        if not (cond1 or cond2):
            ApiResponse.__raise(ValueError(
                'objects must be a django.db.models.Model or QuerySet'))


    @staticmethod
    def __check_given_fields(fields) -> None:
        if fields is not None:
            if not isinstance(fields, list):
                ApiResponse.__raise(ValueError('fields must be a list.'))
            for item in fields:
                if not isinstance(item, str):
                    ApiResponse.__raise(ValueError(
                        'fields must be a list of strings.'))


    @staticmethod
    def __include(o: models.base.Model, d: dict, fields: List[str]) -> dict:
        ApiResponse.__check_field_valid(o, list(d.keys()), fields)

        for key in list(d.keys()):
            if key not in fields:
                del d[key]

        return ApiResponse.__extract_foreign_models_fields(o, d, fields)


    @staticmethod
    def __exclude(o: models.base.Model, d: dict, fields: List[str]) -> dict:
        ApiResponse.__check_field_valid(o, list(d.keys()), fields)

        for key in fields:
            if key in d:
                del d[key]

        return ApiResponse.__extract_foreign_models_fields(o, d, fields)


    @staticmethod
    def __extract_foreign_models_fields(o: models.base.Model, d: dict, fields: List[str]) -> dict:
        foreign_models = set([f.split('__')[0] for f in fields if '__' in f])
        for model in foreign_models:
            foreign_model_fields = [
                f.partition('__')[2] for f in fields if f.startswith(model+'__')
            ]
            d[model] = ApiResponse.__object_serializer(
                o.__getattribute__(model),
                exclude=foreign_model_fields
            )
        return d


    @staticmethod
    def __check_field_valid(obj: models.base.Model, obj_fields: List[str], fields: List[str]) -> bool:
        for f in fields:
            if '__' not in f and f not in obj_fields:
                ApiResponse.__raise(ValueError(
                    f'{type(obj)} has no field "{f}"'))


    @staticmethod
    def __additional_methods_to_dict(obj: models.base.Model, additional_methods: List[str]) -> Dict[str, Any]:
        out = {}
        for method in additional_methods:
            attr = getattr(obj, method)
            if callable(attr):
                out[method] = attr()
            else:
                out[method] = attr
        return out


    @staticmethod
    def __raise(e: Exception) -> None:
        logging.error(e)
        raise e


    def __str__(self) -> str:
        return f"'success': {self.success}, 'messages': {self.messages}, 'data': {self.data}"


    def __eq__(self, __o: object) -> bool:
        if type(__o) is not ApiResponse:
            return False
        return self.__dict__ == __o.__dict__