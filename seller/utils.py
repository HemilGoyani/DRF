import json
import os

import requests
from rest_framework.pagination import PageNumberPagination

from seller.models import MyFCMDevice


def fcm_update(registration_id, device_id, type, user, user_type):
    device_data = MyFCMDevice.objects.filter(
        user=user, device_id=device_id, user_type=user_type
    )
    device = device_data.first()
    if device:
        device_data.update(registration_id=registration_id, type=type, user=user)
    else:
        MyFCMDevice.objects.create(
            device_id=device_id,
            registration_id=registration_id,
            type=type,
            user=user,
            user_type=user_type,
        )


def push_notification(request=None, notification_data=None, user=None, send_to="BUYER"):
    serverToken = (
        os.getenv("FCM_SERVER_KEY_SELLER")
        if "SELLER" == send_to
        else os.getenv("FCM_SERVER_KEY_BUYER")
    )

    if serverToken:
        if user:
            devices = (
                MyFCMDevice.objects.filter(user=user, user_type=send_to)
                .order_by("device_id", "-id")
                .distinct("device_id")
            )
        else:
            devices = MyFCMDevice.objects.order_by("device_id", "-id").distinct(
                "device_id"
            )

        device_token_list = (
            devices.exclude(registration_id__isnull=True)
            .exclude(registration_id="null")
            .values_list("registration_id", flat=True)
        )
        device_token_list = list(set(device_token_list))

        def divide_chunks(l, n):
            for i in range(0, len(l), n):
                yield l[i : i + n]

        deviceTokenList = list(divide_chunks(device_token_list, 900))

        headers = {
            "Content-Type": "application/json",
            "Authorization": "key=" + serverToken,
        }
        response_data = []
        for fcm_token_list in deviceTokenList:
            body = {
                "content_available": True,
                "mutable_content": True,
                "notification": notification_data,
                "registration_ids": fcm_token_list,
                "priority": "high",
                "data": notification_data,
            }
            response = requests.post(
                "https://fcm.googleapis.com/fcm/send",
                headers=headers,
                data=json.dumps(body),
            )
            print(f"Push notification success: {response.content}")
            response_data.append(json.loads(response.content.decode()))
        return response_data


class PaginationClass(PageNumberPagination):
    page_size = 20
