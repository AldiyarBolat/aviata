from __future__ import absolute_import, unicode_literals

from celery import Celery


celery = Celery()
celery.config_from_object('celeryconfig')