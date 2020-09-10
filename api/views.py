from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt  
import redis
import requests
import datetime
import json
from django.conf import settings
from django.core import serializers
from .tasks import get_direction_task, check_flights_task, get_direction_flights_task, update_cache_task

redis_instance = redis.StrictRedis(host=settings.REDIS_HOST,
                                  port=settings.REDIS_PORT, db=0)

directions = [
    ['ALA', 'TSE'],
    ['TSE', 'ALA'],
    ['ALA', 'MOW'],
    ['MOW', 'ALA'],
    ['ALA', 'CIT'],
    ['CIT', 'ALA'],
    ['TSE', 'MOW'],
    ['MOW', 'TSE'],
    ['TSE', 'LED'],
    ['LED', 'TSE']
]



@csrf_exempt
def get_direction(request):
	fly_from, fly_to = request.GET['fly_from'], request.GET['fly_to']
	res = get_direction_task(fly_from, fly_to )
	return JsonResponse({'flights': res}, safe=False)


@csrf_exempt
def check_flights(request):
	check_flights_task()
	return JsonResponse({'res': 'success'}, safe=False)


@csrf_exempt
def get_direction_flights(request):
	fly_from, fly_to = request.GET['fly_from'], request.GET['fly_to']
	res = get_direction_flights_task(fly_from, fly_to)
	return JsonResponse({'flights': res}, safe=False)


@csrf_exempt
def update_cache(request):
	update_cache_task()
	return JsonResponse({'result': 'cache successfully updated'}, safe=False)


