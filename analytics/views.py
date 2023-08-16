from django.shortcuts import render

from rest_framework import viewsets, mixins

from chat.models import Message, Customer, Chat

# Create your views here.


class DashBoardViewSet(viewsets.GenericViewSet):
    pass
