from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt  
import redis
import requests
import datetime
import json
from django.conf import settings
from django.core import serializers
from celery.task import task

redis_instance = redis.StrictRedis(host='localhost',
                                  port='6379', db=0)

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


@task
def get_direction_task(fly_from, fly_to):
	res = {}
	flights = redis_instance.hgetall(fly_from + '+' + fly_to).items()
	for key, value in flights:
		res[key.decode()] = value.decode()
	return res


@task
def check_flights_task():
	for fly_from, fly_to in directions:
		flights = redis_instance.hgetall(fly_from + '+' + fly_to).items()
		for departure_date, token in flights:
			flight = {}
			for key, value in redis_instance.hgetall(token.decode()).items():
				flight[key.decode()] = value.decode()
			if 'flights_invalid' in flight and flight['flights_invalid'] == '0':
				check_flight(token)


@task
def check_flight(token):
	link = "https://booking-api.skypicker.com/api/v0.1/check_flights"
	params = {
        'v': 2,
        'booking_token': token,
        'bnum': 1,
        'pnum': 1,
        'affily':'picky_us',
        'adults': 1
    }
	r = requests.get(link, params=params)
	data = json.loads(r.text)

	flights_invalid = data.get('flights_invalid')
	flights_checked = data.get('flights_checked')
	price = data.get('total')
	redis_instance.hset(token, "flights_invalid", '1' if flights_invalid else '0')
	redis_instance.hset(token, "flights_checked", '1' if flights_checked else '0')
	redis_instance.hset(token, "price", price)


@task
def get_direction_flights_task(fly_from, fly_to):
	res = []
	flights = redis_instance.hgetall(fly_from + '+' + fly_to).items()
	for departure_date, token in flights:
		flight = {}
		for key, value in redis_instance.hgetall(token.decode()).items():
			flight[key.decode()] = value.decode()
		res.append({token.decode(): flight})

	return res


@task
def update_cache_task():
	for fly_from, fly_to in directions:
		update_direction_flights(fly_from, fly_to)


@task
def update_direction_flights(fly_from, fly_to):
	link = "https://api.skypicker.com/flights"
	date_from = datetime.date.today().strftime("%d/%m/%Y")
	date_to = (datetime.date.today() + datetime.timedelta(days=30)).strftime("%d/%m/%Y")
	flights = json.loads(requests.get(link, params={
        'partner': 'picky',
        'fly_from': fly_from,
        'fly_to': fly_to,
        'date_from': date_from,
        'date_to': date_to,
        'one_per_date': 1
    }).text).get('data')

	date_ht = {}
	for flight in flights:
		departure_date = datetime.datetime.fromtimestamp(flight.get('dTime')).strftime("%d/%m/%Y")
		token = flight.get('booking_token')
		price = flight.get('price')
		date_ht[departure_date] = token
		redis_instance.hmset(token, {
            "fly_from": fly_from,
            "fly_to": fly_to,
            "date": str(departure_date),
            "price": price,
            "flights_checked": '0',
            "flights_invalid": '0'
    	})
	redis_instance.hmset(fly_from + '+' + fly_to, date_ht)


