import datetime
from itertools import count
import json
import os
import pathlib
import re
import string
import threading
import zipfile
from django.conf import settings
from django.db.models import Count, Max
from django.contrib import messages
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.html import strip_tags
from django.views.decorators.csrf import csrf_exempt
from .models import *
import requests

from tablib import Dataset
import xlwt
import random
import pytz
from django.core.files.storage import FileSystemStorage
from PIL import Image
from django import db
from django.db.models import CharField
from django.db.models.functions import Length

CharField.register_lookup(Length, 'length')

for con in db.connections:
    print("Databases connections..........",con)

try:
    APP_Setting.objects.create(key="EMAIL_USE_TLS", value="True")
    APP_Setting.objects.create(key="EMAIL_HOST",value = 'smtp.gmail.com')
    APP_Setting.objects.create(key="EMAIL_HOST_USER", value = 'societyfunds@gmail.com')
    APP_Setting.objects.create(key="EMAIL_HOST_PASSWORD ", value= 'ohkuqtqgbbcyloqq')
    APP_Setting.objects.create(key="EMAIL_PORT", value = 587)
    APP_Setting.objects.create(key="DEFAULT_FROM_EMAIL", value = "EMAIL_HOST_USER")
    APP_Setting.objects.create(key="USER_VALIDITY", value=7)
    APP_Setting.objects.create(key="BLOCK_NUMBER_LIMIT", value=7)
except:
    pass



# Create your views here.
def index(request):
    return render(request, "home.html")


def send_SMS(request):
    
    to = request.GET.get('to')
    text = request.GET.get('text')
    token = request.GET.get('token')
    user_id = Developers_token.objects.get(u_token=token).user_id
    if User1.objects.get(pk=user_id).is_active:  
        response = ""
        if len(to) == 10:
            to = "91" + to

        try:
            msg_provider = Developers_token.objects.get(u_token=token)
        except:
            return JsonResponse({"message": "Parameters are not valid."})

        wmp = WA_MSG_Provider.objects.get(id=msg_provider.message_provider_id)
        url_data = Voice_API.objects.get(whatsapp_name=wmp.provider_name)

        time_check = Conversation_Status.objects.filter(to=to, provider=wmp.provider_name)
        print(time_check)
        # After First time
        if time_check:
            lat_entry = time_check[len(time_check) - 1]
            
            if lat_entry.received_time and lat_entry.conversation_status == "Stopped":
                return JsonResponse({"message": "Your messages are blocked by user"})
            else:
                if (not lat_entry.received_time) or  (lat_entry.conversation_status == "Pending"):
                    t = Templates.objects.get(temp_name=msg_provider.template, lang_code=msg_provider.lang,
                                            message_provider_id=wmp.id)
                    print("Working Properly")
                    if t.is_media:
                        if t.med_id is None:
                            return JsonResponse({"message": "Please Upload media content first."})
                        else:
                            js = json.loads(t.med_id)
                            payload = json.dumps({
                                "messaging_product": "whatsapp",
                                "recipient_type": "individual",
                                "to": f"{to}",
                                "type": "template",
                                "template": {
                                    "name": f"{msg_provider.template}",
                                    "language": {
                                        "code": f"{msg_provider.lang}"
                                    },
                                    "components": [
                                        {
                                            "type": "header",
                                            "parameters": [
                                                {
                                                    "type": "image",
                                                    "image": {"link": f"{js['link']}"} if js["type"] == "what" else {
                                                        "id": f"{js['med_obj']}"}
                                                }
                                            ]
                                        }
                                    ]
                                }
                            })
                    else:
                        payload = json.dumps({
                            "messaging_product": "whatsapp",
                            "recipient_type": "individual",
                            "to": f"{to}",
                            "type": "template",
                            "template": {
                                "name": f"{msg_provider.template}",
                                "language": {
                                    "code": f"{msg_provider.lang}"
                                },

                            }
                        })

                    response = requests.request("POST", url_data.message_API, headers=url_data.header, data=payload)
                    try:
                        msgid = json.loads(response.text)['messages'][0]['id']
                        status = "sent"
                    except KeyError:
                        msgid, status = None, None
                    OutBox.objects.create(message=msg_provider.template,
                                            send_time=datetime.datetime.now(
                                                timezone.utc) + datetime.timedelta(
                                                hours=5.5),
                                            reply_number=wmp.provider_name, status=status, request=url_data.message_API,
                                            response=response.text, user_id=wmp.user_id, to_number=to, msg_id=msgid)
                    Message_History.objects.create(message=msg_provider.template, msg_type="send", customer_number=to, 
                                        api_number=wmp.phone_no, user_id=wmp.user_id,
                                        provider_id=wmp.id, msg_id=msgid)
                    OutBox.objects.create(message=text,
                                            send_time=datetime.datetime.now(
                                                timezone.utc) + datetime.timedelta(
                                                hours=5.5),
                                            reply_number=wmp.provider_name, status="in_queue", user_id=wmp.user_id,
                                            to_number=to)
                    con_stat = Conversation_Status.objects.get(to=to, provider=wmp.provider_name)
                    con_stat.inbox_msg = ""
                    con_stat.template = msg_provider.template
                    con_stat.send_time = datetime.datetime.now(timezone.utc) + datetime.timedelta(hours=5.5)
                    con_stat.received_time = None
                    con_stat.conversation_status = "Pending"
                    con_stat.save()

                else:
                    # if lat_entry.inbox_msg == "No" or lat_entry.inbox_msg == "":
                    #     OutBox.objects.create(message=text,
                    #                           send_time=datetime.datetime.now(
                    #                               timezone.utc) + datetime.timedelta(
                    #                               hours=5.5),
                    #                           reply_number=wmp.provider_name, status="in_queue", user_id=wmp.user_id,
                    #                           to_number=to)
                    #     return JsonResponse({"message": "Message added to queue"})
                    # else:
                    payload = json.dumps({
                        "messaging_product": "whatsapp",
                        "recipient_type": "individual",
                        "to": f"{to}",
                        "type": "text",
                        "text": {
                            "preview_url": False,
                            "body": f"{text}"
                        }
                    })
                    response = requests.request("POST", url_data.message_API, headers=url_data.header, data=payload)
                    try:
                        msgid = json.loads(response.text)['messages'][0]['id']
                    except KeyError:
                        msgid = ""
                    OutBox.objects.create(message=text,
                                            send_time=datetime.datetime.now(
                                                timezone.utc) + datetime.timedelta(
                                                hours=5.5), reply_number=wmp.provider_name,
                                            status="sent", request=url_data.message_API, response=response.text,
                                            user_id=wmp.user_id, to_number=to, msg_id=msgid)
                    Message_History.objects.create(message=text, msg_type="send", customer_number=to, 
                                        api_number=wmp.phone_no, user_id=wmp.user_id,
                                        provider_id=wmp.id, msg_id=msgid)
        # First Time API call
        else:
            t = Templates.objects.get(temp_name=msg_provider.template, lang_code=msg_provider.lang,
                                    message_provider_id=wmp.id)
            if t.is_media:
                if t.med_id is None:
                    return JsonResponse({"message": "Please Upload media content first."})
                else:
                    js = json.loads(t.med_id)
                    payload = json.dumps({
                        "messaging_product": "whatsapp",
                        "recipient_type": "individual",
                        "to": f"{to}",
                        "type": "template",
                        "template": {
                            "name": f"{msg_provider.template}",
                            "language": {
                                "code": f"{msg_provider.lang}"
                            },
                            "components": [
                                {
                                    "type": "header",
                                    "parameters": [
                                        {
                                            "type": "image",
                                            "image": {"link": f"{js['link']}"} if js["type"] == "what" else {
                                                "id": f"{js['med_obj']}"}
                                        }
                                    ]
                                }
                            ]
                        }
                    })
            else:
                payload = json.dumps({
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": f"{to}",
                    "type": "template",
                    "template": {
                        "name": f"{msg_provider.template}",
                        "language": {
                            "code": f"{msg_provider.lang}"
                        },

                    }
                })

            response = requests.request("POST", url_data.message_API, headers=url_data.header, data=payload)
            try:
                msgid = json.loads(response.text)['messages'][0]['id']
            except KeyError:
                msgid = ""
            OutBox.objects.create(message=msg_provider.template,
                                send_time=datetime.datetime.now(timezone.utc) + datetime.timedelta(
                                    hours=5.5),
                                reply_number=wmp.provider_name, status="sent", request=url_data.message_API,
                                response=response.text, user_id=wmp.user_id, to_number=to, msg_id=msgid)
            Message_History.objects.create(message=msg_provider.template, msg_type="send", customer_number=to, 
                                        api_number=wmp.phone_no, user_id=wmp.user_id,
                                        provider_id=wmp.id, msg_id=msgid)
            OutBox.objects.create(message=text,
                                send_time=datetime.datetime.now(timezone.utc) + datetime.timedelta(
                                    hours=5.5),
                                reply_number=wmp.provider_name, status="in_queue", user_id=wmp.user_id, to_number=to)
            Conversation_Status.objects.create(to=to, provider=wmp.provider_name, template=msg_provider.template,
                                            send_time=datetime.datetime.now(
                                                timezone.utc) + datetime.timedelta(
                                                hours=5.5), user_id_id=user_id)

        return JsonResponse(json.loads(response.text))
    else:
        return JsonResponse({"message":"User validity has been expired. Please recharge"})

def send_Template(request):
    to = request.GET.get('to')
    template = request.GET.get('temp')
    lang = request.GET.get('language')
    token = request.GET.get('token')
    if User1.objects.get(pk=Developers_token.objects.get(u_token=token).user_id).is_active:
        if to != "" and template != "" and lang != "" and token != "":
            if len(to) == 10:
                to = "91" + to

            msg_provider = Developers_token.objects.get(u_token=token)
            user = WA_MSG_Provider.objects.get(id=msg_provider.message_provider_id)
            url_data = Voice_API.objects.get(u_ID_id=user.user_id)

            time_check = MessageLog.objects.filter(sender_number=to, reply_number=user.phone_no)
            if time_check:
                lat_entry = time_check[len(time_check) - 1]
                this = datetime.datetime.now(timezone.utc) + datetime.timedelta(hours=5.5)

                if lat_entry.received_msg == "No":
                    OutBox.objects.create(to_number=to, reply_number=user.provider_name, response='No message',
                                        user_id=user.user_id)
                    return JsonResponse({"Message": "User unsubscribed"})

            t = Templates.objects.get(temp_name=template, lang_code=lang, message_provider_id=user.id)

            if t.is_media:
                if t.med_id is None:
                    return JsonResponse({"message": "Please Upload media content first."})
                else:
                    js = json.loads(t.med_id)
                    payload = json.dumps({
                        "messaging_product": "whatsapp",
                        "recipient_type": "individual",
                        "to": f"{to}",
                        "type": "template",
                        "template": {
                            "name": f"{template}",
                            "language": {
                                "code": f"{lang}"
                            },
                            "components": [
                                {
                                    "type": "header",
                                    "parameters": [
                                        {
                                            "type": "image",
                                            "image": {"link": f"{js['link']}"} if js["type"] == "what" else {
                                                "id": f"{js['med_obj']}"}
                                        }
                                    ]
                                }
                            ]
                        }
                    })
            else:
                payload = json.dumps({
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": f"{to}",
                    "type": "template",
                    "template": {
                        "name": f"{template}",
                        "language": {
                            "code": f"{lang}"
                        },

                    }
                })
            response = requests.request("POST", url_data.message_API, headers=url_data.header, data=payload)
            try:
                msgid = json.loads(response.text)['messages'][0]['id']
            except KeyError:
                msgid = ""
            OutBox.objects.create(message=msg_provider.template,
                                send_time=datetime.datetime.now(timezone.utc) + datetime.timedelta(
                                    hours=5.5),
                                reply_number=user.provider_name, status="sent", request=url_data.message_API,
                                response=response.text, user_id=user.user_id, to_number=to, msg_id=msgid)
            Message_History.objects.create(message=msg_provider.template, msg_type="send", customer_number=to, 
                                        api_number=user.phone_no, user_id=user.user_id,
                                        provider_id=user.id, msg_id=msgid)
            return JsonResponse(json.loads(response.text))
        else:
            return JsonResponse({"Message": "Required all params"})
    else:
        return JsonResponse({"message":"User validity has been expired. Please recharge"})

def send_matched_temps(token_data, to, msg):
    provider = WA_MSG_Provider.objects.get(id=token_data.message_provider_id)
    msg = msg.replace("  ", " ").replace("\n","")

    api = Voice_API.objects.get(whatsapp_name=provider.provider_name)
    all_temp = New_Templates.objects.filter(message_provider_id=token_data.message_provider_id)
    for a in all_temp:
        
        data = a.text_msg.replace("{#var#}", "(.*)")
        p = re.compile(data)
        
        variables = p.findall(msg+ " Thank you")
        
        if variables:
            # print(data)
            # print(msg+ " Thank you")
            # print(variables)
            print(a.temp_name, a.lang_code)
            payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": f"{to}",
            "type": "template",
            "template": {
                "name": f"{a.temp_name}",
                "language": {
                    "code": f"{a.lang_code}"
                },
                "components": [

                    ]
                }
            }
            
            payload["template"]["components"].append({
                "type": "body",
                "parameters": []
            })

            print(variables)
            to_save  = {}
            i = 1
            if type(variables[0]) is str:
                to_roam = variables
            elif type(variables[0]) is tuple:
                to_roam = variables[0]
            
            for v in to_roam:
                payload["template"]["components"][0]["parameters"].append({"type": "text", "text": f"{v}"})
                to_save[i] = v
                i += 1
            payload = json.dumps(payload)
            # print(payload)
            response = requests.request("POST", api.message_API, headers=api.header, data=payload)
            print(response.text)
            try:
                msgid = json.loads(response.text)['messages'][0]['id']
            except KeyError:
                msgid = ""
            print("Objects Crating .....................")
            OutBox.objects.create(message=a.temp_name,
                        send_time=datetime.datetime.now(timezone.utc) + datetime.timedelta(
                            hours=5.5),
                        reply_number=provider.provider_name, status="sent", request=api.message_API,
                        response=response.text, user_id=provider.user_id, to_number=to, msg_id=msgid, variables=to_save)
            Message_History.objects.create(message=a.temp_name, msg_type="send", customer_number=to, 
                            api_number=provider.phone_no, user_id=provider.user_id,
                            provider_id=provider.id, msg_id=msgid)
            
            return json.loads(response.text)
    MissMatched_Temps.objects.create(text_msg=msg, provider_id=token_data.message_provider_id, usr_id=token_data.user_id)
    return {"message":"Data not found"}


def getMisMatchedData(request):
    data = MissMatched_Temps.objects.filter(usr_id=request.COOKIES['id'])
    return render(request, "MissMatched.html", {"data":data})

def check_matched(token_data, to, msg):
    provider = WA_MSG_Provider.objects.get(id=token_data.message_provider_id)
    msg = regexpstring(msg, 0).replace("  "," ")
    api = Voice_API.objects.get(whatsapp_name=provider.provider_name)
    all_temp = New_Templates.objects.filter(message_provider_id=token_data.message_provider_id)
    for a in all_temp:
        
        data = regexpstring(a.text_msg, 1).replace("{#var#}", "(.*)")
        p = re.compile(data)
        
        variables = p.findall(msg)
        # print(data)
        # print(msg)
        
        if variables:
            # print(data)
            # print(msg)
            # print(variables)
            print(a.temp_name, a.lang_code)
            payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": f"{to}",
            "type": "template",
            "template": {
                "name": f"{a.temp_name}",
                "language": {
                    "code": f"{a.lang_code}"
                },
                "components": [

                    ]
                }
            }
            
            payload["template"]["components"].append({
                "type": "body",
                "parameters": []
            })

            to_save  = {}
            i = 1
            if type(variables[0]) is str:
                to_roam = variables
            elif type(variables[0]) is tuple:
                to_roam = variables[0]
            
            for v in to_roam:
                payload["template"]["components"][0]["parameters"].append({"type": "text", "text": f"{v}"})
                to_save[i] = v
                i += 1
            payload = json.dumps(payload)
            # print(payload)
            response = requests.request("POST", api.message_API, headers=api.header, data=payload)
            print(response.text)
            try:
                msgid = json.loads(response.text)['messages'][0]['id']
                status = "sent"
            except KeyError:
                msgid = None
                status = None
            OutBox.objects.create(message=a.temp_name,
                        send_time=datetime.datetime.now(timezone.utc) + datetime.timedelta(
                            hours=5.5),
                        reply_number=provider.provider_name, status=status, request=api.message_API,
                        response=response.text, user_id=provider.user_id, to_number=to, msg_id=msgid, variables=to_save)
            Message_History.objects.create(message=a.temp_name, msg_type="send", customer_number=to, 
                                        api_number=provider.phone_no, user_id=provider.user_id,
                                        provider_id=provider.id, msg_id=msgid)
            return json.loads(response.text)
    MissMatched_Temps.objects.create(text_msg=msg, provider_id=token_data.message_provider_id, usr_id=token_data.user_id)
    return {"message":"Data not found"}

@csrf_exempt
def send_check(request):
    if request.method == "GET":
        to = request.GET.get('to')
        msg = request.GET.get('msg')
        token = request.GET.get('token')
        try:
            tk = Developers_token.objects.get(u_token=token)
        except Exception as e:
            return JsonResponse({"status":"error", "message": "Please create a valid token"})
        if User1.objects.get(pk=tk.user_id).is_active:
            if to != "" and msg != "" and token != "":
                if len(to) == 10:
                    to = "91" + to
                
                token_data = Developers_token.objects.get(u_token=token)
                msg_state = SMS_Settings.objects.get(usr_id=token_data.user_id)
                if msg_state.selective:
                    if "," not in msg_state.keywords:
                        to_check = msg_state.keywords.replace("['","").replace("']","").split(",")
                    
                    else:
                        ar = msg_state.keywords.split(",")
                        to_check = [x.replace("[","").replace("]","").replace("'","").strip() for x in ar]
                    print(to_check)

                    for i in to_check:
                        if i in msg:
                            print("Matched")
                            if msg_state.sel_whatsapp and msg_state.sel_sms:
                                response2 = check_matched(token_data, to=to, msg=msg)
                                url = msg_state.sms_url.replace("<mobile>", to).replace("<message>", msg)
                                s_response = requests.get(url).text
                                SMS_OutBox.objects.create(message=msg,
                                send_time=datetime.datetime.now(timezone.utc) + datetime.timedelta(hours=5.5),
                                status="sent", request=url,response=s_response, user_id=token_data.user_id, to_number=to)
                                return JsonResponse({"SMS":s_response, "whatsapp":response2}, safe=False)
                            if msg_state.sel_whatsapp:
                                response2 = check_matched(token_data, to=to, msg=msg)
                                s_response= ""
                                if (msg_state.sms or (("error" in response2) and response2["error"]["message"] == "(#100) Invalid parameter")) and msg_state.sms_url:
                                        url = msg_state.sms_url.replace("<mobile>", to).replace("<message>", msg)
                                        s_response = requests.get(url).text
                                        SMS_OutBox.objects.create(message=msg,
                                        send_time=datetime.datetime.now(timezone.utc) + datetime.timedelta(hours=5.5),
                                        status="sent", request=url,response=s_response, user_id=token_data.user_id, to_number=to)
                                return JsonResponse({"whatsapp":response2, "SMS":s_response}, safe=False)
                                
                            if msg_state.sel_sms:

                                url = msg_state.sms_url.replace("<mobile>", to).replace("<message>", msg)
                                s_response = requests.get(url).text
                                response2 = ""
                                SMS_OutBox.objects.create(message=msg,
                                    send_time=datetime.datetime.now(timezone.utc) + datetime.timedelta(hours=5.5),
                                    status="sent", request=url,response=s_response, user_id=token_data.user_id, to_number=to)
                                if msg_state.whatsapp:
                                    response2 = check_matched(token_data, to=to, msg=msg)
                                return JsonResponse({"SMS":s_response, "whatsapp":response2}, safe=False)
                    else:
                        pass
                if msg_state.both or (msg_state.sms and msg_state.whatsapp):
                    url = msg_state.sms_url.replace("<mobile>", to).replace("<message>", msg)
                    s_response = requests.get(url).text
                    OutBox.objects.create(message=msg,
                                send_time=datetime.datetime.now(timezone.utc) + datetime.timedelta(
                                    hours=5.5),
                                reply_number="SMS_url", status="sent", request=url,
                                response=s_response, user_id=token_data.user_id, to_number=to)
                    w_response = check_matched(token_data, to=to, msg=msg)
                    return JsonResponse({"sms":s_response, "whatsapp":w_response}, safe=False)

                elif msg_state.sms:
                    url = msg_state.sms_url.replace("<mobile>", to).replace("<message>", msg)
                    s_response = requests.get(url).text
                    SMS_OutBox.objects.create(message=msg,
                                send_time=datetime.datetime.now(timezone.utc) + datetime.timedelta(hours=5.5),
                                status="sent", request=url,response=s_response, user_id=token_data.user_id, to_number=to)
                    return JsonResponse(s_response, safe=False)

                elif msg_state.whatsapp:
                    response = check_matched(token_data, to=to, msg=msg)
                    if ("error" in response) and response["error"]["message"] == "(#100) Invalid parameter" and msg_state.sms_url:
                        url = msg_state.sms_url.replace("<mobile>", to).replace("<message>", msg)
                        s_response = requests.get(url).text
                    s_response = ""
                    return JsonResponse({"whatsapp":response, "SMS":s_response})

                if (not msg_state.both) and (not msg_state.sms) and (not msg_state.whatsapp) and (not msg_state.selective):
                    response = check_matched(token_data, to=to, msg=msg)
                    s_response = ""
                    if ("error" in response) and response["error"]["message"] == "(#100) Invalid parameter" and msg_state.sms_url: 
                        url = msg_state.sms_url.replace("<mobile>", to).replace("<message>", msg)
                        s_response = requests.get(url).text
                    return JsonResponse({"whatsapp":response, "SMS":s_response})
        else:
            return JsonResponse({"message":"User validity has been expired. Please recharge"})

    else:
        to = request.POST['to']
        token = request.POST['token']
        pdf = request.FILES['pdf']
        msg = request.POST['message']
        print(token)
        print(msg)
        temp_type = request.POST['temptype']

        token_obj = Developers_token.objects.get(u_token=token)
        user_id = token_obj.user_id

        user_obj = User1.objects.get(pk=user_id)
        wa_obj = WA_MSG_Provider.objects.get(pk=token_obj.message_provider_id)

        object_path = settings.MEDIA_ROOT+ "/media_msg/" + user_obj.user_name + "/" + wa_obj.provider_name
        if not os.path.exists(object_path):
            os.mkdir(settings.MEDIA_ROOT+ "/media_msg/" + user_obj.user_name)
            os.mkdir(settings.MEDIA_ROOT+ "/media_msg/" + user_obj.user_name + "/" + wa_obj.provider_name)

        if pdf:
            fss = FileSystemStorage()
            file_s = fss.save(object_path+"/"+pdf.name, pdf)
            furl = fss.url(file_s)
            vname = fss.get_valid_name(file_s)
            furl = "http://wotsapp-campaign.bonrix.in:8000" + furl
        token_data = Developers_token.objects.get(u_token=token)
        provider = WA_MSG_Provider.objects.get(id=token_data.message_provider_id)
        msg = regexpstring(msg, 0).replace("  "," ")
        api = Voice_API.objects.get(whatsapp_name=provider.provider_name)
        all_temp = New_Templates.objects.filter(message_provider_id=token_data.message_provider_id)
        for a in all_temp:
            if temp_type == "dynamic":
                data = regexpstring(a.text_msg, 1).replace("{#var#}", "(.*)")
                p = re.compile(data)
                variables = p.findall(msg)
                print("dynamic", msg)
                # print(a.id, a.text_msg)
                
                if variables:
                    print(variables)
                    print(a.temp_name, a.lang_code)
                    payload = {
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": f"{to}",
                    "type": "template",
                    "template": {
                        "name": f"{a.temp_name}",
                        "language": {
                            "code": f"{a.lang_code}"
                        },
                        "components": [
                                            {
                                    "type": "header",
                                    "parameters": [
                                        {
                                            "type": "document",
                                            "document": {
                                                "link": f"{furl}"
                                            }
                                        }
                                    ]
                                },

                            ]
                        }
                    }
                    
                    payload["template"]["components"].append({
                        "type": "body",
                        "parameters": []
                    })
                    if a.has_button:
                        payload["template"]["components"].append({
                            "type": "button",
                            "sub_type": "URL",
                            "index": "0",
                            "parameters": [{"type": "payload","payload": f"{vname}"}]
                        })

                    to_save  = {}
                    i = 1
                    if type(variables[0]) is str:
                        to_roam = variables
                    elif type(variables[0]) is tuple:
                        to_roam = variables[0]
                    print(to_roam)
                    for v in to_roam:
                        payload["template"]["components"][1]["parameters"].append({"type": "text", "text": f"{v}"})
                        to_save[i] = v
                        i += 1
                    payload = json.dumps(payload)
                    response = requests.request("POST", api.message_API, headers=api.header, data=payload)
                    print(response.text)
                    try:
                        msgid = json.loads(response.text)['messages'][0]['id']
                    except KeyError:
                        msgid = None
                    OutBox.objects.create(message=a.temp_name, send_time=datetime.datetime.now(timezone.utc) + datetime.timedelta(hours=5.5),
                            reply_number=provider.provider_name, request=api.message_API,
                            response=response.text, user_id=provider.user_id, to_number=to, msg_id=msgid, variables=to_save, media_url=furl)
                    Message_History.objects.create(message=a.temp_name, msg_type="send", customer_number=to, 
                                                api_number=provider.phone_no, user_id=provider.user_id,
                                                provider_id=provider.id, msg_id=msgid, media_url=furl)
                    return JsonResponse(json.loads(response.text))

            elif temp_type == "static":
                print(a.temp_name)
                if regexpstring(a.text_msg, 1) == msg:
                    
                    payload = {
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": f"{to}",
                    "type": "template",
                    "template": {
                        "name": f"{a.temp_name}",
                        "language": {
                            "code": f"{a.lang_code}"
                        },
                        "components": [
                                            {
                                    "type": "header",
                                    "parameters": [
                                        {
                                            "type": "document",
                                            "document": {
                                                "link": f"{furl}"
                                            }
                                        }
                                    ]
                                },

                            ]
                        }
                    }
                    
                    payload = json.dumps(payload)
                    response = requests.request("POST", api.message_API, headers=api.header, data=payload)
                    print(response.text)
                    try:
                        msgid = json.loads(response.text)['messages'][0]['id']
                    except KeyError:
                        msgid = None
                    OutBox.objects.create(message=a.temp_name, send_time=datetime.datetime.now(timezone.utc) + datetime.timedelta(hours=5.5),
                            reply_number=provider.provider_name, request=api.message_API,
                            response=response.text, user_id=provider.user_id, to_number=to, msg_id=msgid, media_url=furl)
                    Message_History.objects.create(message=a.temp_name, msg_type="send", customer_number=to, 
                                                api_number=provider.phone_no, user_id=provider.user_id,
                                                provider_id=provider.id, msg_id=msgid, media_url=furl)
                    return JsonResponse(json.loads(response.text))
        else:
            return JsonResponse({"message":"Template not found"})  

@csrf_exempt
def send_dynamic_template(request):
    if request.method == "GET":
        to = request.GET.get('to')
        msg = request.GET.get('msg')
        msg = msg.replace("  ", " ").replace("   ", " ")
        print(msg+" Thank you")
        token = request.GET.get('token')
        if User1.objects.get(pk=Developers_token.objects.get(u_token=token).user_id).is_active:
            if to != "" and msg != "" and token != "":
                if len(to) == 10:
                    to = "91" + to
                
                token_data = Developers_token.objects.get(u_token=token)
                msg_state = SMS_Settings.objects.get(usr_id=token_data.user_id)

                if msg_state.selective:
                    if "," not in msg_state.keywords:
                        to_check = msg_state.keywords.replace("['","").replace("']","").split(",")
                    
                    else:
                        ar = msg_state.keywords.split(",")
                        to_check = [x.replace("[","").replace("]","").replace("'","").strip() for x in ar]
                    print(to_check)
                    
                    for i in to_check:
                        if i in msg:
                            print("Matched")
                            if msg_state.sel_whatsapp and msg_state.sel_sms:
                                response2 = send_matched_temps(token_data, to=to, msg=request.GET.get('msg'))
                                url = msg_state.sms_url.replace("<mobile>", to).replace("<message>", msg)
                                s_response = requests.get(url).text
                                SMS_OutBox.objects.create(message=msg,
                                send_time=datetime.datetime.now(timezone.utc) + datetime.timedelta(hours=5.5),
                                status="sent", request=url,response=s_response, user_id=token_data.user_id, to_number=to)
                                return JsonResponse({"SMS":s_response, "whatsapp":response2}, safe=False)
                            if msg_state.sel_whatsapp:
                                response2 = send_matched_temps(token_data, to=to, msg=request.GET.get('msg'))
                                s_response = ""
                                if msg_state.sms:
                                    url = msg_state.sms_url.replace("<mobile>", to).replace("<message>", msg)
                                    s_response = requests.get(url).text
                                    SMS_OutBox.objects.create(message=msg,
                                    send_time=datetime.datetime.now(timezone.utc) + datetime.timedelta(hours=5.5),
                                    status="sent", request=url,response=s_response, user_id=token_data.user_id, to_number=to)
                                return JsonResponse({"whatsapp":response2, "SMS":s_response}, safe=False)
                                
                            if msg_state.sel_sms:

                                url = msg_state.sms_url.replace("<mobile>", to).replace("<message>", msg)
                                s_response = requests.get(url).text
                                response2 = ""
                                SMS_OutBox.objects.create(message=msg,
                                    send_time=datetime.datetime.now(timezone.utc) + datetime.timedelta(hours=5.5),
                                    status="sent", request=url,response=s_response, user_id=token_data.user_id, to_number=to)
                                if msg_state.whatsapp:
                                    response2 = send_matched_temps(token_data, to=to, msg=request.GET.get('msg'))
                                return JsonResponse({"SMS":s_response, "whatsapp":response2}, safe=False)
                    else:
                        pass

                if msg_state.both or (msg_state.sms and msg_state.whatsapp):
                    url = msg_state.sms_url.replace("<mobile>", to).replace("<message>", msg)
                    s_response = requests.get(url).text
                    OutBox.objects.create(message=msg,
                                send_time=datetime.datetime.now(timezone.utc) + datetime.timedelta(
                                    hours=5.5),
                                reply_number="SMS_url", status="sent", request=url,
                                response=s_response, user_id=token_data.user_id, to_number=to)
                    w_response = send_matched_temps(token_data, to=to, msg=request.GET.get('msg'))
                    return JsonResponse({"sms":s_response, "whatsapp":w_response}, safe=False)

                elif msg_state.sms:
                    url = msg_state.sms_url.replace("<mobile>", to).replace("<message>", msg)
                    s_response = requests.get(url).text
                    SMS_OutBox.objects.create(message=msg,
                                send_time=datetime.datetime.now(timezone.utc) + datetime.timedelta(hours=5.5),
                                status="sent", request=url,response=s_response, user_id=token_data.user_id, to_number=to)
                    return JsonResponse(s_response, safe=False)

                elif msg_state.whatsapp:
                    response = send_matched_temps(token_data, to=to, msg=request.GET.get('msg'))
                    return JsonResponse(response)

                if (not msg_state.both) and (not msg_state.sms) and (not msg_state.whatsapp) and (not msg_state.selective):
                    return JsonResponse({"message":"Please select options in settings"})
                return HttpResponse("Send")
        else:
            return JsonResponse({"message":"User validity has been expired. Please recharge"})
    else:
        to = request.POST['to']
        token = request.POST['token']
        pdf = request.FILES['pdf']
        msg = request.POST['message']
        temp_type = request.POST['temptype']

        token_obj = Developers_token.objects.get(u_token=token)
        user_id = token_obj.user_id

        user_obj = User1.objects.get(pk=user_id)
        wa_obj = WA_MSG_Provider.objects.get(pk=token_obj.message_provider_id)

        object_path = settings.MEDIA_ROOT+ "/media_msg/" + user_obj.user_name + "/" + wa_obj.provider_name
        if not os.path.exists(object_path):
            os.mkdir(settings.MEDIA_ROOT+ "/media_msg/" + user_obj.user_name)
            os.mkdir(settings.MEDIA_ROOT+ "/media_msg/" + user_obj.user_name + "/" + wa_obj.provider_name)

        if pdf:
            fss = FileSystemStorage()
            file_s = fss.save(object_path+"/"+pdf.name, pdf)
            furl = fss.url(file_s)
            vname = fss.get_valid_name(file_s)
            furl = "http://wotsapp-campaign.bonrix.in:8000" + furl
        token_data = Developers_token.objects.get(u_token=token)
        provider = WA_MSG_Provider.objects.get(id=token_data.message_provider_id)
        msg = regexpstring(msg, 0).replace("  "," ")
        api = Voice_API.objects.get(whatsapp_name=provider.provider_name)
        all_temp = New_Templates.objects.filter(message_provider_id=token_data.message_provider_id)
        for a in all_temp:
            if temp_type == "dynamic":
                data = regexpstring(a.text_msg, 1).replace("{#var#}", "(.*)")
                p = re.compile(data)
                variables = p.findall(msg)
                
                if variables:
                    print(variables)
                    print(a.temp_name, a.lang_code)
                    payload = {
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": f"{to}",
                    "type": "template",
                    "template": {
                        "name": f"{a.temp_name}",
                        "language": {
                            "code": f"{a.lang_code}"
                        },
                        "components": [
                                            {
                                    "type": "header",
                                    "parameters": [
                                        {
                                            "type": "document",
                                            "document": {
                                                "link": f"{furl}"
                                            }
                                        }
                                    ]
                                },

                            ]
                        }
                    }
                    
                    payload["template"]["components"].append({
                        "type": "body",
                        "parameters": []
                    })
                    payload["template"]["components"].append({
                        "type": "button",
                        "sub_type": "URL",
                        "index": "0",
                        "parameters": [
                            {
                                "type": "payload",
                                "payload": f"{vname}"
                            }
                        ]
                    })

                    to_save  = {}
                    i = 1
                    if type(variables[0]) is str:
                        to_roam = variables
                    elif type(variables[0]) is tuple:
                        to_roam = variables[0]
                    print(to_roam)
                    for v in to_roam:
                        payload["template"]["components"][1]["parameters"].append({"type": "text", "text": f"{v}"})
                        to_save[i] = v
                        i += 1
                    payload = json.dumps(payload)
                    response = requests.request("POST", api.message_API, headers=api.header, data=payload)
                    print(response.text)
                    try:
                        msgid = json.loads(response.text)['messages'][0]['id']
                    except KeyError:
                        msgid = None
                    OutBox.objects.create(message=a.temp_name, send_time=datetime.datetime.now(timezone.utc) + datetime.timedelta(hours=5.5),
                            reply_number=provider.provider_name, request=api.message_API,
                            response=response.text, user_id=provider.user_id, to_number=to, msg_id=msgid, variables=to_save, media_url=furl)
                    Message_History.objects.create(message=a.temp_name, msg_type="send", customer_number=to, 
                                                api_number=provider.phone_no, user_id=provider.user_id,
                                                provider_id=provider.id, msg_id=msgid, media_url=furl)
                    return JsonResponse(json.loads(response.text))

            elif temp_type == "static":
                print(a.temp_name)
                if regexpstring(a.text_msg, 1) == msg:
                    
                    payload = {
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": f"{to}",
                    "type": "template",
                    "template": {
                        "name": f"{a.temp_name}",
                        "language": {
                            "code": f"{a.lang_code}"
                        },
                        "components": [
                                            {
                                    "type": "header",
                                    "parameters": [
                                        {
                                            "type": "document",
                                            "document": {
                                                "link": f"{furl}"
                                            }
                                        }
                                    ]
                                },

                            ]
                        }
                    }
                    
                    payload = json.dumps(payload)
                    response = requests.request("POST", api.message_API, headers=api.header, data=payload)
                    print(response.text)
                    try:
                        msgid = json.loads(response.text)['messages'][0]['id']
                    except KeyError:
                        msgid = None
                    OutBox.objects.create(message=a.temp_name, send_time=datetime.datetime.now(timezone.utc) + datetime.timedelta(hours=5.5),
                            reply_number=provider.provider_name, request=api.message_API,
                            response=response.text, user_id=provider.user_id, to_number=to, msg_id=msgid, media_url=furl)
                    Message_History.objects.create(message=a.temp_name, msg_type="send", customer_number=to, 
                                                api_number=provider.phone_no, user_id=provider.user_id,
                                                provider_id=provider.id, msg_id=msgid, media_url=furl)
                    return JsonResponse(json.loads(response.text))
        else:
            return JsonResponse({"message":"Template not found"})            

@csrf_exempt
def send_media_SMS(request):
    furl = ""
    
    if request.method == "POST":
        to = request.POST['to']
        text = request.POST['text']
        token = request.POST['token']
        file = request.FILES['media_file']

        token_obj = Developers_token.objects.get(u_token=token)
        user_id = token_obj.user_id

        user_obj = User1.objects.get(pk=user_id)
        wa_obj = WA_MSG_Provider.objects.get(pk=token_obj.message_provider_id)

        object_path = settings.MEDIA_ROOT+ "/media_msg/" + user_obj.user_name + "/" + wa_obj.provider_name
        if not os.path.exists(object_path):
            os.mkdir(settings.MEDIA_ROOT+ "/media_msg/" + user_obj.user_name)
            os.mkdir(settings.MEDIA_ROOT+ "/media_msg/" + user_obj.user_name + "/" + wa_obj.provider_name)

        if file:
            fss = FileSystemStorage()
            file_s = fss.save(object_path+"/"+file.name, file)
            furl = fss.url(file_s)
            furl = "http://wotsapp-campaign.bonrix.in:8000" + furl
            print(furl.split(".")[-1])
    else:
        to = request.GET['to']
        text = request.GET['text']
        token = request.GET['token']
        furl = request.GET['media_file']
        token_obj = Developers_token.objects.get(u_token=token)
        user_id = token_obj.user_id
        print(furl)
    
    
    response = ""
    if len(to) == 10:
        to = "91" + to

    try:
        msg_provider = Developers_token.objects.get(u_token=token)
    except:
        return JsonResponse({"message": "Parameters are not valid."})

    wmp = WA_MSG_Provider.objects.get(id=msg_provider.message_provider_id)
    url_data = Voice_API.objects.get(whatsapp_name=wmp.provider_name)

    time_check = Conversation_Status.objects.filter(to=to, provider=wmp.provider_name)
    print(time_check)
    # After First time
    if time_check:
        lat_entry = time_check[len(time_check) - 1]
        
        if lat_entry.received_time and lat_entry.conversation_status == "Stopped":
            return JsonResponse({"message": "Your messages are blocked by user"})
        else:
            if (not lat_entry.received_time) or  (lat_entry.conversation_status == "Pending"):
                t = Templates.objects.get(temp_name=msg_provider.template, lang_code=msg_provider.lang,
                                          message_provider_id=wmp.id)
                print("Working Properly")
                if t.is_media:
                    if t.med_id is None:
                        return JsonResponse({"message": "Please Upload media content first."})
                    else:
                        js = json.loads(t.med_id)
                        payload = json.dumps({
                            "messaging_product": "whatsapp",
                            "recipient_type": "individual",
                            "to": f"{to}",
                            "type": "template",
                            "template": {
                                "name": f"{msg_provider.template}",
                                "language": {
                                    "code": f"{msg_provider.lang}"
                                },
                                "components": [
                                    {
                                        "type": "header",
                                        "parameters": [
                                            {
                                                "type": "image",
                                                "image": {"link": f"{js['link']}"} if js["type"] == "what" else {
                                                    "id": f"{js['med_obj']}"}
                                            }
                                        ]
                                    }
                                ]
                            }
                        })
                else:
                    payload = json.dumps({
                        "messaging_product": "whatsapp",
                        "recipient_type": "individual",
                        "to": f"{to}",
                        "type": "template",
                        "template": {
                            "name": f"{msg_provider.template}",
                            "language": {
                                "code": f"{msg_provider.lang}"
                            },

                        }
                    })

                response = requests.request("POST", url_data.message_API, headers=url_data.header, data=payload)
                try:
                    msgid = json.loads(response.text)['messages'][0]['id']
                    OutBox.objects.create(message=msg_provider.template,
                                          send_time=datetime.datetime.now(
                                              timezone.utc) + datetime.timedelta(
                                              hours=5.5),
                                          reply_number=wmp.provider_name, status="sent", request=url_data.message_API,
                                          response=response.text, user_id=wmp.user_id, to_number=to, msg_id=msgid)
                    Message_History.objects.create(message=msg_provider.template, msg_type="send", customer_number=to, 
                                        api_number=wmp.phone_no, user_id=wmp.user_id,
                                        provider_id=wmp.id, msg_id=msgid)
                    OutBox.objects.create(message=text,
                                          send_time=datetime.datetime.now(
                                              timezone.utc) + datetime.timedelta(
                                              hours=5.5),
                                          reply_number=wmp.provider_name, status="in_queue", user_id=wmp.user_id,
                                          to_number=to, media_url=furl)
                    con_stat = Conversation_Status.objects.get(to=to, provider=wmp.provider_name)
                    con_stat.inbox_msg = ""
                    con_stat.template = msg_provider.template
                    con_stat.send_time = datetime.datetime.now(timezone.utc) + datetime.timedelta(
                        hours=5.5)
                    con_stat.received_time = None
                    con_stat.conversation_status = "Pending"
                    con_stat.save()
                except KeyError:
                    pass

            else:
                if furl.split(".")[-1] in ['jpg', 'jpeg']:
                    con_type = "image"
                elif furl.split(".")[-1] in ['docx', 'pdf']:
                    con_type = "document"

                payload = json.dumps({
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": f"{to}",
                    "type": con_type,
                    con_type: {
                        "link": furl,
                        "caption": text
                    }
                })
                response = requests.request("POST", url_data.message_API, headers=url_data.header, data=payload)
                try:
                    msgid = json.loads(response.text)['messages'][0]['id']
                except KeyError:
                    msgid = ""
                OutBox.objects.create(message=text,
                                        send_time=datetime.datetime.now(
                                            timezone.utc) + datetime.timedelta(
                                            hours=5.5), reply_number=wmp.provider_name,
                                        status="sent", request=url_data.message_API, response=response.text,
                                        user_id=wmp.user_id, to_number=to, msg_id=msgid)
                Message_History.objects.create(message=text, msg_type="send", customer_number=to, 
                                        api_number=wmp.phone_no, user_id=wmp.user_id,
                                        provider_id=wmp.id, msg_id=msgid)
    # First Time API call
    else:
        t = Templates.objects.get(temp_name=msg_provider.template, lang_code=msg_provider.lang,
                                  message_provider_id=wmp.id)
        if t.is_media:
            if t.med_id is None:
                return JsonResponse({"message": "Please Upload media content first."})
            else:
                js = json.loads(t.med_id)
                payload = json.dumps({
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": f"{to}",
                    "type": "template",
                    "template": {
                        "name": f"{msg_provider.template}",
                        "language": {
                            "code": f"{msg_provider.lang}"
                        },
                        "components": [
                            {
                                "type": "header",
                                "parameters": [
                                    {
                                        "type": "image",
                                        "image": {"link": f"{js['link']}"} if js["type"] == "what" else {
                                            "id": f"{js['med_obj']}"}
                                    }
                                ]
                            }
                        ]
                    }
                })
        else:
            payload = json.dumps({
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": f"{to}",
                "type": "template",
                "template": {
                    "name": f"{msg_provider.template}",
                    "language": {
                        "code": f"{msg_provider.lang}"
                    },

                }
            })

        response = requests.request("POST", url_data.message_API, headers=url_data.header, data=payload)
        try:
            msgid = json.loads(response.text)['messages'][0]['id']
        except KeyError:
            msgid = ""
        OutBox.objects.create(message=msg_provider.template,
                              send_time=datetime.datetime.now(timezone.utc) + datetime.timedelta(
                                  hours=5.5),
                              reply_number=wmp.provider_name, status="sent", request=url_data.message_API,
                              response=response.text, user_id=wmp.user_id, to_number=to, msg_id=msgid)
        Message_History.objects.create(message=msg_provider.template, msg_type="send", customer_number=to, 
                                        api_number=wmp.phone_no, user_id=wmp.user_id,
                                        provider_id=wmp.id, msg_id=msgid)
        OutBox.objects.create(message=text,
                              send_time=datetime.datetime.now(timezone.utc) + datetime.timedelta(
                                  hours=5.5),
                              reply_number=wmp.provider_name, status="in_queue", user_id=wmp.user_id, to_number=to, media_url=furl)
        Conversation_Status.objects.create(to=to, provider=wmp.provider_name, template=msg_provider.template,
                                           send_time=datetime.datetime.now(
                                               timezone.utc) + datetime.timedelta(
                                               hours=5.5), user_id_id=user_id)

    return JsonResponse(json.loads(response.text))
    


def dashboard(request): 
    if 'id' in request.COOKIES and User1.objects.get(id=request.COOKIES['id']).is_authenticated():
        u_id = request.COOKIES['id']
        u_name = request.COOKIES['uname']
        data = Campaign.objects.filter(user_key_id=u_id)
        advData = AdvanceCampaign.objects.filter(user_key_id=u_id)
        try:
            validity = User1.objects.get(id=u_id).validity - datetime.date.today()
        except:
            validity = ""
        return render(request, "dashboard.html", {'u_name': u_name, 'data': data, 'advData': advData, 'validity':validity})
    else:
        return redirect('/')



def register(request):
    if request.method == 'POST':
        is_user = User1.objects.filter(email=request.POST['email'], phone_no=request.POST['phoneno'])
        if is_user:
            return JsonResponse({'msg': 'User already exist'})
        elif request.POST['email'] == "" or request.POST['phoneno'] == "" or \
                request.POST['phoneno'] == "" or request.POST['password'] == "":
            return JsonResponse({'msg': "Please fill the field properly."})
        else:
            u_name = str(request.POST['u-name'])
            u_name = u_name.replace(" ", "_")
            email = request.POST['email']
            password = request.POST['password']
            phone_no = request.POST['phoneno']
            
            validity = datetime.date.today() + datetime.timedelta(days=int(APP_Setting.objects.get(key="USER_VALIDITY").value))
            User1.objects.create(user_name=u_name.lower(), email=email.lower(), password=password, phone_no=phone_no, validity=validity)
            SMS_Settings.objects.create(whatsapp=True, usr_id=User1.objects.get(email=email.lower()).id)
            return redirect('/')


def login(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        print(email,password)
        user = User1.authenticate(email, password)
        if user:
            if user[0].is_active:
                User1.login(user[0])
                response = redirect('dashboard')
                response.set_cookie('uname', user[0].user_name)
                response.set_cookie('id', user[0].id)
                response.set_cookie('mobile', user[0].phone_no)
                print('redirect', {'user': user[0]})
                return response
            else:
                messages.error(request, 'Your validity have been expired')
        else:
            messages.error(request, 'Email or Password is Invalid.')
    return render(request, 'login.html')


def logout(request):
    if request.COOKIES['mobile']:
        User1.objects.get(id=request.COOKIES['id']).logout()
        response = redirect("/")
        response.delete_cookie('mobile')
        response.delete_cookie('id')
        response.delete_cookie('uname')
        response.delete_cookie('camp_id')
        return response
    else:
        return redirect("/")


def resetPass(request):
    email = request.POST['email']
    uid = User1.objects.filter(email=email)

    if uid:
        passw = uid[0].password
        sendmail("Forgot Password ", "mail_template", email, {'pass': passw, 'f_name': uid[0].user_name})
        return HttpResponse("Reset password has been sent to your email")
    else:
        message = "Email does not exist"
        return HttpResponse(message)


def sendmail(subject, template, to, context):
    EMAIL_HOST_USER = "email_user"
    EMAIL_HOST_PASSWORD = "email_password"
    template_str = template + '.html'
    html_message = render_to_string(template_str, {'data': context})
    plain_message = strip_tags(html_message)
    send_mail(subject, plain_message, EMAIL_HOST_USER, [to], html_message=html_message)


def addCamp(request):
    if "id" in request.COOKIES and User1.objects.get(id=request.COOKIES["id"]).is_authenticated():
        uid = User1.objects.get(phone_no=request.COOKIES["mobile"])
        if request.method == 'POST':
            name = str(request.POST['camp-name'])
            name = name.replace(" ", "_")
            if not Campaign.objects.filter(CampaignName=name, user_key_id=uid):
                description = request.POST['desc']
                uid = User1.objects.get(phone_no=request.COOKIES["mobile"])
                Campaign.objects.create(CampaignName=name, Description=description, record_count=0,
                                        CampaignStatus="Stop",
                                        user_key_id=uid.id)
                messages.success(request, "Campaign Added Successfully")
            else:
                messages.error(request, "Campaign Already exist.")
        return redirect("/dashboard/")
    else:
        return JsonResponse({"Error":"Login required to access this page"})

def addComposer(request):
    if "id" in request.COOKIES and User1.objects.get(id=request.COOKIES["id"]).is_authenticated():
        u_id = request.COOKIES["id"]
        id = request.GET.get('unique')
        print(u_id)
        data = WA_MSG_Provider.objects.filter(user_id=u_id)
        print(data)
        return render(request, 'AddCompo.html', {'id': id, 'data': data})
    else:
        return JsonResponse({"Error":"Login required to access this page"})


def record(request):
    if "id" in request.COOKIES and User1.objects.get(id=request.COOKIES["id"]).is_authenticated():
        u_id = request.GET.get('unique')
        record = Data_Summary.objects.filter(recordID_id=u_id)
        url_data = Voice_API.objects.filter(u_ID_id=u_id)
        campaign = Campaign.objects.filter(id=u_id)[0].CampaignName
        campStat = Campaign.objects.filter(id=u_id)[0].CampaignStatus
        providers = WA_MSG_Provider.objects.filter(user_id=request.COOKIES['id'])
        success = Data_Summary.objects.filter(recordID_id=u_id,status="Success").count()
        sent = Data_Summary.objects.filter(recordID_id=u_id,what_status="Sent").count()
        delivered = Data_Summary.objects.filter(recordID_id=u_id,what_status="delivered").count()
        read = Data_Summary.objects.filter(recordID_id=u_id,what_status="read").count()
        failed = Data_Summary.objects.filter(recordID_id=u_id,what_status="failed").count()
        try:
            comp_ratio = (read/record.count())*100
            print(success)
            response = render(request, "record.html",
                            {"Campaign": campaign, "record": record, "url_data": url_data, "CampStat": campStat,
                            "providers": providers, 
                            "success":{"c":success, "p":int((success/record.count())*100)}, 
                            "sent":sent, 
                            "delivered":delivered, "read":{"c":read,"p": int((read/record.count())*100)},
                            "total":record.count(), 
                            "failed":{"c":failed,"p": int((failed/record.count())*100)}, "comp_ratio":comp_ratio})
        except ZeroDivisionError:
            response = render(request, "record.html",
                            {"Campaign": campaign, "record": record, "url_data": url_data, "CampStat": campStat,
                            "providers": providers})
        response.set_cookie("camp_id", u_id)
        return response
    else:
        return JsonResponse({"Error":"Login required to access this page"})


def pendingAll(request):
    if "id" in request.COOKIES and User1.objects.get(id=request.COOKIES['id']).is_authenticated():
        campID = request.COOKIES["camp_id"]
        if request.GET['name'] == "advance":
            pending = Advance_Data.objects.filter(recordID_id=campID, status="Success")
            for p in pending:
                p.status = "Pending"
                p.save()
            return redirect(f"/advanceRecord?unique={campID}")
        elif request.GET['name'] == "normal":
            pending = Data_Summary.objects.filter(recordID_id=campID, status="Success")
            for p in pending:
                p.status = "Pending"
                p.save()
            return redirect(f"/composerList/?unique={campID}")
    else:
        return JsonResponse({"Error":"Login required to access this page"})


def deleteAll(request):
    print("...........................Delete")
    name = request.GET.get('name')
    print(name)
    if name == "Camp":
        Campaign.objects.filter(user_key_id=request.COOKIES['id']).delete()
        return redirect("/dashboard")
    if name == "AdvCamp":
        AdvanceCampaign.objects.filter(user_key_id=request.COOKIES['id']).delete()
        return redirect("/dashboard")
    if name == "Rec":
        camp = request.COOKIES['camp_id']
        Data_Summary.objects.filter(recordID_id=camp).delete()
        campaign = Campaign.objects.get(id=camp)
        campaign.record_count = 0
        campaign.save()
        return redirect("/dashboard")
    if name == "advRec":
        camp = request.COOKIES['camp_id']
        print(camp)
        Advance_Data.objects.filter(recordID_id=camp).delete()
        campaign = AdvanceCampaign.objects.get(id=camp)
        campaign.record_count = 0
        campaign.save()
        return redirect("/dashboard")
    if name == 'inbox':
        MessageLog.objects.filter(user_id=request.COOKIES['id']).delete()
        return redirect("/dashboard")
    if name == 'outbox':
        OutBox.objects.filter(user_id=request.COOKIES['id']).delete()
        return redirect("/dashboard")
    if name == "submessage":
        SubMessageLog.objects.filter(user_id=request.COOKIES['id']).delete()
        return redirect("/dashboard")


def delete(request):
    if "id" in request.COOKIES and User1.objects.get(id=request.COOKIES['id']).is_authenticated():
        name = request.GET.get('name')
        if name == 'Camp':
            campid = request.GET.get('cid')
            print(Campaign.objects.get(id=campid).delete())
            return redirect("/dashboard")
        if name == 'AdvCamp':
            campid = request.GET.get('cid')
            print(AdvanceCampaign.objects.get(id=campid).delete())
            return redirect("/dashboard")
        
        if name == 'Tok':
            tok_id = request.GET.get('tid')
            print(tok_id)
            print(Developers_token.objects.get(message_provider_id=tok_id).delete())
            return redirect("/generateToken/")
        
        if name == "auto_rep":
            rep_id = request.GET['rid']
            bot_auto = Bot_Auto_Reply.objects.get(pk=rep_id)
            if "catalogue" in bot_auto.reply_message:
                catlist = bot_auto.reply_message['catalogue']
                for c in catlist:
                    fname = c["link"].split("/")[6]
                    provider = c["link"].split("/")[5]
                try: 
                    pth = r"C:/Whatsapp_Cloud_API_Server/media_objects/UnzippedFiles" + f"/{provider}/{fname}" 
                    pth = pathlib.Path(pth)
                    
                    for sub in pth.iterdir() :
                            sub.unlink()

                    os.rmdir("C:\Whatsapp_Cloud_API_Server\media_objects/UnzippedFiles/"+provider+"/"+fname)
                except Exception as e:
                    print(e)
            bot_auto.delete()
            messages.success(request, "Data deleted Successfully")
            return JsonResponse({"Status":"Success"})
    else:
        return JsonResponse({"Error":"Login required to access this page"})

@csrf_exempt
def deleteRec(request):
    if "id" in request.COOKIES and User1.objects.get(id=request.COOKIES['id']).is_authenticated():
        result = json.load(request)
        data = result['data']
        name = result['name']
        print(data)

        if name == "template":
            for i in data:
                template = Templates.objects.get(pk=i)
                prod = WA_MSG_Provider.objects.get(pk=template.message_provider_id)
                resp = requests.delete(f"https://graph.facebook.com/v15.0/{prod.business_id}/message_templates?name={template.temp_name}&access_token={prod.token}")
                status_check = json.loads(resp.text)
                print(status_check)
                template.delete()
        if name == "dytemplate":
            for i in data:
                template = New_Templates.objects.get(pk=i)
                prod = WA_MSG_Provider.objects.get(pk=template.message_provider_id)
                resp = requests.delete(f"https://graph.facebook.com/v15.0/{prod.business_id}/message_templates?name={template.temp_name}&access_token={prod.token}")
                status_check = json.loads(resp.text)
                print(status_check)
                template.delete()
        if name == "record":
            camp_id = request.COOKIES['camp_id']
            count = Campaign.objects.get(id=camp_id)
            n = 0
            for id in data:
                Data_Summary.objects.get(id=id).delete()
                n += 1
            count.record_count -= n
            count.save()
        if name == "advanceRec":
            camp_id = request.COOKIES['camp_id']
            count = AdvanceCampaign.objects.get(id=camp_id)
            n = 0
            for id in data:
                Advance_Data.objects.get(id=id).delete()
                n += 1
            count.record_count -= n
            count.save()
        if name == 'outbox':
            data = data
            for id in data:
                OutBox.objects.get(id=id).delete()
        if name == 'inbox':
            data = data
            for id in data:
                MessageLog.objects.get(id=id).delete()
        if name == "submessage":
            data = data
            for id in data:
                SubMessageLog.objects.get(id=id).delete()
        
        if name == "startbot":
            CustomerBotStop.objects.filter(pk__in=data).delete()
        
        if name == "botSetting":
            What_Bot.objects.filter(pk__in=data).delete()

        if name == "appSetting":
            APP_Setting.objects.filter(pk__in=data).delete()

        if name == "reminduser":
            Reminder_User.objects.filter(pk__in=data).delete()

        return JsonResponse({"Name": "DeleteFunction"})
    else:
        return JsonResponse({"Error":"Login required to access this page"})

def show_settings(request):
    if "id" in request.COOKIES and User1.objects.get(id=request.COOKIES['id']).is_authenticated():
        u_id = request.COOKIES['id']
        print(u_id)
        data = WA_MSG_Provider.objects.filter(user_id=u_id)
        return render(request, "settings.html",
                      {"data": data, "home": "/dashboard", "addS": "/addSettings", "delete": "/delete_setting/",
                       "edit": "/editSettings"})
    else:
        return JsonResponse({"Error":"Login required to access this page"})

def addSettings(request):
    if "id" in request.COOKIES and User1.objects.get(id=request.COOKIES['id']).is_authenticated():
        message = {"MSG": ""}
        if request.method == "POST":
            mobile = request.POST['phone_no'].replace(" ", "")
            mobile = mobile.replace("+", "")
            mobile = mobile.strip()
            if not WA_MSG_Provider.objects.filter(phone_id=request.POST['phone_id'],
                                                  provider_name=request.POST['p_name']):
                WA_MSG_Provider.objects.create(phone_id=request.POST['phone_id'], provider_name=request.POST['p_name'],
                                               phone_no=mobile, token=request.POST['token'],
                                               business_id=request.POST['b_id'], user_id=request.COOKIES['id'], temp_header="Dear Customer", temp_footer="By "+request.POST['p_name'])
                Voice_API.objects.create(u_ID_id=request.COOKIES['id'],
                                         message_API=f"https://graph.facebook.com/v15.0/{request.POST['phone_id']}/messages",
                                         header={'Content-Type': 'application/json',
                                                 'Authorization': f'Bearer {request.POST["token"]}'},
                                         whatsapp_name=request.POST['p_name'])
                return redirect("/settings")
            else:
                message = {"MSG": "API setting already exist"}
        return render(request, "AddSettings.html", {"action": "/addSettings/", "set": "/settings"})
    else:
        return JsonResponse({"Error":"Login required to access this page"})

def editSettings(request):
    if "id" in request.COOKIES and User1.objects.get(id=request.COOKIES['id']).is_authenticated():
        if request.method == "POST":
            sid = request.POST['sid']
            data = WA_MSG_Provider.objects.get(id=sid)
            data.phone_id = request.POST['phone_id']
            # data.provider_name = request.POST['p_name']
            data.phone_no = request.POST['phone_no']
            data.token = request.POST['token']
            data.business_id = request.POST['b_id']
            data.save()
            if Voice_API.objects.filter(u_ID_id=data.user_id):
                va = Voice_API.objects.get(u_ID_id=data.user_id, whatsapp_name=data.provider_name)
                va.message_API = f"https://graph.facebook.com/v15.0/{request.POST['phone_id']}/messages"
                va.header = {"Content-Type": "application/json", "Authorization": f"Bearer {request.POST['token']}"}
                va.save()
            return redirect("/settings")
        else:
            sid = request.GET.get('sid')
            data = WA_MSG_Provider.objects.get(id=sid)
            return render(request, "editSettings.html",
                          {'sid': sid, 'data': data, "action": "/editSettings/", "set": "/settings"})
    else:
        return JsonResponse({"Error":"Login required to access this page"})

def delete_setting(request):
    if "id" in request.COOKIES and User1.objects.get(id=request.COOKIES['id']).is_authenticated():
        sid = request.GET.get('sid')
        data = WA_MSG_Provider.objects.get(id=sid)
        if Voice_API.objects.filter(u_ID_id=data.user_id, whatsapp_name=data.provider_name):
            Voice_API.objects.get(u_ID_id=data.user_id, whatsapp_name=data.provider_name).delete()
        data.delete()
        return redirect("/settings")
    else:
        return JsonResponse({"Error":"Login required to access this page"})

def start(request):
    if "id" in request.COOKIES and User1.objects.get(id=request.COOKIES['id']).is_authenticated():
        id = request.GET.get('id')
        mode = request.GET.get('mode')
        record = Data_Summary.objects.get(id=id)
        red_id = record.recordID_id
        url = f"/composerList?unique={red_id}"
        if record.status == "Pending":
            API = Voice_API.objects.filter(whatsapp_name=record.sender_name)[0]
            resp, img_link = hit_voice(record, API, mode)
            return JsonResponse({"url": url, "text": resp, "img": img_link})
        else:
            return JsonResponse({"url": url, "text": "Message has been already sent", "img": "img_link"})
    else:
        return JsonResponse({"Error":"Login required to access this page"})

def send_multiple_msg(request):
    if "id" in request.COOKIES and User1.objects.get(id=request.COOKIES['id']).is_authenticated():
        data = json.loads(request.body)
        if data['type'] == "record":
            mode = data['mode']
            record = Data_Summary.objects.filter(pk__in=data['data'], status="Pending")
            print(record)
            if not record:
                return  JsonResponse({"text": "messages Already Sent", "img": "http://craftizen.org/wp-content/uploads/2019/02/successful_payment_388054.png"})
            resp_list = []
            img_link = ""
            for r in record:
                API = Voice_API.objects.filter(whatsapp_name=r.sender_name)[0]
                resp, img_link = hit_voice(r, API, mode)
                resp_list.append(resp)
            
            return JsonResponse({"text": resp_list, "img": img_link})
        if data['type'] == "Advrecord":
            mode = data['mode']
            record = Advance_Data.objects.filter(pk__in=data['data'], status="Pending")
            if not record:
                return  JsonResponse({"text": "messages Already Sent", "img": "http://craftizen.org/wp-content/uploads/2019/02/successful_payment_388054.png"})
            resp_list = []
            img_link = ""
            for r in record:
                API = Voice_API.objects.filter(whatsapp_name=r.sender_name)[0]
                resp, img_link = advanceSend(r, API, mode)
                resp_list.append(resp)
            
            return JsonResponse({"text": resp_list, "img": img_link})
    else:
        return JsonResponse({"Error":"Login required to access this page"})

def hit_voice(record, API, mode):
    url = API.message_API
    headers = API.header
    payload = ""
    if mode == "text":
        msg = record.mobile
        payload = json.dumps({
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": f"{record.mobile}",
            "type": "text",
            "text": {
                "preview_url": False,
                "body": f"{record.text}"
            }
        })
    elif mode == "temp":
        msg = f"{record.template} [{record.lang}]"
        p = WA_MSG_Provider.objects.get(provider_name=API.whatsapp_name).id
        print(p, record.lang, record.template)
        t = Templates.objects.get(temp_name=record.template, lang_code=record.lang, message_provider_id=p)

        if t.is_media:
            if t.med_id is None:
                return "Please upload media from template management", ""
            else:
                js = json.loads(t.med_id)
                payload = json.dumps({
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": f"{record.mobile}",
                    "type": "template",
                    "template": {
                        "name": f"{record.template}",
                        "language": {
                            "code": f"{record.lang}"
                        },
                        "components": [
                            {
                                "type": "header",
                                "parameters": [
                                    {
                                        "type": "image",
                                        "image": {"link": f"{js['link']}"} if js["type"] == "what" else {
                                            "id": f"{js['med_obj']}"}
                                    }
                                ]
                            }
                        ]
                    }
                })
        else:
            msg = f"{record.template} [{record.lang}]" 
            payload = json.dumps({
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": f"{record.mobile}",
                "type": "template",
                "template": {
                    "name": f"{record.template}",
                    "language": {
                        "code": f"{record.lang}"
                    },

                }
            })
    # For simple text
    # payload = payload.replace("{reply}", record.text)
    response = requests.request("POST", url, headers=headers, data=payload)

    print(response.text)

    record.voiceshoot_req = url + str(headers)
    record.voiceshoot_res = response.text
    record.save()
    try:
        id = json.loads(response.text)["messages"][0]["id"]
        record.msg_id = id
        record.save()
        wap = WA_MSG_Provider.objects.get(provider_name=API.whatsapp_name)
        Message_History.objects.create(message=msg, msg_type="send", customer_number=record.mobile, 
                                        api_number=wap.phone_no, user_id=wap.user_id,
                                        provider_id=wap.id, msg_id=id)
        return f"Message sent Successfully.\nOn Whatsapp Number {record.mobile}\nMessage ID is:" + id, "http://craftizen.org/wp-content/uploads/2019/02/successful_payment_388054.png"
    except KeyError:
        return response.text, "http://craftizen.org/wp-content/uploads/2019/02/global_hint_failure_595796.png"


def check(request):
    
    # all_u = User1.objects.all()
    # for u in all_u:
    #     if not u.validity:
    #         u.validity=datetime.date.today()
    #         u.save()
        # if not SMS_Settings.objects.filter(usr_id=u.id):
        #     print(u.id)
        #     SMS_Settings.objects.create(whatsapp=True, usr_id=u.id)
    # data = Conversation_Status.objects.all()
    prds = WA_MSG_Provider.objects.all()
    data = []
    for p in prds:
        response = requests.get(
            f"https://graph.facebook.com/v15.0/{p.business_id}/message_templates?access_token={p.token}")
        try:
            response = json.loads(response.text)
            data = response['data']
        except KeyError:
            continue
        # print(data)
        for i in data:
            print(i['components'][-1])
    
            if i['components'][-1]['type'] == 'BUTTONS':
                for b in i['components'][-1]['buttons']:
                    if b['type'] == "URL":
                        New_Templates.objects.filter(temp_id=i['id']).update(has_button=1)
    # for d in data:
    #     try:
    #         try:
    #             payl = json.loads(d.response)
    #             print(type(payl))
    #         except:
    #             continue
    #         msgid = payl["messages"][0]['id']
    #         d.msg_id = msgid
    #         d.save()
    #     except KeyError:
    #         continue
    # for d in data:
    #     ids = WA_MSG_Provider.objects.filter(provider_name=d.provider)
    #     for id in ids:
    #         d.user_id_id=id.user_id
    #         d.save()

    # try:
    # if status:
    #     status = status[len(status) - 1].msg_status
    #     print(status)
    #     d.status = status
    #     d.save()
    # except:
    #     continue
    return JsonResponse({})


def background_process(id, mode, is_adv):
    if is_adv:
        data = Advance_Data.objects.filter(recordID_id=id, status="Pending")
        
        user = AdvanceCampaign.objects.get(id=id).user_key_id
        for i in data:
            print(threading.current_thread().name)
            if AdvanceCampaign.objects.get(id=id).CampaignStatus == "Start":
                API = Voice_API.objects.get(u_ID_id=user, whatsapp_name=i.sender_name)
                advanceSend(i, API, mode)
                i.status = "Success"
                i.save()
                db.close_old_connections()
                print(i.status)
            else:
                print("Done")
                break
        else:
            obj = AdvanceCampaign.objects.get(id=id)
            obj.CampaignStatus = "Stop"
            obj.save()
    else:
        data = Data_Summary.objects.filter(recordID_id=id, status="Pending")
        user = Campaign.objects.get(id=id).user_key_id
        for i in data:
            print(threading.current_thread().name)
            if Campaign.objects.get(id=id).CampaignStatus == "Start":
                API = Voice_API.objects.get(u_ID_id=user, whatsapp_name=i.sender_name)
                hit_voice(i, API, mode)
                i.status = "Success"
                i.save()
                db.close_old_connections()
                print(i.status)
            else:
                print("Done")
                break 
        else:
            obj = Campaign.objects.get(id=id)
            obj.CampaignStatus = "Stop"
            obj.save()


def start_all(request):
    if "id" in request.COOKIES and User1.objects.get(id=request.COOKIES['id']).is_authenticated():
        my_id = request.COOKIES['camp_id']
        mode = request.GET.get('mode')
        camp_type = request.GET.get("type")
        if camp_type == "normal":
            obj = Campaign.objects.get(id=my_id)
            obj.CampaignStatus = "Start"
            obj.save()
            t = threading.Thread(target=background_process, args=(my_id, mode, 0), kwargs={}, name=obj.CampaignName)
            t.setDaemon(True)
            t.start()
            messages.info(request, "Campaign Started")
            t.join()
            url = f"/composerList?unique={my_id}"
            return redirect(url)
        elif camp_type == "advance":
            obj = AdvanceCampaign.objects.get(id=my_id)
            obj.CampaignStatus = "Start"
            obj.save()
            t = threading.Thread(target=background_process, args=(my_id, mode, 1), kwargs={}, name=obj.CampaignName)
            t.setDaemon(True)
            t.start()
            messages.info(request, "Campaign Started")
            t.join()
            url = f"/advanceRecord?unique={my_id}"
            return redirect(url)
    else:
        return JsonResponse({"Error":"Login required to access this page"})


def stop(request):
    if "id" in request.COOKIES and User1.objects.get(id=request.COOKIES['id']).is_authenticated():
        my_id = request.COOKIES['camp_id']
        if request.GET['type'] == "advance":
            obj = AdvanceCampaign.objects.get(id=my_id)
            obj.CampaignStatus = "Stop"
            obj.save()
            messages.info(request, "Campaign Stopped")
            url = f"/advanceRecord?unique={my_id}"
            return redirect(url)
        elif request.GET['type'] == "normal":
            obj = Campaign.objects.get(id=my_id)
            obj.CampaignStatus = "Stop"
            obj.save()
            messages.info(request, "Campaign Stopped")
            url = f"/composerList?unique={my_id}"
            return redirect(url)
    else:
        return JsonResponse({"Error":"Login required to access this page"})

@csrf_exempt
def preview_composer(request):
    global chars, my_csv_data
    if "id" in request.COOKIES and User1.objects.get(id=request.COOKIES['id']).is_authenticated():
        if request.method == 'POST':
            type = request.POST['compType']
            mobile = ""
            desc = str(request.POST['Description'])
            template = str(request.POST['template']).split("-")[0] if request.POST['template'] else ""
            lang = str(request.POST['template']).split("-")[1] if request.POST['template'] else ""
            provider_no = request.POST['provider']
            checks = request.POST.getlist('country_check[]')
            print(checks)
            msg_provider = WA_MSG_Provider.objects.get(phone_no=provider_no)
            message_API = f"https://graph.facebook.com/v15.0/{msg_provider.phone_id}/messages"
            header = {'Content-Type': 'application/json',
                      'Authorization': f'Bearer {msg_provider.token}'}

            if type == "multiple":
                mobile = "{" + str(request.POST['col_Num']) + "}"
                file = request.FILES.get('myfile')
                if file.name.lower().endswith('.xlsx') or file.name.lower().endswith('.xls'):
                    dataset = Dataset()
                    imported_data = dataset.load(file.read(), format='xlsx')
                    my_csv_data = []
                    for i in imported_data[0]:
                        my_csv_data.append(str(i))
                else:
                    data = str(file.read())
                    rows = data.split("\\r\\n")
                    print(len(rows[1]))
                    print(rows[1])
                    my_csv_data = rows[1].split(",")

                chars = []

                asc = 65
                for i in range(len(my_csv_data)):
                    chars.append("{" + chr(asc) + "}")
                    asc += 1

                for c in range(len(my_csv_data)):
                    desc = desc.replace(f"{chars[c]}", my_csv_data[c])
                mobile = my_csv_data[chars.index(mobile)]
                if len(checks) and checks[0] == "yes":
                    mobile = request.POST['country_val'] + str(mobile)
            else:
                if len(checks) and checks[0] == "yes":
                    mobile = request.POST['country_val'] + request.POST['mobile']
                else:
                    mobile = request.POST['mobile']
            t = Templates.objects.get(temp_name=template, lang_code=lang, message_provider_id=msg_provider.id)

            if t.is_media:
                if t.med_id is None:
                    return JsonResponse({"text": "Please upload media from template management", "img": ""})
                else:
                    js = json.loads(t.med_id)
                    payload = json.dumps({
                        "messaging_product": "whatsapp",
                        "recipient_type": "individual",
                        "to": f"{mobile}",
                        "type": "template",
                        "template": {
                            "name": f"{template}",
                            "language": {
                                "code": f"{lang}"
                            },
                            "components": [
                                {
                                    "type": "header",
                                    "parameters": [
                                        {
                                            "type": "image",
                                            "image": {"link": f"{js['link']}"} if js["type"] == "what" else {
                                                "id": f"{js['med_obj']}"}
                                        }
                                    ]
                                }
                            ]
                        }
                    })
            else:
                print(mobile)
                payload = json.dumps({
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": f"{mobile}",
                    "type": "template",
                    "template": {
                        "name": f"{template}",
                        "language": {
                            "code": f"{lang}"
                        },
                    }
                })
            response = requests.request("POST", message_API, headers=header, data=payload)
            print(response.text)
            return JsonResponse({"text": response.text})
    else:
        return JsonResponse({"Error":"Login required to access this page"})

def prepare(file, id):
    if file.name.lower().endswith('.xlsx'):
        dataset = Dataset()
        imported_data = dataset.load(file.read(), format='xlsx')
        rows = []
        header = imported_data.headers
        for i in imported_data:
            rows.append(i)
        return rows, "tup", header
    else:
        data = str(file.read())
        rows = data.split("\\r\\n")
        header = rows[0]
        return rows, "", header


@csrf_exempt
def process_composer(request):
    if "id" in request.COOKIES and User1.objects.get(id=request.COOKIES['id']).is_authenticated():
        if request.method == 'POST':
            print(request.COOKIES['id'])
            id = request.POST['id']
            type = request.POST['compType']
            checks = request.POST.getlist('country_check[]')
            desc = str(request.POST['Description'])
            template = str(request.POST['template']).split("-")[0] if request.POST['template'] else ""
            lang = str(request.POST['template']).split("-")[1] if request.POST['template'] else ""

            provider_no = request.POST['provider']
            msg_provider = WA_MSG_Provider.objects.get(phone_no=provider_no)
            if not Voice_API.objects.filter(
                    message_API=f"https://graph.facebook.com/v15.0/{msg_provider.phone_id}/messages",
                    u_ID_id=request.COOKIES['id']):
                Voice_API.objects.create(u_ID_id=request.COOKIES['id'],
                                         message_API=f"https://graph.facebook.com/v15.0/{msg_provider.phone_id}/messages",
                                         header={'Content-Type': 'application/json',
                                                 'Authorization': f'Bearer {msg_provider.token}'},
                                         whatsapp_name=msg_provider.provider_name)

            if type == "multiple":
                mob_num = "{" + str(request.POST['col_Num']) + "}"
                file = request.FILES.get('myfile')
                rows, ftype, headers_char = prepare(file, request.COOKIES['id'])

                if ftype == "":
                    chars = []
                    asc = 65
                    numocol = len(rows[0].split(','))
                    for i in range(numocol):
                        chars.append("{" + chr(asc) + "}")
                        asc += 1

                    for i in range(1, len(rows) - 1):
                        jn = desc
                        final = ""

                        cols = rows[i].split(",")
                        for c in range(len(cols)):
                            jn = jn.replace(f"{chars[c]}", cols[c])
                        final += jn

                        mobile = cols[chars.index(mob_num)]
                        template = str(request.POST['template']).split("-")[0]
                        lang = str(request.POST['template']).split("-")[1]

                        if len(checks) and checks[0] == "yes":
                            mobile = request.POST['country_val'] + str(mobile)

                        Data_Summary.objects.create(template=template, lang=lang, mobile=mobile, text=final,
                                                    recordID_id=id, sender_name=msg_provider.provider_name)
                        count = Campaign.objects.get(id=id)
                        count.record_count += 1
                        count.save()
                    return redirect("/dashboard")
                elif ftype == "tup":
                    chars = []
                    asc = 65
                    numocol = len(rows[0])
                    for i in range(numocol):
                        chars.append("{" + chr(asc) + "}")
                        asc += 1
                    for i in range(0, len(rows)):
                        jn = desc
                        final = ""

                        cols = [x for x in rows[i]]
                        for c in range(len(cols)):
                            jn = jn.replace(f"{chars[c]}", str(cols[c]))
                        final += jn

                        mobile = cols[chars.index(mob_num)]
                        template = str(request.POST['template']).split("-")[0]
                        lang = str(request.POST['template']).split("-")[1]

                        if len(checks) and checks[0] == "yes":
                            mobile = request.POST['country_val'] + str(mobile)

                        Data_Summary.objects.create(template=template, lang=lang,
                                                    mobile=mobile, text=final,
                                                    recordID_id=id, sender_name=msg_provider.provider_name)
                        count = Campaign.objects.get(id=id)
                        count.record_count += 1
                        count.save()

                    return redirect("/dashboard")

            else:

                if len(checks) and checks[0] == "yes":
                    mob_num = request.POST['country_val'] + request.POST['mobile']
                else:
                    mob_num = request.POST['mobile']

                Data_Summary.objects.create(template=template, lang=lang, mobile=mob_num,
                                            text=desc,
                                            recordID_id=id, sender_name=msg_provider.provider_name)
                count = Campaign.objects.get(id=id)
                count.record_count += 1
                count.save()
                return redirect("/dashboard")
    else:
        return JsonResponse({"Error":"Login required to access this page"})

def DownloadZip(request):
    if "id" in request.COOKIES and User1.objects.get(id=request.COOKIES['id']).is_authenticated():
        uname = User1.objects.get(id=request.COOKIES["id"]).user_name
        camp = Campaign.objects.get(id=request.COOKIES["camp_id"]).CampaignName
        final = uname + "/" + camp

        from django.conf import settings
        path = settings.MEDIA_ROOT + "/" + final

        import os
        import zipfile
        zip_name = "myzipfile.zip"
        zf = zipfile.ZipFile(zip_name, "w")

        for dirname, subdirs, files in os.walk(path):
            for filename in files:
                zf.write(os.path.join(dirname, filename))
        zf.close()
        zip_file = open(zip_name, 'rb')
        response = HttpResponse(zip_file, content_type='application/force-download')
        response['Content-Disposition'] = 'attachment; filename=%s' % zip_name

        return response
    else:
        return JsonResponse({"Error":"Login required to access this page"})

def export_excel(request):
    if "id" in request.COOKIES and User1.objects.get(id=request.COOKIES['id']).is_authenticated():
        table_name = request.GET.get('table')
        # content-type of response
        response = HttpResponse(content_type='application/ms-excel')
        print(table_name)
        # decide file name
        response['Content-Disposition'] = f'attachment; filename="{table_name}.xls"'

        # creating workbook
        wb = xlwt.Workbook(encoding='utf-8')

        # adding sheet
        ws = wb.add_sheet("sheet1")

        # Sheet header, first row
        row_num = 0

        font_style = xlwt.XFStyle()
        # headers are bold
        font_style.font.bold = True

        # get your data, from database or from a text file...
        if table_name == "Record":
            # column header names, you can use your own headers here
            columns = ['Mobile', 'Sender', 'Template', 'Whatsapp Request', 'Whatsapp Response']

            # write column headers in sheet
            for col_num in range(len(columns)):
                ws.write(row_num, col_num, columns[col_num], font_style)

            # Sheet body, remaining rows
            font_style = xlwt.XFStyle()
            data = Data_Summary.objects.filter(recordID_id=request.COOKIES['camp_id'])  # dummy method to fetch data.
            for my_row in data:
                row_num = row_num + 1
                ws.write(row_num, 0, my_row.mobile, font_style)
                ws.write(row_num, 1, my_row.sender_name, font_style)
                ws.write(row_num, 2, my_row.template, font_style)
                ws.write(row_num, 3, my_row.voiceshoot_req, font_style)
                ws.write(row_num, 4, my_row.voiceshoot_res, font_style)
        elif table_name == "Inbox":
            try:
                print(request.GET['from'], request.GET['to'])
                from_d = str(request.GET['from']).split('-')
                to_d = str(request.GET['to']).split('-')
                from_d = datetime.datetime(int(from_d[0]), int(from_d[1]), int(from_d[2]), tzinfo=timezone.utc)
                to_d = datetime.datetime(int(to_d[0]), int(to_d[1]), int(to_d[2]), tzinfo=timezone.utc)
                data = MessageLog.objects.filter(user_id=request.COOKIES['id'], received_time__gte=from_d,
                                                 received_time__lte=to_d)
            except Exception as e:
                data = MessageLog.objects.filter(user_id=request.COOKIES['id'])
                print(e.__class__)
            # column header names, you can use your own headers here
            columns = ['Sender', 'Received message', 'Received Time', 'Reply_Number' 'Reply']

            # write column headers in sheet
            for col_num in range(len(columns)):
                ws.write(row_num, col_num, columns[col_num], font_style)

            # Sheet body, remaining rows
            font_style = xlwt.XFStyle()

            for my_row in data:
                row_num = row_num + 1
                ws.write(row_num, 0, my_row.sender_number, font_style)
                ws.write(row_num, 1, my_row.received_msg, font_style)
                ws.write(row_num, 2, str(my_row.received_time), font_style)
                ws.write(row_num, 3, my_row.reply_number, font_style)
                ws.write(row_num, 4, my_row.reply, font_style)
                # ws.write(row_num, 5, my_row.send_time, font_style)
        elif table_name == "outbox":
            try:
                print(request.GET['from'], request.GET['to'])
                from_d = str(request.GET['from']).split('-')
                to_d = str(request.GET['to']).split('-')
                from_d = datetime.datetime(int(from_d[0]), int(from_d[1]), int(from_d[2]), tzinfo=timezone.utc)
                to_d = datetime.datetime(int(to_d[0]), int(to_d[1]), int(to_d[2]), tzinfo=timezone.utc)
                data = OutBox.objects.filter(user_id=request.COOKIES['id'], send_time__gte=from_d, send_time__lte=to_d)
            except Exception as e:
                data = OutBox.objects.filter(user_id=request.COOKIES['id'])
                print(e.__class__)
            # column header names, you can use your own headers here
            columns = ['To', 'Message', 'Send Time', 'Reply_Number' 'Request', 'Response']

            # write column headers in sheet
            for col_num in range(len(columns)):
                ws.write(row_num, col_num, columns[col_num], font_style)

            # Sheet body, remaining rows
            font_style = xlwt.XFStyle()

            for my_row in data:
                row_num = row_num + 1
                ws.write(row_num, 0, my_row.to_number, font_style)
                ws.write(row_num, 1, my_row.message, font_style)
                ws.write(row_num, 2, str(my_row.send_time), font_style)
                ws.write(row_num, 3, my_row.reply_number, font_style)
                ws.write(row_num, 4, my_row.request, font_style)
                ws.write(row_num, 5, my_row.response, font_style)
        elif table_name == "conv_table":
            # column header names, you can use your own headers here
            columns = ['To Mobile', 'From', 'Message', 'Template', 'Send Time', 'Received Time', "Status"]

            # write column headers in sheet
            for col_num in range(len(columns)):
                ws.write(row_num, col_num, columns[col_num], font_style)

            # Sheet body, remaining rows
            font_style = xlwt.XFStyle()
            data = Conversation_Status.objects.filter(user_id=request.COOKIES['id'])  # dummy method to fetch data.
            for my_row in data:
                row_num = row_num + 1
                ws.write(row_num, 0, my_row.to, font_style)
                ws.write(row_num, 1, my_row.provider, font_style)
                ws.write(row_num, 2, my_row.inbox_msg, font_style)
                ws.write(row_num, 3, my_row.template, font_style)
                ws.write(row_num, 4, str(my_row.send_time), font_style)
                ws.write(row_num, 5, str(my_row.received_time), font_style)
                ws.write(row_num, 6, my_row.conversation_status, font_style)
        wb.save(response)
        return response
    else:
        return JsonResponse({"Error":"Login required to access this page"})
selected_Ecxel_file = ""

def export_selected_excel(request):
    if "id" in request.COOKIES and User1.objects.get(id=request.COOKIES['id']).is_authenticated():
        result = json.load(request)
        table_name = result["name"]
        # content-type of response
        response = HttpResponse(content_type='application/ms-excel')
        print(table_name)
        # decide file name
        response['Content-Disposition'] = f'attachment; filename="{table_name}.xls"'

        # creating workbook
        wb = xlwt.Workbook(encoding='utf-8')

        # adding sheet
        ws = wb.add_sheet("sheet1")

        # Sheet header, first row
        row_num = 0

        font_style = xlwt.XFStyle()
        # headers are bold
        font_style.font.bold = True

        # get your data, from database or from a text file...
        if table_name == "Record":
            # column header names, you can use your own headers here
            columns = ['Mobile', 'Sender', 'Template', 'Whatsapp Request', 'Whatsapp Response']

            # write column headers in sheet
            for col_num in range(len(columns)):
                ws.write(row_num, col_num, columns[col_num], font_style)

            # Sheet body, remaining rows
            font_style = xlwt.XFStyle()
            data = Data_Summary.objects.filter(pk__in=result['data'])  # dummy method to fetch data.
            for my_row in data:
                row_num = row_num + 1
                ws.write(row_num, 0, my_row.mobile, font_style)
                ws.write(row_num, 1, my_row.sender_name, font_style)
                ws.write(row_num, 2, my_row.template, font_style)
                ws.write(row_num, 3, my_row.voiceshoot_req, font_style)
                ws.write(row_num, 4, my_row.voiceshoot_res, font_style)
        elif table_name == "AdvRecord":
            # column header names, you can use your own headers here
            columns = ['Mobile', 'Sender', 'Template', 'Whatsapp Request', 'Whatsapp Response']

            # write column headers in sheet
            for col_num in range(len(columns)):
                ws.write(row_num, col_num, columns[col_num], font_style)

            # Sheet body, remaining rows
            font_style = xlwt.XFStyle()
            data = Advance_Data.objects.filter(pk__in=result['data'])  # dummy method to fetch data.
            for my_row in data:
                row_num = row_num + 1
                ws.write(row_num, 0, my_row.mobile, font_style)
                ws.write(row_num, 1, my_row.sender_name, font_style)
                ws.write(row_num, 2, my_row.template, font_style)
                ws.write(row_num, 3, my_row.voiceshoot_req, font_style)
                ws.write(row_num, 4, my_row.voiceshoot_res, font_style)
        elif table_name == "Inbox":
            data = MessageLog.objects.filter(pk__in=result['data'])
            print(data)
            # column header names, you can use your own headers here
            columns = ['Sender', 'Received message', 'Received Time', 'Reply_Number' 'Reply']

            # write column headers in sheet
            for col_num in range(len(columns)):
                ws.write(row_num, col_num, columns[col_num], font_style)

            # Sheet body, remaining rows
            font_style = xlwt.XFStyle()

            for my_row in data:
                row_num = row_num + 1
                ws.write(row_num, 0, my_row.sender_number, font_style)
                ws.write(row_num, 1, my_row.received_msg, font_style)
                ws.write(row_num, 2, str(my_row.received_time), font_style)
                ws.write(row_num, 3, my_row.reply_number, font_style)
                ws.write(row_num, 4, my_row.reply, font_style)
                # ws.write(row_num, 5, my_row.send_time, font_style)
        elif table_name == "outbox":
            data = OutBox.objects.filter(pk__in=result['data'])
            print(data)
            # column header names, you can use your own headers here
            columns = ['To', 'Message', 'Send Time', 'Reply_Number' 'Request', 'Response']

            # write column headers in sheet
            for col_num in range(len(columns)):
                ws.write(row_num, col_num, columns[col_num], font_style)

            # Sheet body, remaining rows
            font_style = xlwt.XFStyle()

            for my_row in data:
                row_num = row_num + 1
                ws.write(row_num, 0, my_row.to_number, font_style)
                ws.write(row_num, 1, my_row.message, font_style)
                ws.write(row_num, 2, str(my_row.send_time), font_style)
                ws.write(row_num, 3, my_row.reply_number, font_style)
                ws.write(row_num, 4, my_row.request, font_style)
                ws.write(row_num, 5, my_row.response, font_style)
        elif table_name == "conv_table":
            data = Conversation_Status.objects.filter(pk__in=result['data'])
            # column header names, you can use your own headers here
            columns = ['To Mobile', 'From', 'Message', 'Template', 'Send Time', 'Received Time', "Status"]

            # write column headers in sheet
            for col_num in range(len(columns)):
                ws.write(row_num, col_num, columns[col_num], font_style)

            # Sheet body, remaining rows
            font_style = xlwt.XFStyle()
              # dummy method to fetch data.
            for my_row in data:
                row_num = row_num + 1
                ws.write(row_num, 0, my_row.to, font_style)
                ws.write(row_num, 1, my_row.provider, font_style)
                ws.write(row_num, 2, my_row.inbox_msg, font_style)
                ws.write(row_num, 3, my_row.template, font_style)
                ws.write(row_num, 4, str(my_row.send_time), font_style)
                ws.write(row_num, 5, str(my_row.received_time), font_style)
                ws.write(row_num, 6, my_row.conversation_status, font_style)
        wb.save(response)
        global selected_Ecxel_file
        selected_Ecxel_file = response
        return JsonResponse({"url":"/getExcel"})
    else:
        return JsonResponse({"Error":"Login required to access this page"})

def getExcel(request):
    
    return selected_Ecxel_file


def refresh_temp(request):
    # request.COOKIES['id']
    # if User1.objects.get(id=34).is_authenticated():
    print(request.GET.get('pname'))
    if request.GET.get('pname') == "":
        # p = WA_MSG_Provider.objects.filter(user_id=request.COOKIES['id'])
        return JsonResponse({"alert": "Please select api provider first"})
    else:
        prods = WA_MSG_Provider.objects.filter(phone_no=request.GET.get('pname'))
        
    data = []
    if prods:
        p = prods[0]
        data = []
        response = requests.get(
            f"https://graph.facebook.com/v15.0/{p.business_id}/message_templates?access_token={p.token}")
        try:
            response = json.loads(response.text)
            data = response['data']
        except KeyError:
            return JsonResponse({"alert":response})
        api_temp_ids = set()
        temp_ids_query = Templates.objects.filter(message_provider_id=p.id).values('temp_id')
        tab_temp_id = set()
        for tab_temp in temp_ids_query:
            tab_temp_id.add(tab_temp['temp_id'])

        for i in data:
            api_temp_ids.add(i["id"])
            chat_temp = Chat_Templates.objects.filter(temp_id=i['id'])
            if not chat_temp:
                temp_compo = i['components']
                temp_preview = {}
                for j in range(len(temp_compo)):

                    is_media= False
                    if temp_compo[j]['type'].lower() == "header" and temp_compo[j]['format'].lower() == "text":
                        temp_preview[temp_compo[j]["type"]] = temp_compo[j]["text"]
                    elif temp_compo[j]['type'].lower() == "header" and temp_compo[j]['format'].lower() in ["image", "document"]:
                        if "example" in temp_compo[j]:
                            temp_preview[temp_compo[j]["type"]] = temp_compo[j]["example"]["header_handle"][0]
                        else:
                            temp_preview[temp_compo[j]["type"]] = temp_compo[j]["type"]
                        is_media = True
                        pass
                    elif temp_compo[j]['type'].lower() == "body":
                        temp_preview[temp_compo[j]["type"]] = temp_compo[j]["text"]
                    elif temp_compo[j]['type'].lower() == "buttons":
                        cont = 0
                        for b, d in enumerate(temp_compo[j]["buttons"]):
                            temp_preview[temp_compo[j]["type"] + str(b + 1)] = temp_compo[j]["buttons"][b]["text"]
                            cont += 1
                    elif temp_compo[j]['type'].lower() == "footer":
                        temp_preview[temp_compo[j]["type"]] = temp_compo[j]["text"]
                Chat_Templates.objects.create(user_id=p.user_id, message_provider_id=p.id, temp_name=i['name'], is_media = is_media,
                                            lang_code=i['language'], temp_id=i['id'], json=i, temp_preview=temp_preview, status=i['status'])
            else:
                temp_compo = i['components']
                im = False
                for j in range(len(temp_compo)):
                    if temp_compo[j]['type'].lower() == "header" and temp_compo[j]['format'].lower() != "text":
                        im=True
                chat_temp.update(is_media=im, status=i['status'])

            if Templates.objects.filter(temp_id=i['id']):
                Templates.objects.filter(temp_id=i['id']).update(status=i['status'])
                continue
            else:
                if i['components'][0]['type'].lower() == 'header' and i['components'][0]['format'].lower() != "text":
                    Templates.objects.create(user_id=p.user_id, message_provider_id=p.id, temp_name=i['name'],
                                             lang_code=i['language'], is_media=1, temp_id=i['id'],
                                             status=i['status'])
                else:
                    Templates.objects.create(user_id=p.user_id, message_provider_id=p.id, temp_name=i['name'],
                                             lang_code=i['language'], is_media=0, temp_id=i['id'],
                                             status=i['status'])
            
        to_delete = tab_temp_id - api_temp_ids
        for t_d in to_delete:
            Templates.objects.get(temp_id=t_d).delete()
        return JsonResponse({"alert": ""})
    else:
        JsonResponse({"alert":"No data found"})

def fetch_Temp(request):
    phone = request.GET.get("phone")
    print(phone)
    result = WA_MSG_Provider.objects.get(phone_no=phone)
    temps = Templates.objects.filter(user_id=request.COOKIES['id'], message_provider_id=result.id)
    yl = {}
    j = 0

    for i in temps:
        yl[j] = [i.temp_name, i.lang_code, i.is_media, i.temp_id]
        j += 1
    return JsonResponse({"data": yl})


@csrf_exempt
def receive_msg(request):
    data = json.loads(request.body)
    rec_phone_id = data['entry'][0]["changes"][0]["value"]['metadata']['phone_number_id']
    try:
        intern = data['entry'][0]["changes"][0]["value"]["statuses"]
        msgid = intern[0]['id']
        status = intern[0]['status']
        t = datetime.datetime.now(timezone.utc) + datetime.timedelta(hours=5.5)
        entry = WA_MSG_Provider.objects.get(phone_id=rec_phone_id)
        CallBack_Data.objects.create(Received=data, received_time=t, user_id=entry.user_id, msg_id=msgid,
                                     msg_status=status)
        if status == "failed":
            MessageLog.objects.filter(msg_id=msgid).update(response=intern[0]['errors'][0]['title'])
            SubMessageLog.objects.filter(msg_id=msgid).update(response=intern[0]['errors'][0]['title'])
            Data_Summary.objects.filter(msg_id=msgid).update(voiceshoot_res=intern[0]['errors'][0]['title'])
            OutBox.objects.filter(msg_id=msgid).update(response=intern[0]['errors'][0]['title'])
            Advance_Data.objects.filter(msg_id=msgid).update(voiceshoot_res=intern[0]['errors'][0]['title'])

        MessageLog.objects.filter(msg_id=msgid).update(status=status)
        SubMessageLog.objects.filter(msg_id=msgid).update(status=status)
        Data_Summary.objects.filter(msg_id=msgid).update(what_status=status)
        OutBox.objects.filter(msg_id=msgid).update(status=status)
        Advance_Data.objects.filter(msg_id=msgid).update(what_status=status)
        Message_History.objects.filter(msg_id=msgid).update(status=status)
        Reminder_User.objects.filter(b_msg_id=msgid).update(b_status=status)
        Reminder_User.objects.filter(a_msg_id=msgid).update(a_status=status)

        tem = datetime.datetime.fromtimestamp(int(intern[0]['timestamp']), tz=timezone.utc) + datetime.timedelta(hours=5.5)
        if status == "sent":
            Message_History.objects.filter(msg_id=msgid).update(sent_time=tem)
        if status == "delivered":
            
            Message_History.objects.filter(msg_id=msgid).update(delivered_time=tem)
        if status == "read":
            Message_History.objects.filter(msg_id=msgid).update(read_time=tem)
        # for thread in threading.enumerate():
        #     if not thread.is_alive():
        #         thread.join()
        #     print("Thread working........",thread.name, thread.isDaemon(), thread.is_alive())
        print(entry.provider_name, status)
        return JsonResponse({"response": "Success"})
    except KeyError:
        message = ""
        number, msg_type = data['entry'][0]["changes"][0]["value"]["messages"][0]['from'], "receive"
        incom_msg_id = data['entry'][0]["changes"][0]["value"]["messages"][0]['id']
        if data['entry'][0]["changes"][0]["value"]["messages"][0]['type'] == 'text':
            message = data['entry'][0]["changes"][0]["value"]["messages"][0]['text']['body']
        elif data['entry'][0]["changes"][0]["value"]["messages"][0]['type'] == 'button':
            message = data['entry'][0]["changes"][0]["value"]["messages"][0]['button']['text']
        t = datetime.datetime.now(timezone.utc) + timezone.timedelta(hours=5.5)
        # + datetime.timedelta(hours=5.5)
        rec_phone_id = data['entry'][0]["changes"][0]["value"]['metadata']['phone_number_id']

        try:
            entry = WA_MSG_Provider.objects.get(phone_id=rec_phone_id)
        except:
            print("Provider not found", rec_phone_id)
            return JsonResponse({"status": "Provider not found"})
        
        pid, p_num = entry.id, entry.phone_no

        CallBack_Data.objects.create(Received=data, received_time=t, user_id=entry.user_id, msg_id=incom_msg_id)
        MessageLog.objects.create(sender_number=number, received_msg=message, received_time=t, is_read=True,
                                  reply_number=p_num, json=data, user_id=entry.user_id)
        Message_History.objects.create(message=message, msg_type="received", customer_number=number, 
                                        api_number=p_num, user_id=entry.user_id,
                                        provider_id=pid)
        print("..............................", message)
        msg_log = MessageLog.objects.filter(received_msg=message, received_time=t,sender_number=number,reply_number=p_num,)
        
        check_conv = Conversation_Status.objects.filter(to=number, provider=entry.provider_name,
                                                        conversation_status="Pending")
        check_out = OutBox.objects.filter(to_number=number, reply_number=entry.provider_name, status="in_queue")
        update_conv = Conversation_Status.objects.filter(to=number, provider=entry.provider_name)
        update_conv.update(inbox_msg=message, received_time=t)
        
        print(check_out, check_conv)
        
        if (message.lower() in ["yes", "हां", "ok", "interested"]) and (check_out or check_conv):
            print("Yes Matched Hindi")
            pend_msg = check_out
            url_data = Voice_API.objects.get(whatsapp_name=entry.provider_name)
    
            for p in pend_msg:
                if p.media_url:
                    if p.media_url.split(".")[-1] in ['jpg', 'jpeg']:
                        con_type = "image"
                    elif p.media_url.split(".")[-1] in ['docx', 'pdf']:
                        con_type = "document"

                    payload = json.dumps({
                        "messaging_product": "whatsapp",
                        "recipient_type": "individual",
                        "to": f"{number}",
                        "type": con_type,
                        "image": {
                            "link": "http://wotsapp-campaign.bonrix.in:8000"+p.media_url,
                            "caption":p.message
                        }
                    })
                else:
                    payload = json.dumps({
                        "messaging_product": "whatsapp",
                        "recipient_type": "individual",
                        "to": f"{number}",
                        "type": "text",
                        "text": {
                            "preview_url": False,
                            "body": f"{p.message}"
                        }
                    })
                response = requests.request("POST", url_data.message_API, headers=url_data.header, data=payload)
                try:
                    msgid = json.loads(response.text)['messages'][0]['id']
                except KeyError:
                    msgid = ""
                p.status = "sent"
                p.msg_id = msgid
                p.request = url_data.message_API
                p.resonse = response.text
                p.save()
                Message_History.objects.create(message=p.message, msg_type="sent", customer_number=number, 
                                        api_number=p_num, user_id=entry.user_id,
                                        provider_id=pid, msg_id=msgid)
            print("Reaching")
            update_conv.update(conversation_status="Started")
        elif message.lower() in ["yes", "हां", "ok", 'start']:
            update_conv.update(conversation_status="Started")
        elif message.lower() in ["no","cancel"]:
            update_conv.update(conversation_status="Stopped")
        check_bot_exist = What_Bot.objects.filter(provider_id=entry.id)
        if check_bot_exist and (not CustomerBotStop.objects.filter(user_number=number, provider_id=entry.id)) and message.split("\n")[0].lower() not in ["no",""] :
            if check_bot_exist[0].is_on :
                print(check_bot_set(entry.user_id, entry.id, number, message.split("\n")[0], incom_msg_id, msg_log[0]))
    return JsonResponse({"response": "Success"})


def send_message_panel(request):
    if "id" in request.COOKIES and User1.objects.get(id=request.COOKIES['id']).is_authenticated():
        if request.method == "POST":
            data = json.loads(request.body)
            row_ids = data["data"]
            id_phone_p = MessageLog.objects.filter(pk__in=row_ids).values_list("id","reply_number")
            pair = []
            for i in  id_phone_p:
                pair.append(i[0])
            
            return JsonResponse({"phone": id_phone_p[0][1], "id":pair})
        elif request.method == "GET":
            row_id = request.GET.get("id")
            phone = MessageLog.objects.get(id=row_id).reply_number
            return render(request, 'send_message_panel.html', {"phone": phone, "id": row_id})
    else:
        return JsonResponse({"Error":"Login required to access this page"})

def submessage_panel(request):
    if "id" in request.COOKIES and User1.objects.get(id=request.COOKIES['id']).is_authenticated():
        row_id = request.GET.get("id")
        messages = SubMessageLog.objects.filter(parent_msg_id=row_id).order_by('-id').values()
        return render(request, 'subMessages.html', {'messages': messages})
    else:
        return JsonResponse({"Error":"Login required to access this page"})


@csrf_exempt
def getHeaderExcel(request):
    if "id" in request.COOKIES and User1.objects.get(id=request.COOKIES['id']).is_authenticated():
        if request.method == "POST":
            file = request.FILES.get('myfile')
            if file.name.lower().endswith('.xlsx'):
                dataset = Dataset()
                csv_data = dataset.load(file.read(), format='xlsx')
                csv_data = csv_data.headers
                print(csv_data)
            else:
                data = str(file.read())
                rows = data.split("\\r\\n")
                csv_data = rows[0].split(",")
                print(csv_data)
            return JsonResponse({"data": csv_data})
    else:
        return JsonResponse({"Error":"Login required to access this page"})

@csrf_exempt
def send_message(request):
    if "id" in request.COOKIES and User1.objects.get(id=request.COOKIES['id']).is_authenticated():
        phone = request.POST['phone']
        try:
            ids = str(request.POST['id']).replace("]", "").replace("[","").split(",")
        except Exception as e:
            ids = list(request.POST['id'])

        msg_p = WA_MSG_Provider.objects.get(phone_no=phone)
        api = Voice_API.objects.get(u_ID_id=msg_p.user_id, whatsapp_name=msg_p.provider_name)

        template = str(request.POST['template']).split("-")[0] if request.POST['template'] else ""
        lang = str(request.POST['template']).split("-")[1] if request.POST['template'] else ""

        numbers = MessageLog.objects.filter(pk__in=ids).order_by().values('sender_number').distinct()
        print(numbers)
        for num in numbers:
            print(num)
            msg_log = MessageLog.objects.filter(sender_number=num["sender_number"], reply_number=phone).latest("id")
            id = msg_log.id
            if request.POST['method'].lower() == "temp":
                t = Templates.objects.get(temp_name=template, lang_code=lang, message_provider_id=msg_p.id)

                if t.is_media:
                    print(t)
                    if t.med_id is None:
                        return JsonResponse({"message": "Please Upload media content first."})
                    else:
                        js = json.loads(t.med_id)
                        payload = json.dumps({
                            "messaging_product": "whatsapp",
                            "recipient_type": "individual",
                            "to": f"{msg_log.sender_number}",
                            "type": "template",
                            "template": {
                                "name": f"{template}",
                                "language": {
                                    "code": f"{lang}"
                                },
                                "components": [
                                    {
                                        "type": "header",
                                        "parameters": [
                                            {
                                                "type": "image",
                                                "image": {"link": f"{js['link']}"} if js["type"] == "what" else {
                                                    "id": f"{js['med_obj']}"}
                                            }
                                        ]
                                    }
                                ]
                            }
                        })
                else:
                    payload = json.dumps({
                        "messaging_product": "whatsapp",
                        "recipient_type": "individual",
                        "to": f"{msg_log.sender_number}",
                        "type": "template",
                        "template": {
                            "name": f"{template}",
                            "language": {
                                "code": f"{lang}"
                            },
                        }
                    })
                response = requests.post(url=api.message_API, data=payload, headers=api.header)
                print(payload)
                print(response.text)
                msg_log.reply = f"{template} [{lang}]"
                msg_log.request = api.message_API
                msg_log.send_time = datetime.datetime.now(timezone.utc) + datetime.timedelta(hours=5.5)
                msg_log.response = response.text
                try:
                    msg_id = json.loads(response.text)["messages"][0]['id']
                    msg_log.msg_id = msg_id
                    msg_log.save()
                except:
                    msg_id = ""
                    msg_log.save()
                SubMessageLog.objects.create(parent_msg_id=msg_log.id, reply_number=msg_log.reply_number,
                                            user_id=msg_log.user_id, reply=f"{template} [{lang}]", request=api.message_API,
                                            send_time=datetime.datetime.now(
                                                timezone.utc) + datetime.timedelta(hours=5.5),
                                            response=response.text, msg_id=msg_id)
                p = WA_MSG_Provider.objects.get(phone_no=msg_log.reply_number).id
                Message_History.objects.create(message=request.POST['message'], msg_type="send", customer_number=msg_log.reply_number, 
                                        api_number=msg_log.reply_number, user_id=msg_log.user_id, provider_id=p, msg_id=msg_id)
                    

            elif request.POST['method'].lower() == "mes":
                payload = json.dumps({
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": f"{msg_log.sender_number}",
                    "type": "text",
                    "text": {
                        "preview_url": False,
                        "body": f"{request.POST['message']}"
                    }
                })
                response = requests.post(url=api.message_API, data=payload, headers=api.header)
                print(response.text)
                msg_log.reply = request.POST['message']
                msg_log.request = api.message_API
                msg_log.response = response.text
                msg_log.send_time = datetime.datetime.now(timezone.utc) + datetime.timedelta(hours=5.5)
                try:
                    msg_id = json.loads(response.text)["messages"][0]['id']
                    msg_log.msg_id = msg_id
                    msg_log.save()
                    # messages.success(request, f"Message sent successfully to {msg_log.sender_number}")
                except:
                    msg_id = ""
                    msg_log.save()
                    # messages.error(request, f"Message not sent to {msg_log.sender_number}")
                SubMessageLog.objects.create(parent_msg_id=msg_log.id, reply_number=msg_log.reply_number,
                                                user_id=msg_log.user_id, reply=request.POST['message'],
                                                request=api.message_API,
                                                send_time=datetime.datetime.now(
                                                    timezone.utc) + datetime.timedelta(hours=5.5),
                                                response=response.text, msg_id=msg_id)
                p = WA_MSG_Provider.objects.get(phone_no=msg_log.reply_number).id
                Message_History.objects.create(message=request.POST['message'], msg_type="send", customer_number=msg_log.reply_number, 
                                        api_number=msg_log.reply_number, user_id=msg_log.user_id, provider_id=p,msg_id=msg_id)
                    
        return redirect("/showMessages/")
    else:
        return JsonResponse({"Error":"Login required to access this page"})

def showMessages(request):
    if "id" in request.COOKIES and User1.objects.get(id=request.COOKIES['id']).is_authenticated():
        id = request.COOKIES['id']
        messages = MessageLog.objects.filter(user_id=id).order_by('-id').values()
        providers = WA_MSG_Provider.objects.filter(user_id=id)
        
        return render(request, 'messages.html', {'messages': messages, 'provider': providers, "phone":providers[0].phone_no})
    else:
        return JsonResponse({"Error":"Login required to access this page"})


def get_state(request):
    prod_no = request.GET['phone']
    analysis = MessageLog.objects.values("received_msg").filter(reply_number=prod_no, received_msg__length__lt=15).distinct().annotate(m_count=Count("sender_number", distinct=True))
    analysis = analysis.order_by('-m_count')
    message = {}
    i = 0
    for d in list(analysis):
        if i > 15:
            break
        if d["received_msg"] == "" or d["received_msg"] == " " or (not d["received_msg"]):
            continue
        message[i]= {"m":d['received_msg'], "c": d['m_count']}
        i+=1
    return JsonResponse({"data": message})

def outBox(request):
    if "id" in request.COOKIES and User1.objects.get(id=request.COOKIES['id']).is_authenticated():
        id = request.COOKIES['id']
        messages = OutBox.objects.filter(user_id=id).order_by('-id').values()
        # 'provider': providers
        return render(request, 'outbox.html', {'messages': messages})
    else:
        return JsonResponse({"Error":"Login required to access this page"})

def SMS_outbox(request):
    if "id" in request.COOKIES and User1.objects.get(id=request.COOKIES['id']).is_authenticated():
        id = request.COOKIES['id']
        messages = SMS_OutBox.objects.filter(user_id=id).order_by('-id').values()
        # 'provider': providers
        return render(request, 'sms_outbox.html', {'messages': messages})
    else:
        return JsonResponse({"Error":"Login required to access this page"})

def get_random_string(length):
    # With combination of lower and upper case
    result_str = ''.join(random.choice(string.ascii_letters) for i in range(length))
    # print random string
    return result_str


def updateTokenTemp(request):
    if "id" in request.COOKIES and User1.objects.get(id=request.COOKIES['id']).is_authenticated():
        if request.method == "POST":
            token_id = str(request.POST["token_id"])
            print(token_id)
            template = str(request.POST['template']).split("-")[0] if request.POST['template'] else ""
            lang = str(request.POST['template']).split("-")[1] if request.POST['template'] else ""

            is_entry = Developers_token.objects.filter(u_token=token_id)
            if is_entry:
                is_entry.update(template=template, lang=lang)
        return redirect("/generateToken/")
    else:
        return JsonResponse({"Error":"Login required to access this page"})

@csrf_exempt
def generateToken(request):
    if "id" in request.COOKIES and User1.objects.get(id=request.COOKIES['id']).is_authenticated():
        user = request.COOKIES['id']
        u = User1.objects.get(id=user)
        if request.method == "POST":

            provider = request.POST["provider"]
            template = str(request.POST['template']).split("-")[0] if request.POST['template'] else ""
            lang = str(request.POST['template']).split("-")[1] if request.POST['template'] else ""
            try:
                m_id = WA_MSG_Provider.objects.get(phone_no=provider).id
            except:
                return JsonResponse({})

            if not Developers_token.objects.filter(message_provider_id=m_id):
                Developers_token.objects.create(user_id=int(u.id), message_provider_id=int(m_id),
                                                u_token=get_random_string(36), gen_time=datetime.datetime.now(
                        timezone.utc) + datetime.timedelta(hours=5.5),
                                                template=template, lang=lang)

        print(user)
        temp = WA_MSG_Provider.objects.filter(user_id=user)
        tk = Developers_token.objects.filter(user_id=user)
        print(temp)
        print(tk)
        data = {}
        if tk:
            for t in tk:
                data[t.message_provider_id] = {'temp': t.template, 'token': t.u_token}
            for tp in temp:
                if tp.id not in data:
                    pass
                else:
                    data[tp.id].update({'provider': tp.provider_name})
        return render(request, 'generate_token.html', {'temp': temp, 'data': data})
    else:
        return JsonResponse({"Error":"Login required to access this page"})

@csrf_exempt
def manageTemplate(request):
    if "id" in request.COOKIES and User1.objects.get(id=request.COOKIES['id']).is_authenticated():
        if request.method == "POST":
            template_id = request.POST['temp_id']
            platform = request.POST['plateform']

            mid = Templates.objects.get(temp_id=template_id)
            print("...............", mid.user_id)
            if mid.status.lower() in ["rejected", "pending"]:
                print("message")
                messages.error(request, "Template is not approved")

            else:
                user_name = User1.objects.get(id=mid.user_id).user_name
                p = WA_MSG_Provider.objects.get(id=mid.message_provider_id)
                provider_name = p.provider_name

                object_path = "C:/Whatsapp_Cloud_API_Server/media_objects/" + user_name + "/" + provider_name
                if not os.path.exists(object_path):
                    os.mkdir("C:/Whatsapp_Cloud_API_Server/media_objects/" + user_name)
                    os.mkdir("C:/Whatsapp_Cloud_API_Server/media_objects/" + user_name + "/" + provider_name)

                file = request.FILES['media_obj']
                open_f = file.name
                if file:
                    fss = FileSystemStorage()
                    file = fss.save(file.name, file)

                im = Image.open(r"C:/Whatsapp_Cloud_API_Server/media_objects/" + open_f)
                im.convert("RGB")
                file_name_save = template_id + "_" + str(datetime.datetime.now().timestamp()) + ".jpg"
                im.save(object_path + "/" + file_name_save)

                os.remove("C:/Whatsapp_Cloud_API_Server/media_objects/" + open_f)

                if platform.lower() == "facebook":
                    v = Voice_API.objects.get(whatsapp_name=provider_name)
                    url = f"https://graph.facebook.com/v15.0/{p.phone_id}/media"
                    headers = {'Authorization': f'Bearer {p.token}'}
                    payload = {'messaging_product': 'whatsapp'}
                    files = [
                        ('file', (file_name_save, open(object_path + f"/{file_name_save}", 'rb'), 'image/jpeg'))
                    ]
                    response = requests.request("POST", url, headers=headers, data=payload, files=files)
                    print(response.text)
                    result = json.loads(response.text)
                    # {"type": "facebook", "med_obj": result['id']}
                    Templates.objects.filter(temp_id=template_id).update(
                        med_id=json.dumps({"type": "facebook", "med_obj": result['id']}))
                    Chat_Templates.objects.filter(temp_id=template_id).update(
                        med_id=json.dumps({"type": "facebook", "med_obj": result['id']}))
                elif platform.lower() == "bonrix":
                    arr = object_path.split("/")
                    obj_id = f"{settings.HOST_URL}/media/" + arr[-2] + "/" + arr[
                        -1] + "/" + file_name_save
                    # {"type": "facebook", "link": obj_id}
                    Templates.objects.filter(temp_id=template_id).update(
                        med_id=json.dumps({"type": "what", "link": obj_id}))
                    Chat_Templates.objects.filter(temp_id=template_id).update(
                        med_id=json.dumps({"type": "what", "link": obj_id}))
                print(platform, file)

        user_id = request.COOKIES['id']
        data = Templates.objects.filter(user_id=user_id).order_by("-id")
        dl_temp = Templates.objects.filter(status="")
        for d in dl_temp:
            d.delete()
        prods = WA_MSG_Provider.objects.filter(user_id=user_id)
        return render(request, 'manageTemplates.html', {'data': data, 'prods': prods})
    else:
        return JsonResponse({"Error":"Login required to access this page"})

@csrf_exempt
def setAllTemp(request):
    if "id" in request.COOKIES and User1.objects.get(id=request.COOKIES['id']).is_authenticated():
        if request.method == "POST":
            camp_id = request.COOKIES['camp_id']
            provider = request.POST['provider']
            p_name = WA_MSG_Provider.objects.get(phone_no=provider).provider_name
            template = str(request.POST['template']).split("-")[0] if request.POST['template'] else ""
            lang = str(request.POST['template']).split("-")[1] if request.POST['template'] else ""
            data = Data_Summary.objects.filter(recordID_id=camp_id)
            for d in data:
                d.sender_name = p_name
                d.template = template
                d.lang = lang
                d.save()
        return JsonResponse({})
    else:
        return JsonResponse({"Error":"Login required to access this page"})

@csrf_exempt
def searchTable(request):
    if "id" in request.COOKIES and User1.objects.get(id=request.COOKIES['id']).is_authenticated():
        name = request.GET.get('name')
        print(name)
        final = {}
        if name == "inbox":
            sender = request.POST['sender']
            msg = request.POST['message']
            receiver = request.POST['receiver']
            stat = request.POST['status']

            data = MessageLog.objects.filter(user_id=request.COOKIES['id'])
            if sender != "":
                data = data & MessageLog.objects.filter(sender_number=sender)
            if msg != "":
                data = data & MessageLog.objects.filter(received_msg=msg)
            if receiver != "":
                data = data & MessageLog.objects.filter(reply_number=receiver)
            if stat != "":
                data = data & MessageLog.objects.filter(status=stat)
            if request.POST['start'] != "" or request.POST['end'] != "":
                start = str(request.POST['start']).split("-")
                end = str(request.POST['end']).split("-")
                start = datetime.datetime(int(start[0]), int(start[1]), int(start[2]), tzinfo=timezone.utc)
                end = datetime.datetime(int(end[0]), int(end[1]), int(end[2]), tzinfo=timezone.utc)
                if start == end or request.POST['end'] == "":
                    data = data & MessageLog.objects.filter(received_time__gte=start)
                else:
                    data = data & MessageLog.objects.filter(received_time__gte=start, received_time__lte=end)
            for d in data:
                final[d.id] = {"Sender": d.sender_number, "received_time": d.received_time.strftime("%b. %d, %Y, %H:%M %p"),
                            "message": d.received_msg, "reply": d.reply, "from": d.reply_number, 'status': d.status,
                            "req": d.request, "res": d.response}
        elif name == "outbox":
            sender = request.POST['sender']
            from_no = request.POST['from']
            msg = request.POST['message']
            stat = request.POST['status']

            data = OutBox.objects.filter(user_id=request.COOKIES['id'])
            if from_no != "":
                data = data & OutBox.objects.filter(to_number=from_no)
            if sender != "":
                data = data & OutBox.objects.filter(reply_number=sender)
            if msg != "":
                data = data & OutBox.objects.filter(message=msg)
            if stat != "":
                data = data & OutBox.objects.filter(status=stat)
            if request.POST['start'] != "" or request.POST['end'] != "":
                start = request.POST['start']
                end = request.POST['end']
                if start == end or request.POST['end'] == "":
                    start = str(start).split("-")
                    start = datetime.datetime(int(start[0]), int(start[1]), int(start[2]), tzinfo=timezone.utc)
                    print(start)
                    data = data & OutBox.objects.filter(send_time__gte=start)
                else:
                    start = str(start).split("-")
                    end = str(end).split("-")
                    start = datetime.datetime(int(start[0]), int(start[1]), int(start[2]), tzinfo=timezone.utc)
                    end = datetime.datetime(int(end[0]), int(end[1]), int(end[2]), tzinfo=timezone.utc)
                    data = data & OutBox.objects.filter(send_time__gte=start, send_time__lte=end)
                # print(data)

            for d in data:
                final[d.id] = {"To": d.to_number, "Sender": d.reply_number, "message": d.message,
                            "send_time": d.send_time.strftime("%b. %d, %Y, %H:%M %p"), 'status': d.status,
                            'req': d.request, 'res': d.response}
        elif name == "template":
            print("Reaching")
            provider = request.GET.get('provider')
            final = {}
            data = Templates.objects.filter(message_provider_id=WA_MSG_Provider.objects.get(phone_no=provider).id)
            for d in data:
                final[d.id] = {'temp_id': d.temp_id, 'temp_name': d.temp_name, 'lang_code': d.lang_code,
                            'is_media': d.is_media,
                            'status': d.status}
            # print(data)
        # print(final)
        return JsonResponse(final)
    else:
        return JsonResponse({"Error":"Login required to access this page"})

def customerStat(request):
    if "id" in request.COOKIES and User1.objects.get(id=request.COOKIES['id']).is_authenticated():
        id = request.COOKIES['id']
        data = Conversation_Status.objects.filter(user_id_id=id).order_by('-id').values()
        return render(request, "customerStat.html", {"data": data})
    else:
        return JsonResponse({"Error":"Login required to access this page"})

def advanceCamp(request):
    if "id" in request.COOKIES and User1.objects.get(id=request.COOKIES['id']).is_authenticated():
        uid = User1.objects.get(phone_no=request.COOKIES["mobile"])
        if request.method == 'POST':
            if not Campaign.objects.filter(CampaignName=request.POST['camp-name'], user_key_id=uid):
                name = str(request.POST['camp-name'])
                name = name.replace(" ", "_")
                description = request.POST['desc']
                uid = User1.objects.get(phone_no=request.COOKIES["mobile"])
                AdvanceCampaign.objects.create(CampaignName=name, Description=description, record_count=0,
                                               CampaignStatus="Stop",
                                               user_key_id=uid.id)
            else:
                messages.error(request, "Campaign Already exist.")
        return redirect("/dashboard/")
    else:
        return JsonResponse({"Error":"Login required to access this page"})


def advanceTemplate(request):
    if "id" in request.COOKIES and User1.objects.get(id=request.COOKIES['id']).is_authenticated():
        id = request.GET.get('unique')
        u_id = request.COOKIES["id"]
        if request.method == "POST":
            vari = request.POST.getlist('body-variable[]')
            variables = vari
            try:
                header_vari = request.POST.getlist('header-variable[]')
            except:
                header_vari = []
                pass

            camp_id = request.POST['id']
            comp_type = request.POST['compType']
            checks = request.POST.getlist('country_check[]')

            desc = request.POST['Description']
            desc_vars = re.findall(r"\{[A-Z]}", desc)
            desc_vars.sort()
            desc_vars = [x.replace("{", "").replace("}", "") for x in desc_vars]
            print(desc_vars)
            alphabet = list(string.ascii_uppercase)

            temp_id = str(request.POST['template'])
            template = Templates.objects.get(temp_id=temp_id)

            provider_no = request.POST['provider']
            msg_provider = WA_MSG_Provider.objects.get(phone_no=provider_no)

            if not Voice_API.objects.filter(
                    message_API=f"https://graph.facebook.com/v15.0/{msg_provider.phone_id}/messages",
                    u_ID_id=request.COOKIES['id']):
                Voice_API.objects.create(u_ID_id=request.COOKIES['id'],
                                        message_API=f"https://graph.facebook.com/v15.0/{msg_provider.phone_id}/messages",
                                        header={'Content-Type': 'application/json',
                                                'Authorization': f'Bearer {msg_provider.token}'},
                                        whatsapp_name=msg_provider.provider_name)

            if comp_type == "multiple":
                mob_num = str(request.POST['col_Num'])
                file = request.FILES.get('myfile')
                rows, f_type, header_chars = prepare(file, request.COOKIES['id'])

                if f_type == "":
                    header_chars = header_chars.split(",")
                    desc = desc
                    for i in range(1, len(rows) - 1):

                        cols = rows[i].split(",")

                        for d in desc_vars:
                            desc = desc.replace("{" + d + "}", str(cols[alphabet.index(d)]))
                        pure_text = desc

                        to_save = {"header": {}, "body": {}}
                        for c in variables:
                            c = c.replace("{", "")
                            c = c.replace("}", "")
                            to_save["body"][str(variables.index(c) + 1)] = str(cols[header_chars.index(c)])

                        for h in header_vari:
                            h = h.replace("{", "")
                            h = h.replace("}", "")
                            to_save["header"][str(header_vari.index(h) + 1)] = str(cols[header_chars.index(h)])

                        mobile = cols[header_chars.index(mob_num)]
                        temp = template.temp_name
                        lang = template.lang_code

                        if len(checks) and checks[0] == "yes":
                            mobile = request.POST['country_val'] + str(mobile)

                        Advance_Data.objects.create(template=temp, lang=lang, mobile=mobile, variables=to_save,
                                                    text=pure_text,
                                                    recordID_id=camp_id, sender_name=msg_provider.provider_name)
                        count = AdvanceCampaign.objects.get(id=camp_id)
                        count.record_count += 1
                        count.save()
                    return redirect("/dashboard")
                elif f_type == "tup":
                    desc = desc
                    for i in range(0, len(rows)):
                        cols = [x for x in rows[i]]

                        for d in desc_vars:
                            desc = desc.replace("{" + d + "}", str(cols[alphabet.index(d)]))
                        pure_text = desc

                        to_save = {"header": {}, "body": {}}
                        for c in variables:
                            c = c.replace("{", "")
                            c = c.replace("}", "")
                            to_save["body"][str(variables.index(c) + 1)] = str(cols[header_chars.index(c)])

                        for h in header_vari:
                            h = h.replace("{", "")
                            h = h.replace("}", "")
                            to_save["header"][str(header_vari.index(h) + 1)] = str(cols[header_chars.index(h)])

                        mobile = cols[header_chars.index(mob_num)]
                        temp = template.temp_name
                        lang = template.lang_code

                        if len(checks) and checks[0] == "yes":
                            mobile = request.POST['country_val'] + str(mobile)

                        Advance_Data.objects.create(template=temp, lang=lang, mobile=mobile, variables=to_save,
                                                    text=pure_text,
                                                    recordID_id=camp_id, sender_name=msg_provider.provider_name)
                        count = AdvanceCampaign.objects.get(id=camp_id)
                        count.record_count += 1
                        count.save()

                    return redirect("/dashboard")

            else:

                if len(checks) and checks[0] == "yes":
                    mob_num = request.POST['country_val'] + request.POST['mobile']
                else:
                    mob_num = request.POST['mobile']
                to_save = {"header": {}, "body": {}}
                i = 1
                for c in variables:
                    to_save["body"][f"{str(i)}"] = c
                    i += 1
                i = 1
                for h in header_vari:
                    to_save["header"][f"{str(i)}"] = h
                    i += 1

                Advance_Data.objects.create(template=template.temp_name, lang=template.lang_code, mobile=mob_num,
                                            variables=to_save,
                                            recordID_id=camp_id, sender_name=msg_provider.provider_name)
                count = AdvanceCampaign.objects.get(id=camp_id)
                count.record_count += 1
                count.save()
                return redirect("/dashboard")

        data = WA_MSG_Provider.objects.filter(user_id=u_id)
        return render(request, "advanceTemp.html", {"id": id, "data": data})
    else:
        return JsonResponse({"Error":"Login required to access this page"})

@csrf_exempt
def advancePreview(request):
    if "id" in request.COOKIES and User1.objects.get(id=request.COOKIES['id']).is_authenticated():
        if request.method == 'POST':
            vari = request.POST.getlist('body-variable[]')
            variables = vari[0].split(",")
            try:
                header_vari = request.POST.getlist('header-variable[]')
                header_vari = header_vari[0].split(",")
            except:
                header_vari = []
                pass
            print(variables, header_vari)
            id = request.POST['id']
            type = request.POST['compType']
            checks = request.POST.getlist('country_check[]')

            temp_id = str(request.POST['template'])
            template = Templates.objects.get(temp_id=temp_id)

            provider_no = request.POST['provider']

            msg_provider = WA_MSG_Provider.objects.get(phone_no=provider_no)
            message_API = f"https://graph.facebook.com/v15.0/{msg_provider.phone_id}/messages"
            header = {'Content-Type': 'application/json',
                    'Authorization': f'Bearer {msg_provider.token}'}
            to_save = {"header": {}, "body": {}}
            if type == "multiple":
                mobile = request.POST['col_Num']
                file = request.FILES.get('myfile')
                if file.name.lower().endswith('.xlsx'):
                    dataset = Dataset()
                    imported_data = dataset.load(file.read(), format='xlsx')
                    header_chars = imported_data.headers
                    my_csv_data = []
                    for i in imported_data[0]:
                        my_csv_data.append(str(i))
                else:
                    data = str(file.read())
                    rows = data.split("\\r\\n")
                    header_chars = rows[0].split(",")
                    my_csv_data = rows[1].split(",")
                # to_save = {"header": {}, "body": {}}

                for c in variables:
                    c = c.replace("{", "")
                    c = c.replace("}", "")
                    to_save["body"][str(variables.index(c) + 1)] = my_csv_data[header_chars.index(c)]

                for h in header_vari:
                    if h != "":
                        h = h.replace("{", "")
                        h = h.replace("}", "")
                        to_save["header"][str(header_vari.index(h) + 1)] = my_csv_data[header_chars.index(h)]

                mobile = my_csv_data[header_chars.index(mobile)]
                if len(checks) and checks[0] == "yes":
                    mobile = request.POST['country_val'] + str(mobile)
            else:
                if len(checks) and checks[0] == "yes":
                    mobile = request.POST['country_val'] + request.POST['mobile']
                else:
                    mobile = request.POST['mobile']
                i = 1
                for c in variables:
                    to_save["body"][f"{str(i)}"] = c
                    i += 1
                i = 1
                for h in header_vari:
                    if h != "":
                        to_save["header"][f"{str(i)}"] = h
                        i += 1
            t = template
            print(to_save)
            if t.is_media:
                if t.med_id is None:
                    return "Please upload media from template management", ""
                else:
                    js = json.loads(t.med_id)
                    payload = {
                        "messaging_product": "whatsapp",
                        "recipient_type": "individual",
                        "to": f"{mobile}",
                        "type": "template",
                        "template": {
                            "name": f"{t.temp_name}",
                            "language": {
                                "code": f"{t.lang_code}"
                            },
                            "components": [
                                {
                                    "type": "header",
                                    "parameters": [
                                        {
                                            "type": "image",
                                            "image": {"link": f"{js['link']}"} if js["type"] == "what" else {
                                                "id": f"{js['med_obj']}"}
                                        }
                                    ]
                                },
                                {
                                    "type": "body",
                                    "parameters": []

                                }
                            ]
                        }
                    }
                    vars = to_save
                    if vars["header"]:
                        payload["template"]["components"].append({
                            "type": "header",
                            "parameters": []
                        })
                        payload["template"]["components"].append({
                            "type": "body",
                            "parameters": []
                        })
                        for i in vars["header"]:
                            payload["template"]["components"][0]["parameters"].append(
                                {"type": "text", "text": f"{vars['header'][i]}"})
                        for i in vars["body"]:
                            payload["template"]["components"][1]["parameters"].append(
                                {"type": "text", "text": f"{vars['body'][i]}"})
                    elif vars["body"] and (not vars['header']):
                        payload["template"]["components"].append({
                            "type": "body",
                            "parameters": []
                        })

                        for i in vars["body"]:
                            payload["template"]["components"][0]["parameters"].append({"type": "text", "text": f"{vars['body'][i]}"})
                    payload = json.dumps(payload)
            else:
                payload = {
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": f"{mobile}",
                    "type": "template",
                    "template": {
                        "name": f"{t.temp_name}",
                        "language": {
                            "code": f"{t.lang_code}"
                        },
                        "components": [

                        ]
                    }
                }
                vars = to_save
                if vars["header"]:
                    payload["template"]["components"].append({
                        "type": "header",
                        "parameters": []
                    })
                    payload["template"]["components"].append({
                        "type": "body",
                        "parameters": []
                    })
                    for i in vars["header"]:
                        payload["template"]["components"][0]["parameters"].append(
                            {"type": "text", "text": f"{vars['header'][i]}"})
                    for i in vars["body"]:
                        payload["template"]["components"][1]["parameters"].append(
                            {"type": "text", "text": f"{vars['body'][i]}"})
                elif vars["body"] and (not vars['header']):
                    payload["template"]["components"].append({
                        "type": "body",
                        "parameters": []
                    })

                    for i in vars["body"]:
                        payload["template"]["components"][0]["parameters"].append({"type": "text", "text": f"{vars['body'][i]}"})
                payload = json.dumps(payload)
            response = requests.request("POST", message_API, headers=header, data=payload)
            print(response.text)
            return JsonResponse({"text": response.text})
    else:
        return JsonResponse({"Error":"Login required to access this page"})

def advanceRecord(request):
    if "id" in request.COOKIES and User1.objects.get(id=request.COOKIES['id']).is_authenticated():
        c_id = request.GET.get('unique')
        record = Advance_Data.objects.filter(recordID_id=c_id)
        # url_data = Voice_API.objects.filter(u_ID_id=c_id)
        campaign = AdvanceCampaign.objects.filter(id=c_id)[0]

        providers = WA_MSG_Provider.objects.filter(user_id=request.COOKIES['id'])
        success = Advance_Data.objects.filter(recordID_id=c_id,status="Success").count()
        sent = Advance_Data.objects.filter(recordID_id=c_id,what_status="Sent").count()
        delivered = Advance_Data.objects.filter(recordID_id=c_id,what_status="delivered").count()
        read = Advance_Data.objects.filter(recordID_id=c_id,what_status="read").count()
        failed = Advance_Data.objects.filter(recordID_id=c_id,what_status="failed").count()
        try:
            comp_ratio = (read/record.count())*100
            response = render(request, "advanceRecord.html",
                          {"Campaign": campaign.CampaignName, "record": record, "url_data": "url_data",
                           "CampStat": campaign.CampaignStatus,
                           "providers": providers,
                           "success":{"c":success, "p":int((success/record.count())*100)}, 
                           "sent":sent, 
                           "delivered":delivered, "read":{"c":read,"p": int((read/record.count())*100)},
                           "total":record.count(), 
                           "failed":{"c":failed,"p": int((failed/record.count())*100)}, "comp_ratio":comp_ratio})
        
        except ZeroDivisionError:
            response = render(request, "advanceRecord.html",
                          {"Campaign": campaign.CampaignName, "record": record, "url_data": "url_data",
                           "CampStat": campaign.CampaignStatus,"providers": providers})
        response.set_cookie("camp_id", c_id)
        return response
        
    else:
        return JsonResponse({"Error":"Login required to access this page"})

def advanceSend(record, API, mode):
    url = API.message_API
    headers = API.header
    payload = ""
    if mode == "text":
        msg = record.text
        payload = json.dumps({
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": f"{record.mobile}",
            "type": "text",
            "text": {
                "preview_url": False,
                "body": f"{record.text}"
            }
        })
    elif mode == "temp":
        provider = WA_MSG_Provider.objects.get(provider_name=API.whatsapp_name)
        p = provider.id
        print(p, record.lang, record.template)
        msg = f"{record.template} [{record.lang}]"
        t = Templates.objects.get(temp_name=record.template, lang_code=record.lang, message_provider_id=p)

        if t.is_media:
            if t.med_id is None:
                return "Please upload media from template management", ""
            else:
                js = json.loads(t.med_id)
                payload = {
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": f"{record.mobile}",
                    "type": "template",
                    "template": {
                        "name": f"{record.template}",
                        "language": {
                            "code": f"{record.lang}"
                        },
                        "components": [
                            {
                                "type": "header",
                                "parameters": [
                                    {
                                        "type": "image",
                                        "image": {"link": f"{js['link']}"} if js["type"] == "what" else {
                                            "id": f"{js['med_obj']}"}
                                    }
                                ]
                            }
                        ]
                    }
                }
                vars = record.variables
                if vars["body"] and (not vars['header']):
                    params = []
                    for i in vars["body"]:
                        
                        params.append(
                            {"type": "text", "text": f"{vars['body'][i]}"})
                    payload["template"]["components"].append({
                        "type": "body",
                        "parameters": params
                    })

                    
                payload = json.dumps(payload)
                
        else:
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": f"{record.mobile}",
                "type": "template",
                "template": {
                    "name": f"{record.template}",
                    "language": {
                        "code": f"{record.lang}"
                    },
                    "components": [

                    ]
                }
            }
            vars = record.variables
            if vars["header"]:
                payload["template"]["components"].append({
                    "type": "header",
                    "parameters": []
                })
                payload["template"]["components"].append({
                    "type": "body",
                    "parameters": []
                })
                for i in vars["header"]:
                    payload["template"]["components"][0]["parameters"].append(
                        {"type": "text", "text": f"{vars['header'][i]}"})
                for i in vars["body"]:
                    payload["template"]["components"][1]["parameters"].append(
                        {"type": "text", "text": f"{vars['body'][i]}"})
            elif vars["body"] and (not vars['header']):
                payload["template"]["components"].append({
                    "type": "body",
                    "parameters": []
                })

                for i in vars["body"]:
                    payload["template"]["components"][0]["parameters"].append({"type": "text", "text": f"{vars['body'][i]}"})
            payload = json.dumps(payload)
            

    response = requests.request("POST", url, headers=headers, data=payload)

    record.voiceshoot_req = url + str(headers)
    record.voiceshoot_res = response.text
    record.save()
    try:
        id = json.loads(response.text)["messages"][0]["id"]
        record.msg_id = id
        record.save()
        Message_History.objects.create(message=msg, msg_type="send", customer_number=record.mobile, 
                                        api_number=provider.phone_no, user_id=provider.user_id, provider_id=p, msg_id=id)
        return f"Message sent Successfully.\nOn Whatsapp Number {record.mobile}\nMessage ID is:" + id, "http://craftizen.org/wp-content/uploads/2019/02/successful_payment_388054.png"
    except KeyError:
        return "Something Went Wrong.", "http://craftizen.org/wp-content/uploads/2019/02/global_hint_failure_595796.png"


def advanceStart(request):
    if "id" in request.COOKIES and User1.objects.get(id=request.COOKIES['id']).is_authenticated():
        id = request.GET.get('id')
        mode = request.GET.get('mode')
        record = Advance_Data.objects.get(id=id)
        red_id = record.recordID_id
        url = f"/advanceRecord?unique={red_id}"
        if record.status == "Pending":
            API = Voice_API.objects.filter(whatsapp_name=record.sender_name)[0]
            resp, img_link = advanceSend(record, API, mode)
            return JsonResponse({"url": url, "text": resp, "img": img_link})
        else:
            return JsonResponse({"url": url, "text": "Message already sent.", "img": "img_link"})
    else:
        return JsonResponse({"Error":"Login required to access this page"})
    


def delete_oldData(request):
    try:
        print("Old Data Delete")
        today = datetime.datetime.now(timezone.utc) + datetime.timedelta(hours=5.5) - datetime.timedelta(days=6)
        o_data = OutBox.objects.filter(send_time__lte=today)
        for i in o_data:
            i.delete()
        return JsonResponse({"status":True})
    except:
        return JsonResponse({"status":False})
    
def validity_update(request):
    try:
        today = datetime.date.today()
        user = User1.objects.filter(validity__lte=today)
        user.update(is_active=0)
        print(user)
        return JsonResponse({"Status":True})
    except:
        return JsonResponse({"Status":False})
    

def conversation_update(request):
    try:
        set_days = int(APP_Setting.objects.get(key="BLOCK_NUMBER_LIMIT").value)
        hours = datetime.datetime.now(timezone.utc)+ datetime.timedelta(hours=5.5) - datetime.timedelta(hours=24)
        days = datetime.datetime.now(timezone.utc)+ datetime.timedelta(hours=5.5) - datetime.timedelta(days=set_days)
        c_data = Conversation_Status.objects.filter(received_time__lte=hours).update(conversation_status="Pending")
        Conversation_Status.objects.filter(inbox_msg="NO").update(conversation_status="Stopped")
        Conversation_Status.objects.filter(received_time__lte=days).update(conversation_status="Stopped")
        return JsonResponse({"status":True})
    except:
        return JsonResponse({"status":False})

def customerBotState(request):
    if "id" in request.COOKIES and User1.objects.get(id=request.COOKIES['id']).is_authenticated():
        bot_id = request.GET['bid']
        p_id = request.GET['pid']
        data = CustomerBotStop.objects.filter(provider_id=p_id)
        return render(request, "customerBotState.html", {"data":data})
    else:
        return JsonResponse({"Error":"Login required to access this page"})

def botSettings(request):
    if "id" in request.COOKIES and User1.objects.get(id=request.COOKIES['id']).is_authenticated():
        if request.method == "POST":
            msg_prods = WA_MSG_Provider.objects.get(phone_no=request.POST['provider'])
            if not What_Bot.objects.filter(provider_id=msg_prods.id):
                What_Bot.objects.create(bot_name=msg_prods.provider_name + "_Bot", message_pair={},
                                        provider_id=msg_prods.id, user_id=msg_prods.user_id)
            else:
                messages.error(request, "Bot already exist for provider")
            return redirect("/botSettings")
        else:
            providers = WA_MSG_Provider.objects.filter(user_id=request.COOKIES['id'])
            bots = What_Bot.objects.filter(user_id=request.COOKIES['id'])
            return render(request, "botSettings.html", {"bots": bots, "providers": providers})
    else:
        return JsonResponse({"Error":"Login required to access this page"})

def button_status(request):
    if "id" in request.COOKIES and User1.objects.get(id=request.COOKIES['id']).is_authenticated():
        msg_prods = WA_MSG_Provider.objects.get(phone_no=request.GET['name'])
        bot = What_Bot.objects.get(bot_name=msg_prods.provider_name + "_bot")
        btn_id = bot.id
        if bot.is_on:
            btn_cls = "btn btn-danger"
            btn_text = "Off"
        else:
            btn_cls = "btn btn-success"
            btn_text = "On"
        return JsonResponse({"btn_cls": btn_cls, "btn_text": btn_text, "btn_id":btn_id})
    else:
        return JsonResponse({"Error":"Login required to access this page"})

def addMesPair(request):
    if "id" in request.COOKIES and User1.objects.get(id=request.COOKIES['id']).is_authenticated():
        phone = ""
        if request.method == "POST":
            try:
                rec = str(request.POST["rec_mes"]).split(",")
                rec = [x.lower().strip() for x in rec if x not in [" ",""]]
            except Exception as e:
                rec = str(request.POST["rec_mes"]).lower()
            
            bot_id = request.POST['bid']
            phone = request.POST['phone']
            pid = WA_MSG_Provider.objects.get(phone_no=phone).id
        
            data = Bot_Auto_Reply.objects.filter(provider_id=pid)
            
            checked_list = []
            for d in data:
                for r in rec:
                    if "," not in d.receive_message:
                        to_check = d.receive_message.replace("['","").replace("']","").split(" ")
                    else:
                        to_check = d.receive_message
                    
                    if r in to_check:
                        print(d.receive_message)
                        checked_list.append(r)
            
            checked_list = [j for j in filter(lambda x: x != "", checked_list)]
            print(checked_list)
            if not checked_list:        
                bot = What_Bot.objects.get(pk=bot_id)
                rep_opt = request.POST['reply_option']
                if rep_opt == "catalogue":
                    save_urls = []
                    save_name = []
                    zip_file = request.FILES['catalogue_zip']
                    provider_name = WA_MSG_Provider.objects.get(pk=bot.provider_id).provider_name
                    if not os.path.exists("media_objects/UnzippedFiles/"+provider_name):
                                os.makedirs("media_objects/UnzippedFiles/"+provider_name) 
                    i = 1
                    with zipfile.ZipFile(zip_file, mode="r") as archive:
                        
                        for fileName in archive.namelist():
                            file_type = fileName.split('.')[-1]
                            file_type = file_type.lower()
                            file= archive.extract(fileName, "media_objects/UnzippedFiles/"+provider_name)    
                            save_urls.append({"type":file_type, "link":f"{settings.HOST_URL}/media/UnzippedFiles/{provider_name}/{fileName}"})
                            i+=1
                        save_name= f"{(zip_file.name).split('.')[0]} - {str(i)} Files"
                    Bot_Auto_Reply.objects.create(receive_message=rec, msg_type=rep_opt, reply_message={rep_opt:save_urls},show_reply_message=save_name, bot_id=bot_id, provider_id=bot.provider_id) 
                    
                elif rep_opt == "template":
                    rep = request.POST["reply_mes"]
                    temp_obj = Templates.objects.get(temp_id=rep)
                    temp_name = f"{temp_obj.temp_name} [{temp_obj.lang_code}]"
                    Bot_Auto_Reply.objects.create(receive_message=rec, msg_type=rep_opt, reply_message={rep_opt:rep},show_reply_message=temp_name, bot_id=bot_id, provider_id=bot.provider_id)
                    print(rec, rep, bot_id)
                elif rep_opt == "text":
                    rep = request.POST["reply_mes"]
                    Bot_Auto_Reply.objects.create(receive_message=rec, msg_type=rep_opt, reply_message={rep_opt:rep},show_reply_message=rep, bot_id=bot_id, provider_id=bot.provider_id)
                    print(rec, rep, bot_id)
                elif rep_opt == "btn-w-text":
                    tex_rep = request.POST['text']
                    btn_c = request.POST['btn-count']
                    btn_text = request.POST.getlist('btn-text[]')
                    rep = {"btext":tex_rep, "bcount":btn_c, "btn_text":btn_text}
                    print(tex_rep, btn_c, btn_text)
                    Bot_Auto_Reply.objects.create(receive_message=rec, msg_type=rep_opt, reply_message={rep_opt:rep}, show_reply_message=tex_rep+"With Buttons" + str(btn_text), bot_id=bot_id, provider_id=bot.provider_id)
                elif rep_opt == "list-btn":
                    body_tex = request.POST['body-text']
                    button_text = request.POST['btn-text']
                    list_c = request.POST['list-count']
                    list_title = request.POST.getlist('list-title[]')
                    list_desc = request.POST.getlist('list-desc[]')
                    rep = {"body_tex":body_tex,"button_text":button_text, "list_c":list_c, "list_title":list_title, "list_desc":list_desc}
                    Bot_Auto_Reply.objects.create(receive_message=rec, msg_type=rep_opt, reply_message={rep_opt:rep}, show_reply_message=body_tex+"With button list", bot_id=bot_id, provider_id=bot.provider_id)
                messages.success(request, "Message Added Succesfully")
            else:
                messages.error(request, "Message Already exist")
                print()
            
            return redirect(f"/addMesPair?bid={bot_id}&pid={pid}")
        else:
            bot_id = request.GET["bid"]
            pid = request.GET['pid']
            phone = WA_MSG_Provider.objects.get(pk=pid).phone_no
            bot_reply = Bot_Auto_Reply.objects.filter(bot_id=bot_id)
            return render(request, "Bot_Messages.html", {"data": bot_reply, "pid":phone, "bid":bot_id, "bot_state":What_Bot.objects.get(pk=bot_id).is_on})
    else:
        return JsonResponse({"Error":"Login required to access this page"})

def stopBot(request):
    if "id" in request.COOKIES and User1.objects.get(id=request.COOKIES['id']).is_authenticated():
        user_num = request.GET['user']
        provider = request.GET['provider']
        p = WA_MSG_Provider.objects.get(phone_no=provider)
        data = CustomerBotStop.objects.filter(user_number=user_num, provider_name=p.provider_name)
        if not data:
            CustomerBotStop.objects.create(user_number=user_num, provider_name=p.provider_name, provider_id=p.id)
        return redirect("/showMessages")
    else:
        return JsonResponse({"Error":"Login required to access this page"})

def toggle_Bot_Stat(request):
    if "id" in request.COOKIES and User1.objects.get(id=request.COOKIES['id']).is_authenticated():
        if request.GET['type'] == 'bot':
            bot_id = request.GET['bot_id']
            bot = What_Bot.objects.get(pk=bot_id)
            if bot.is_on:
                bot.is_on = False
            elif not bot.is_on:
                bot.is_on = True
            bot.save()
            red_url = "/botSettings"
        elif request.GET['type'] == "row":
            row_id = request.GET['reply_row_id']
            reply_row = Bot_Auto_Reply.objects.get(pk=row_id)
            if reply_row.is_active:
                reply_row.is_active = False
            elif not reply_row.is_active:
                reply_row.is_active = True
            reply_row.save()
            red_url = f"/addMesPair?bid={reply_row.bot_id}&pid={reply_row.provider_id}"

        
        return redirect(red_url)
    else:
        return JsonResponse({"Error":"Login required to access this page"})

def editAutoReply(request):
    if "id" in request.COOKIES and User1.objects.get(id=request.COOKIES['id']).is_authenticated():
        if request.method == "POST":
            try:
                rec = str(request.POST["rec_mes"]).split(",")
                rec = [x.lower().strip() for x in rec if x not in [" ",""]]
            except Exception as e:
                rec = str(request.POST["rec_mes"]).lower()
            
            auto_rep_id = request.POST['mid']
            bot_id = request.POST['bid']
            phone = request.POST['pid']
            pid = WA_MSG_Provider.objects.get(phone_no=phone).id
        
            data = Bot_Auto_Reply.objects.filter(provider_id=pid)
            data = data & Bot_Auto_Reply.objects.exclude(pk=auto_rep_id)
            print(data)
            checked_list = []
            for d in data:
                for r in rec:
                    check = d.receive_message.replace("[","").replace("]","").split(" ")
                    if r in check:
                        print(d.receive_message)
                        checked_list.append(r)
            
            checked_list = [j for j in filter(lambda x: x != "", checked_list)]
            print(checked_list)
            if not checked_list:        
                rep = request.POST['reply_mes']
                if request.POST['rep_type'] == "text":      
                    Bot_Auto_Reply.objects.filter(pk=auto_rep_id).update(receive_message=rec, reply_message={"text":rep}, show_reply_message=rep)
                    messages.success(request, "Message Updated Succesfully")
                if request.POST['rep_type'] == "template":
                    temp_name = Templates.objects.get(temp_id=rep)
                    messages.success(request, "Message Updated Succesfully")
                    Bot_Auto_Reply.objects.filter(pk=auto_rep_id).update(receive_message=rec, reply_message={"template":rep}, show_reply_message=f"{temp_name.temp_name} [{temp_name.lang_code}]")
            pid = WA_MSG_Provider.objects.get(phone_no=request.POST['pid']).id
            return redirect(f"/addMesPair?bid={bot_id}&pid={pid}")
        else:  
            auto_rep_id = request.GET['mid']
            res_rep = Bot_Auto_Reply.objects.get(pk=auto_rep_id)
            my_list = res_rep.receive_message
            my_list = my_list.replace("\'","").replace("[","").replace("]","")
            data = {"mid":res_rep.id,"receive_msg":my_list, "reply_message":res_rep.reply_message, "type":res_rep.msg_type}
            return JsonResponse(data)
    else:
        return JsonResponse({"Error":"Login required to access this page"})


def ShowFiles(request):
    if "id" in request.COOKIES and User1.objects.get(id=request.COOKIES['id']).is_authenticated():
        uid = User1.objects.get(phone_no=request.COOKIES["mobile"])
        rid = request.GET['rid']
        data = Bot_Auto_Reply.objects.get(pk=rid).reply_message
        files = data["catalogue"]
        return JsonResponse(files, safe=False)
    else:
        return JsonResponse({"Error":"Login required to access this page"})


def check_bot_set(user, provider, to, message, msg_id, msg_log):
    for bot in Bot_Auto_Reply.objects.filter(provider_id=provider):
        if "," not in bot.receive_message:
            to_check = bot.receive_message.replace("['","").replace("']","").split(",")
            
        else:
            ar = bot.receive_message.split(",")
            to_check = [x.replace("[","").replace("]","").replace("'","").strip() for x in ar]
            
        if bot.is_active and message.lower() in to_check:
            b = bot
            break
        
    # elif bot and (not bot[0].is_active):
        
    else:
        default = Bot_Auto_Reply.objects.filter(provider_id=provider, receive_message__contains="*")
        
        if default and default[0].is_active:
            b = default[0]
            print("Default reply")
        else:
            return "Auto reply and Default reply Blocked"
    print("reach", b)
    api = Voice_API.objects.get(whatsapp_name=WA_MSG_Provider.objects.get(pk=provider).provider_name)
    if "text" in b.reply_message.keys():
        payload = json.dumps({
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": f"{to}",
        "type": "text",
        "text": {
            "preview_url": False,
            "body": f"{b.reply_message['text']}"
        }
        })
        response = requests.post(url=api.message_API, headers=api.header, data=payload)
        msg_log.reply = b.reply_message['text']
        msg_log.request = api.message_API
        msg_log.send_time = datetime.datetime.now(timezone.utc) + datetime.timedelta(hours=5.5)
        msg_log.response = response.text
        try:
            msg_id = json.loads(response.text)["messages"][0]['id']
            msg_log.msg_id = msg_id
            msg_log.save()
        except:
            msg_id = ""
            msg_log.save()
        SubMessageLog.objects.create(parent_msg_id=msg_log.id, reply_number=msg_log.reply_number,
                                    user_id=msg_log.user_id, reply=b.reply_message['text'], request=api.message_API,
                                    send_time=datetime.datetime.now(
                                        timezone.utc) + datetime.timedelta(hours=5.5),
                                    response=response.text, msg_id=msg_id)
        pid = WA_MSG_Provider.objects.get(phone_no=msg_log.reply_number).id
        Message_History.objects.create(message=b.reply_message['text'], msg_type="send", customer_number=msg_log.sender_number, 
                                        api_number=msg_log.reply_number, user_id=msg_log.user_id, provider_id=pid, msg_id=msg_id)
        return response.text
    if "template" in b.reply_message.keys():
        record = Templates.objects.get(temp_id=b.reply_message["template"])
        if record.is_media:
            if record.med_id is None:
                return "Please upload media from template management", ""
            else:
                js = json.loads(record.med_id)
                payload = json.dumps({
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": f"{to}",
                    "type": "template",
                    "template": {
                        "name": f"{record.temp_name}",
                        "language": {
                            "code": f"{record.lang_code}"
                        },
                        "components": [
                            {
                                "type": "header",
                                "parameters": [
                                    {
                                        "type": "image",
                                        "image": {"link": f"{js['link']}"} if js["type"] == "what" else {
                                            "id": f"{js['med_obj']}"}
                                    }
                                ]
                            }
                        ]
                    }
                })
        else:
            payload = json.dumps({
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": f"{to}",
                "type": "template",
                "template": {
                    "name": f"{record.temp_name}",
                    "language": {
                        "code": f"{record.lang_code}"
                    },
                }
            })
        
        response = requests.post(url=api.message_API, headers=api.header, data=payload)
        msg_log.reply = f"{record.temp_name} [{record.lang_code}]"
        msg_log.request = api.message_API
        msg_log.send_time = datetime.datetime.now(timezone.utc) + datetime.timedelta(hours=5.5)
        msg_log.response = response.text
        try:
            msg_id = json.loads(response.text)["messages"][0]['id']
            msg_log.msg_id = msg_id
            msg_log.save()
        except:
            msg_id = ""
            msg_log.save()
        SubMessageLog.objects.create(parent_msg_id=msg_log.id, reply_number=msg_log.reply_number,
                                    user_id=msg_log.user_id, reply=f"{record.temp_name} [{record.lang_code}]", request=api.message_API,
                                    send_time=datetime.datetime.now(
                                        timezone.utc) + datetime.timedelta(hours=5.5),
                                    response=response.text, msg_id=msg_id)
        pid = WA_MSG_Provider.objects.get(phone_no=msg_log.reply_number).id
        Message_History.objects.create(message=f"{record.temp_name} [{record.lang_code}]", msg_type="send", customer_number=msg_log.sender_number, 
                                        api_number=msg_log.reply_number, user_id=msg_log.user_id, provider_id=pid, msg_id=msg_id)
        return response.text
    if "catalogue" in b.reply_message.keys():
        files = b.reply_message["catalogue"]
        count = 1
        for f in files:
            if f['type'] == 'pdf':
                print(f)
                payload = json.dumps({
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": f"{to}",
                    "type": "document",
                    "document": {
                        "link": f["link"],
                        "caption": f"Document {count}"
                    }
                })
            else:
                print(f)
                payload = json.dumps({
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": f"{to}",
                    "type": "image",
                    "image": {
                        "link": f["link"],
                        "caption": f"Document {count}"
                    }
                })
            count += 1
            response = requests.post(url=api.message_API, headers=api.header, data=payload)
            reply = f["link"].split("/")[-1]
            msg_log.reply = reply
            msg_log.request = api.message_API
            msg_log.send_time = datetime.datetime.now(timezone.utc) + datetime.timedelta(hours=5.5)
            msg_log.response = response.text
            try:
                msg_id = json.loads(response.text)["messages"][0]['id']
                msg_log.msg_id = msg_id
                msg_log.save()
            except:
                msg_id = ""
                msg_log.save()
            SubMessageLog.objects.create(parent_msg_id=msg_log.id, reply_number=msg_log.reply_number,
                                        user_id=msg_log.user_id, reply=reply, request=api.message_API,
                                        send_time=datetime.datetime.now(
                                            timezone.utc) + datetime.timedelta(hours=5.5),
                                        response=response.text, msg_id=msg_id)
            pid = WA_MSG_Provider.objects.get(phone_no=msg_log.reply_number).id
            Message_History.objects.create(message=reply, msg_type="send", customer_number=msg_log.sender_number, 
                                        api_number=msg_log.reply_number, user_id=msg_log.user_id, provider_id=pid, msg_id=msg_id)
        return response.text
    if "btn-w-text" in b.reply_message.keys():
        btn_data = b.reply_message['btn-w-text']
        
        payload = {
                "messaging_product": "whatsapp",    
                "recipient_type": "individual",
                "to": f"{to}",
                "type": "interactive",
                "interactive": { "type": "button",
                                "body":{"text":btn_data["btext"]},
                                "action": {"buttons": []}
                                }
                }
        for i in range (int(btn_data["bcount"])):
            payload["interactive"]["action"]["buttons"].append({"type": "reply","reply": {"id": i+1,"title": btn_data["btn_text"][i]}})
        payload = json.dumps(payload)
        response = requests.post(url=api.message_API, headers=api.header, data=payload)
        reply = btn_data["btext"] + "(With buttons reply)"
        msg_log.reply = reply
        msg_log.request = api.message_API
        msg_log.send_time = datetime.datetime.now(timezone.utc) + datetime.timedelta(hours=5.5)
        msg_log.response = response.text
        try:
            msg_id = json.loads(response.text)["messages"][0]['id']
            msg_log.msg_id = msg_id
            msg_log.save()
        except:
            msg_id = ""
            msg_log.save()
        SubMessageLog.objects.create(parent_msg_id=msg_log.id, reply_number=msg_log.reply_number,
                                    user_id=msg_log.user_id, reply=reply, request=api.message_API,
                                    send_time=datetime.datetime.now(
                                        timezone.utc) + datetime.timedelta(hours=5.5),
                                    response=response.text, msg_id=msg_id)
        pid = WA_MSG_Provider.objects.get(phone_no=msg_log.reply_number).id
        Message_History.objects.create(message=reply, msg_type="send", customer_number=msg_log.sender_number, 
                                        api_number=msg_log.reply_number, user_id=msg_log.user_id, provider_id=pid, msg_id=msg_id)
        return response.text
    if "list-btn" in b.reply_message.keys():
        data = b.reply_message["list-btn"]
        payload = {"messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": f"{to}",
                    "type": "interactive",
                    "interactive": {
                        "type": "list",
                        "body": {
                        "text": f"{data['body_tex']}"
                        },
                        "action": {
                        "button": f"{data['button_text']}",
                        "sections": [
                            {
                            "title": f"{data['button_text']}",
                            "rows": []
                            }
                        ]
                        }
                    }
                    }
        for i in range(int(data["list_c"])):
            payload["interactive"]["action"]["sections"][0]["rows"].append({
                                "id": f"{i+1}",
                                "title": f"{data['list_title'][i]}",
                                "description": f"{data['list_desc'][i]}"
                                })
        payload = json.dumps(payload)
        
        response = requests.post(url=api.message_API, headers=api.header, data=payload)
        reply = data["body_tex"] + "(With list reply)"
        msg_log.reply = reply
        msg_log.request = api.message_API
        msg_log.send_time = datetime.datetime.now(timezone.utc) + datetime.timedelta(hours=5.5)
        msg_log.response = response.text
        try:
            msg_id = json.loads(response.text)["messages"][0]['id']
            msg_log.msg_id = msg_id
            msg_log.save()
        except:
            msg_id = ""
            msg_log.save()
        SubMessageLog.objects.create(parent_msg_id=msg_log.id, reply_number=msg_log.reply_number,
                                    user_id=msg_log.user_id, reply=reply, request=api.message_API,
                                    send_time=datetime.datetime.now(
                                        timezone.utc) + datetime.timedelta(hours=5.5),
                                    response=response.text, msg_id=msg_id)
        pid = WA_MSG_Provider.objects.get(phone_no=msg_log.reply_number).id
        Message_History.objects.create(message=reply, msg_type="send", customer_number=msg_log.sender_number, 
                                        api_number=msg_log.reply_number, user_id=msg_log.user_id, provider_id=pid, msg_id=msg_id)
        return response.text

def prepare_TempForChat(pid, tname, tcode):
    
    json_data = Chat_Templates.objects.filter(message_provider_id=pid)
    
    temp_compo = json_data[0]['components']
    temp_preview = {}
    for i in range(len(temp_compo)):
        if temp_compo[i]['type'].lower() == "header" and temp_compo[i]['format'].lower() == "text":
            temp_preview[temp_compo[i]["type"]] = temp_compo[i]["text"]
        elif temp_compo[i]['type'].lower() == "header" and temp_compo[i]['format'].lower() in ["image", "document"]:
            temp_preview[temp_compo[i]["type"]] = temp_compo[i]["example"]["header_handle"][0]
            pass
        elif temp_compo[i]['type'].lower() == "body":
            temp_preview[temp_compo[i]["type"]] = temp_compo[i]["text"]
        elif temp_compo[i]['type'].lower() == "buttons":
            cont = 0
            for b, d in enumerate(temp_compo[i]["buttons"]):
                temp_preview[temp_compo[i]["type"] + str(b + 1)] = temp_compo[i]["buttons"][b]["text"]
                cont += 1
        elif temp_compo[i]['type'].lower() == "footer":
            temp_preview[temp_compo[i]["type"]] = temp_compo[i]["text"]
    
    temp_look = ""
    for i in temp_preview:
        temp_look += f'''
    {temp_preview[i]}\n
    
    '''
    return temp_preview

def prepare_chat(cus_list, uname):
    time_data  = {}
    
    for i in range(len(cus_list)):
        sub = ""
        time_data[cus_list[i]] = []

        if i < len(cus_list)-1:
            sub = SubMessageLog.objects.filter(parent_msg_id=cus_list[i].id, send_time__gte=cus_list[i].received_time, 
                    send_time__lt=cus_list[i+1].received_time)
        else:
            sub = SubMessageLog.objects.filter(parent_msg_id=cus_list[i].id, send_time__gte=cus_list[i].received_time)
        for s in sub:
            ext = s.reply.split(".")[-1]
            print(ext)
            if ext in ['jpg', 'jpeg', 'png']:
                if "http" in s.reply:
                    time_data[cus_list[i]].append({"time":s.send_time,"type":"img","reply":s.reply, "status":s.status})
                else:
                    time_data[cus_list[i]].append({"time":s.send_time,"type":"img","status":s.status,"reply":f'http://wotsapp-campaign.bonrix.in:8000/media/UnzippedFiles/{uname}/{s.reply}'})
            elif ext in ['docx', 'pdf']:
                time_data[cus_list[i]].append({"time":s.send_time,"type":ext,"status":s.status,"name":s.reply.split("/")[-1],"reply":s.reply})
            elif "[" in s.reply or "]" in s.reply:
                temp_name = s.reply.split(" ")[0]
                u_id = s.user_id
                lang_code = s.reply.split(" ")[1].replace("[","").replace("]","")
                try:
                    temp = Chat_Templates.objects.get(temp_name=temp_name, lang_code=lang_code, user_id=u_id)
                    if "HEADER" in temp.temp_preview and "http" in temp.temp_preview['HEADER']:
                        temp.temp_preview["HEADER"] = s.media_content
                    time_data[cus_list[i]].append({"type":"temp", "reply":temp.temp_preview, "time":s.send_time, "status":s.status})
                except:
                    time_data[cus_list[i]].append({"type":"temp", "reply":temp_name, "time":s.send_time, "status":s.status})
            else:
                time_data[cus_list[i]].append({"type":"text","reply":s.reply, "time":s.send_time, "status":s.status})
            
    return time_data


def what_gui(request):
    if "id" in request.COOKIES and User1.objects.get(id=request.COOKIES['id']).is_authenticated():
        uid = request.COOKIES["id"]
        try:
            to = request.GET['to']
            rnum  =request.GET['from']
            customers = MessageLog.objects.filter(reply_number=rnum, sender_number=to).order_by("received_time")
        except:
            customers = MessageLog.objects.filter(user_id=uid).order_by("received_time")
            to, rnum = customers[len(customers)-1].sender_number, customers[len(customers)-1].reply_number
        
        users = MessageLog.objects.filter(user_id=uid).values("sender_number", "reply_number").distinct()
        act_users = users
        # .reverse()[:5]
        # arc_users = users.reverse()[5:]
        for u in act_users:
            if u['sender_number'] == to:
                u["active"] = "active"
        pname = WA_MSG_Provider.objects.get(phone_no=rnum).provider_name
        return render(request, "what_GUI.html", {"from":rnum, "to":to,"provider":pname,
        "act_users": act_users,"time_data":prepare_chat(customers, pname)})
        # "arc_users":arc_users,
    else:
        return JsonResponse({"Error":"Login required to access this page"})

@csrf_exempt
def chat_msg(request):
    if "id" in request.COOKIES and User1.objects.get(id=request.COOKIES['id']).is_authenticated():
        data = json.loads(request.body)
        to = data['to']
        fom = data['from']
        msg = str(data['msg'])
        mes_type = data['type']
        
        api = Voice_API.objects.get(whatsapp_name=fom)
        provider = WA_MSG_Provider.objects.get(provider_name=fom)
        media_content = ""
        if mes_type == "text":
            payload = json.dumps({
                        "messaging_product": "whatsapp",
                        "recipient_type": "individual",
                        "to": f"{to}",
                        "type": "text",
                        "text": {
                            "preview_url": False,
                            "body": f"{msg}"
                        }
                    })
        
        elif mes_type == "temp":
            
            tname = msg.split("-")[0]
            tcode = msg.split("-")[1]
            msg = f"{tname} [{tcode}]"
            media_content = ""
            t = Chat_Templates.objects.get(message_provider_id=provider.id, temp_name=tname, lang_code=tcode)
            if t.is_media:
                if t.med_id is None:
                    
                    return JsonResponse({"message": "Please Upload media content first."})
                else:
                    js = json.loads(t.med_id)
                    media_content = js['link'] if js["type"] == "what" else js['med_obj']
                    payload = json.dumps({
                        "messaging_product": "whatsapp",
                        "recipient_type": "individual",
                        "to": f"{to}",
                        "type": "template",
                        "template": {
                            "name": f"{tname}",
                            "language": {
                                "code": f"{tcode}"
                            },
                            "components": [
                                {
                                    "type": "header",
                                    "parameters": [
                                        {
                                            "type": "image",
                                            "image": {"link": f"{js['link']}"} if js["type"] == "what" else {
                                                "id": f"{js['med_obj']}"}
                                        }
                                    ]
                                }
                            ]
                        }
                    })
            else:
                payload = json.dumps({
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": f"{to}",
                    "type": "template",
                    "template": {
                        "name": f"{tname}",
                        "language": {
                            "code": f"{tcode}"
                        },

                    }
                })
        elif mes_type == "image":
            payload = json.dumps({
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": f"{to}",
                "type": "image",
                "image": {
                    "link": msg,
                }
            })
        elif mes_type == "pdf" or mes_type == "doc":
            payload = json.dumps({
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": f"{to}",
                    "type": "document",
                    "document": {
                        "link": msg,
                    }
                })
        
        response = requests.post(url=api.message_API, data=payload, headers=api.header)
        
        msg_log = MessageLog.objects.filter(sender_number=to, reply_number=provider.phone_no)
        
        msg_log = msg_log[len(msg_log) -1]
        
        msg_log.reply = msg
        msg_log.media_content = media_content
        msg_log.request = api.message_API
        msg_log.response = response.text
        msg_log.send_time = datetime.datetime.now(timezone.utc) + datetime.timedelta(hours=5.5)
        try:
            msg_id = json.loads(response.text)["messages"][0]['id']
            msg_log.msg_id = msg_id
            msg_log.save()
            # messages.success(request, f"Message sent successfully to {msg_log.sender_number}")
        except:
            msg_id = ""
            msg_log.save()
            # messages.error(request, f"Message not sent to {msg_log.sender_number}")
        SubMessageLog.objects.create(parent_msg_id=msg_log.id, reply_number=msg_log.reply_number,
                                        user_id=msg_log.user_id, reply=msg,
                                        request=api.message_API,
                                        send_time=datetime.datetime.now(
                                            timezone.utc) + datetime.timedelta(hours=5.5),
                                        response=response.text, msg_id=msg_id, media_content=media_content)
        pid = WA_MSG_Provider.objects.get(phone_no=msg_log.reply_number).id
        Message_History.objects.create(message=msg, msg_type="send", customer_number=msg_log.sender_number, 
                                        api_number=msg_log.reply_number, user_id=msg_log.user_id, provider_id=pid, msg_id=msg_id)
   

        return JsonResponse({"response":response.text})
    else:
        return JsonResponse({"Error":"Login required to access this page"})


def change_chat(request):
    if "id" in request.COOKIES and User1.objects.get(id=request.COOKIES['id']).is_authenticated():
        uid = request.COOKIES["id"]
        to = request.GET['to']
        customers = MessageLog.objects.filter(user_id=uid, sender_number=to).order_by("received_time")
        return JsonResponse({"chat":  prepare_chat(customers)})
    else:
        return JsonResponse({"Error":"Login required to access this page"})

def testgui(request):
    return render(request, "what_GUI.html")


def createTemp(request):
    if "id" in request.COOKIES and User1.objects.get(id=request.COOKIES['id']).is_authenticated():
        if request.method == "POST":
            if request.POST["type"] == "multiple":
                template_name = str(request.POST['temp-name'])
                provider = request.POST["provider"]
                data = WA_MSG_Provider.objects.get(phone_no=provider)
                database_temps = New_Templates.objects.filter(message_provider_id=data.id).values("temp_id")
                table_temp_id_list = [x['temp_id'] for x in database_temps]
                body = request.POST["body"]
                language = request.POST["language"]
                category = request.POST['category']

                response = requests.get(
                    f"https://graph.facebook.com/v15.0/{data.business_id}/message_templates?access_token={data.token}")
                try:
                    response = json.loads(response.text)
                    res_dt = response['data']
                except KeyError:
                    print("Fetch Problem")
                    return JsonResponse({"response":response})

                file = request.FILES.get('myfile')
                rows, f_type, header_chars = prepare(file, request.COOKIES['id'])

                if f_type == "":
                    header_chars = header_chars.split(",")

                    for i in range(1, len(rows) - 1):

                        cols = rows[i].split(",")

                        temp_n = cols[header_chars.index(template_name)].replace(" ","_").lower()

                        temp_b = cols[header_chars.index(body)]

                        for td in res_dt:
                            print("Checking")
                            ind = next((index for (index, c) in enumerate(td['components']) if c["type"] == "BODY"), None)
                            if ind and (td['id'] not in table_temp_id_list):
                                c = td["components"][ind]
                                excel_text = regexpstring(temp_b, 0).replace("{#var#}", "(.*)")
                                p = re.compile(excel_text)
                                variables = p.findall(regexpstring(c['text'], 1))
                                if variables:
                                    print("Matched")
                                    New_Templates.objects.create(user_id=request.COOKIES['id'], message_provider_id=data.id, temp_name=td['name'],
                                                    text_msg=regexpstring(temp_b, 0), text_converted=c['text'], lang_code=td['language'], category=td['category'],
                                                    temp_id=td['id'], status=td['status'])
                                    break
                        else:  
                            myli = temp_b.split("{#var#}")
                            myli = [j for j in filter(lambda x: x != "", myli)]

                            vars = temp_b.count("{#var#}")

                            final = ""
                            n = 1
                            for i in myli:
                                if n > vars:
                                    final += i
                                    break
                                final += i + "{{"+str(n)+"}}"
                                n+=1
                            final += " Thank you"
                            

                            payload = {
                                "name": temp_n,
                                "components":[
                                    {
                                        "type":"HEADER",
                                        "format":"TEXT",
                                        "text": data.temp_header
                                    },
                                    {
                                        "type":"BODY",
                                        "text":final
                                    },
                                    {
                                        "type":"FOOTER",
                                        "text":data.temp_footer
                                    }
                                ],
                                "language":language,
                                "category":category
                            }
                            if "isbutton" in request.POST:
                                payload["components"].append({"type": "BUTTONS","buttons": [{"type": "QUICK_REPLY","text": request.POST['button-text']}]})
                                has_b = True
                            else:
                                has_b = False
                            payload = json.dumps(payload)
                            url = f"https://graph.facebook.com/v15.0/{data.business_id}/message_templates?access_token={data.token}"
                            header = {"Content-Type": "application/json", "Authorization": f"{data.token}"}

                            response = requests.post(url=url, data=payload, headers=header)

                            print(response.text)
                            try:
                                New_Templates.objects.create(user_id=request.COOKIES['id'], message_provider_id=data.id, temp_name=temp_n,
                                                            text_msg=regexpstring(temp_b, 0), text_converted=final, lang_code=language, category=category,
                                                            temp_id=json.loads(response.text)['id'], status="PENDING", has_button=has_b)         
                            except:
                                return JsonResponse({"Response":json.loads(response.text)})
                    return redirect("/createTemp")
                elif f_type == "tup":
                    
                    for i in range(0, len(rows)):
                        cols = [x for x in rows[i]]

                        temp_n = cols[header_chars.index(template_name)].replace(" ","_").lower()
                        # temp_h = cols[header_chars.index(header)]
                        temp_b = cols[header_chars.index(body)]
                        # temp_f = cols[header_chars.index(footer)]

                        for td in res_dt:
                            print("checking")
                            ind = next((index for (index, c) in enumerate(td['components']) if c["type"] == "BODY"), None)
                            if ind and (td['id'] not in table_temp_id_list):
                                c = td["components"][ind]
                                excel_text = regexpstring(temp_b, 0).replace("{#var#}", "(.*)")
                                p = re.compile(excel_text)
                                variables = p.findall(regexpstring(c['text'],1))
                                if variables:
                                    print("Matched")
                                    New_Templates.objects.create(user_id=request.COOKIES['id'], message_provider_id=data.id, temp_name=td['name'],
                                                    text_msg=regexpstring(temp_b, 0), text_converted=c['text'], lang_code=td['language'], category=td['category'],
                                                    temp_id=td['id'], status=td['status'])
                                    break
                        else:
                            myli = temp_b.split("{#var#}")
                            myli = [j for j in filter(lambda x: x != "", myli)]

                            vars = temp_b.count("{#var#}")

                            final = ""
                            n = 1
                            for i in myli:
                                if n > vars:
                                    final += i
                                    break
                                final += i + "{{"+str(n)+"}}"
                                n+=1
                            final += " Thank you"
                            payload = {
                                "name": temp_n,
                                "components":[
                                    {
                                        "type":"HEADER",
                                        "format":"TEXT",
                                        "text": data.temp_header
                                    },
                                    {
                                        "type":"BODY",
                                        "text":final
                                    },
                                    {
                                        "type":"FOOTER",
                                        "text":data.temp_footer
                                    }
                                ],
                                "language":language,
                                "category":category
                            }
                            if "isbutton" in request.POST:
                                payload["components"].append({"type": "BUTTONS","buttons": [{"type": "QUICK_REPLY","text": request.POST['button-text']}]})
                            payload = json.dumps(payload)
                            url = f"https://graph.facebook.com/v15.0/{data.business_id}/message_templates?access_token={data.token}"
                            header = {"Content-Type": "application/json", "Authorization": f"{data.token}"}

                            response = requests.post(url=url, data=payload, headers=header)
                            print(response.text)
                            try:
                                New_Templates.objects.create(user_id=request.COOKIES['id'], message_provider_id=data.id, temp_name=temp_n,
                                                            text_msg=regexpstring(temp_b, 0), text_converted=final, lang_code=language, category=category,
                                                            temp_id=json.loads(response.text)['id'], status="PENDING")
                            except:
                                return JsonResponse({"Response":json.loads(response.text)})
                    return redirect("/createTemp")
            elif request.POST["type"] == "single":
                print("Single")
                
                template_name = str(request.POST['temp-name']).replace(" ","_").lower()
                provider = request.POST["wa_provider"]
                data = WA_MSG_Provider.objects.get(phone_no=provider)
                database_temps = New_Templates.objects.filter(message_provider_id=data.id).values("temp_id")
                table_temp_id_list = [x['temp_id'] for x in database_temps]
                body = request.POST["temp-body"]
                language = request.POST["language"]
                category = request.POST['category']

                response = requests.get(
                    f"https://graph.facebook.com/v15.0/{data.business_id}/message_templates?access_token={data.token}")
                try:
                    response = json.loads(response.text)
                    res_dt = response['data']
                except KeyError:
                    print("Fetch Problem")
                    return JsonResponse({"response":response})

                for td in res_dt:
                    ind = next((index for (index, c) in enumerate(td['components']) if c["type"] == "BODY"), None)
                    if ind and (td['id'] not in table_temp_id_list):
                        c = td["components"][ind]
                        excel_text = regexpstring(body, 0).replace("{#var#}", "(.*)")
                        p = re.compile(excel_text)
                        variables = p.findall(regexpstring(c['text'], 1))
                        if variables:
                            print("Matched")
                            New_Templates.objects.create(user_id=request.COOKIES['id'], message_provider_id=data.id, temp_name=td['name'],
                                            text_msg=regexpstring(body, 0), text_converted=c['text'], lang_code=td['language'], category=td['category'],
                                            temp_id=td['id'], status=td['status'])
                            break
                else:
                    myli = body.split("{#var#}")
                    myli = [j for j in filter(lambda x: x != "", myli)]

                    vars = body.count("{#var#}")

                    final = ""
                    n = 1
                    for i in myli:
                        if n > vars:
                            final += i
                            break
                        final += i + "{{"+str(n)+"}}"
                        n+=1
                    final += " Thank you"

                    url = f"https://graph.facebook.com/v15.0/{data.business_id}/message_templates?access_token={data.token}"
                    header = {"Content-Type": "application/json", "Authorization": f"{data.token}"}

                    payload = {
                                "name": template_name,
                                "components":[
                                    {
                                        "type":"HEADER",
                                        "format":"TEXT",
                                        "text": data.temp_header
                                    },
                                    {
                                        "type":"BODY",
                                        "text":final
                                    },
                                    {
                                        "type":"FOOTER",
                                        "text":data.temp_footer
                                    }
                                ],
                                "language":language,
                                "category":category
                            }

                    if "isbutton" in request.POST:
                        payload["components"].append({"type": "BUTTONS","buttons": [{"type": "QUICK_REPLY","text": request.POST['button-text']}]})
                        has_b = True
                    else:
                        has_b = False
                    payload = json.dumps(payload)
                    response = requests.post(url=url, data=payload,headers=header)

                    print(response.text)
                    try:
                        New_Templates.objects.create(user_id=request.COOKIES['id'], message_provider_id=data.id, temp_name=template_name,
                                                    text_msg=regexpstring(body, 0), text_converted=final, lang_code=language, category=category,
                                                    temp_id=json.loads(response.text)['id'], status="PENDING", has_button=has_b)
                    except:
                        return JsonResponse({"response":json.loads(response.text)})
                return redirect("/createTemp")
        else:
            uid = request.COOKIES['id']
            data = WA_MSG_Provider.objects.filter(user_id=uid)
            templates = New_Templates.objects.filter(user_id=uid).order_by("id")
            
            sms_set = SMS_Settings.objects.filter(usr_id=uid)
            if sms_set:
                sms_set = sms_set[0]
            else:
                sms_set = ""
            return render(request, "create_temp.html", {"data":data, "templates": templates, "header":data[0].temp_header, "footer":data[0].temp_footer, "sms_set":sms_set})
    else:
        return JsonResponse({"Error":"Login required to access this page"})


def add_SMS_setting(request):
    if "id" in request.COOKIES and User1.objects.get(id=request.COOKIES['id']).is_authenticated():
        if request.method == "POST":
            mes_set = SMS_Settings.objects.filter(usr_id=request.COOKIES['id'])
            if not mes_set:
                SMS_Settings.objects.create(usr_id=request.COOKIES['id'])

            if "both" in request.POST:
                mes_set.update(both=True)
            else:
                mes_set.update(both=False)

            if "wa" in request.POST:
                mes_set.update(whatsapp=True)
            else:
                mes_set.update(whatsapp=False)

            if "mes" in request.POST:
                mes_set.update(sms=True)
            else:
                mes_set.update(sms=False)
            
            if "seletive" in request.POST:
                mes_set.update(selective=True)
                mes_set.update(keywords=request.POST["keywords"])
                if "sel_wa" in request.POST:
                    mes_set.update(sel_whatsapp=True)
                else:
                    mes_set.update(sel_whatsapp=False)

                if "sel_mes" in request.POST:
                    mes_set.update(sel_sms=True)
                else:
                    mes_set.update(sel_sms=False)
            else:
                mes_set.update(selective=False)
            
            mes_set.update(sms_url=request.POST["sms-url"])
            return redirect("/createTemp")
    else:
        return JsonResponse({"Error":"Login required to access this page"})


def regexpstring(text, isGram):
    from cleantext import clean
    
    if not isGram:
        text =  text + " Thank you"
    text = clean(text, no_emoji=True, lower=False)
    try:
        text = text.replace("\r\n"," ").replace("\n"," ").replace("\t"," ").replace("*", "").replace("?", "") 
        newString = ""
        previousIsWhitespace = False
        for t in text:
            if t.isspace():
                if previousIsWhitespace:
                    continue
                previousIsWhitespace = True
            else:
                previousIsWhitespace = False
            
            newString += t
        return newString
    except:
        text = text.replace("\r\n"," ").replace("\n"," ").replace("\t"," ").replace("*", "").replace("?", "")
        return text

@csrf_exempt
def getMatchTemp(request):
    if "id" in request.COOKIES and User1.objects.get(id=request.COOKIES['id']).is_authenticated():
        if request.method == "POST":
            data = json.loads(request.body)
            # print(data)
            phone = data["prod"]
            text = regexpstring(data["text"], 0)

            to_check_data = New_Templates.objects.filter(message_provider_id=WA_MSG_Provider.objects.get(phone_no=phone))
            temps = []
            for t in to_check_data:
                
                data = regexpstring(t.text_msg, 1).replace("{#var#}", "(.*)")
                # print(data)
                
                p = re.compile(data)
                
                variables = p.findall(text)
                
                if variables:
                    print(text)
                    print(data)
                    temps.append(f"{t.temp_name} [{t.lang_code}]")
                    print("Matched......................................") 
            return JsonResponse({"data":temps})
    else:
        return JsonResponse({"Error":"Login required to access this page"})

def ChangeHeaderorFooter(request):
    if "id" in request.COOKIES and User1.objects.get(id=request.COOKIES['id']).is_authenticated():
        if request.method == "POST":
            phone = request.POST["wa_provider"]
            WA_MSG_Provider.objects.filter(phone_no=phone).update(temp_header=request.POST["header"], temp_footer=request.POST["footer"])
            return redirect("/createTemp")
        else:
            print(request.GET["phone"])
            h = WA_MSG_Provider.objects.get(phone_no=request.GET["phone"])
            return JsonResponse({"head": h.temp_header,"foot":h.temp_footer})
    else:
        return JsonResponse({"Error":"Login required to access this page"})

def fetch_New(request):
    print(request.GET.get('pname'))
    if request.GET.get('pname') == "":
        return JsonResponse({"alert": "Please select api provider first"})
    else:
        prods = WA_MSG_Provider.objects.filter(phone_no=request.GET.get('pname'))
    data = []
    if prods:
        p = prods[0]
        data = []
        response = requests.get(
            f"https://graph.facebook.com/v15.0/{p.business_id}/message_templates?access_token={p.token}")
        try:
            response = json.loads(response.text)
            data = response['data']
        except KeyError:
            return JsonResponse({"alert": response})
        api_temp_ids = set()
        temp_ids_query = New_Templates.objects.filter(message_provider_id=p.id).values('temp_id')
        tab_temp_id = set()

        for tab_temp in temp_ids_query:
            tab_temp_id.add(tab_temp['temp_id'])

        for i in data:
            api_temp_ids.add(i["id"])
            if New_Templates.objects.filter(temp_id=i['id']):
                New_Templates.objects.filter(temp_id=i['id']).update(status=i['status'])

        
        to_delete = tab_temp_id - api_temp_ids
        print(to_delete)
        for t_d in to_delete:
            New_Templates.objects.get(temp_id=t_d).delete()
        return JsonResponse({"alert": ""})

def new_dash(request):
    return render(request, "new_dashboard.html")

def what_token(request):
    if "id" in request.COOKIES and User1.objects.get(id=request.COOKIES['id']).is_authenticated():
        if request.method == "POST":
            validity = request.POST["validity"]
            perm = request.POST["permission"]
            if perm == "user":
                ctime = datetime.datetime.now(tz=timezone.utc)+datetime.timedelta(hours=5.5)
                Whatsapp_Token.objects.create(user_id=request.COOKIES['id'], token=get_random_string(36),
                created_at=ctime, valid_till=int(validity), user_vice=1)
            
            elif perm == "provider":
                pid = WA_MSG_Provider.objects.get(phone_no=request.POST["provider"]).id
                ctime = datetime.datetime.now(tz=timezone.utc)+datetime.timedelta(hours=5.5)
                Whatsapp_Token.objects.create(user_id=request.COOKIES['id'], token=get_random_string(36),
                created_at=ctime, valid_till=int(validity), provider_vice=1, prod_id=pid)
            
            elif perm == "pro-cus":
                pid = WA_MSG_Provider.objects.get(phone_no=request.POST["prod-pair"]).id
                
                ctime = datetime.datetime.now(tz=timezone.utc)+datetime.timedelta(hours=5.5)
                Whatsapp_Token.objects.create(user_id=request.COOKIES['id'], token=get_random_string(36),
                created_at=ctime, valid_till=int(validity), provider_cus_pair=1, 
                prod_id=pid, customer_num=request.POST["cus-pair"])

            elif perm == "campaign":
                ctime = datetime.datetime.now(tz=timezone.utc)+datetime.timedelta(hours=5.5)
                if request.POST["norm-camp"] != "":
                    Whatsapp_Token.objects.create(user_id=request.COOKIES['id'], token=get_random_string(36),
                    created_at=ctime, valid_till=int(validity), campaign_vice=1, campaign_id=request.POST["norm-camp"])
                    
                elif request.POST["adv-camp"] != "":
                    Whatsapp_Token.objects.create(user_id=request.COOKIES['id'], token=get_random_string(36),
                    created_at=ctime, valid_till=int(validity), campaign_vice=1, adv_campaign_id=request.POST['adv-camp'])
            return redirect("/what_token")
        else:
            prod_data = WA_MSG_Provider.objects.filter(user_id=request.COOKIES['id'])
            campaigns = Campaign.objects.filter(user_key_id=request.COOKIES['id'])
            adv_campaigns = AdvanceCampaign.objects.filter(user_key_id=request.COOKIES['id'])
            data = Whatsapp_Token.objects.filter(user_id=request.COOKIES['id'])
            main_data = {}
            for i, m in enumerate(data):
                if m.user_vice:
                    detail = f"User - {User1.objects.get(pk=m.user_id).user_name}"
                elif m.provider_vice:
                    detail = f"Provider - {WA_MSG_Provider.objects.get(pk=m.prod_id).provider_name}"
                elif m.provider_cus_pair:
                    detail = f"{WA_MSG_Provider.objects.get(pk=m.prod_id).provider_name} - {m.customer_num}"
                elif m.campaign_vice and m.campaign_id:
                    detail = f"{Campaign.objects.get(pk=m.campaign_id).CampaignName} - Campaign"
                elif m.campaign_vice and m.adv_campaign_id:
                    detail = f"{AdvanceCampaign.objects.get(pk=m.adv_campaign_id).CampaignName} - Campaign"
                main_data[i] = {"token":m.token, "detail":detail, "created_at":m.created_at, "validity":m.valid_till}
            return render(request, "whatsappToken.html", {"main_data":main_data,"prod_data":prod_data, "camp":campaigns, "Advcamp":adv_campaigns})
    else:
        return JsonResponse({"Error":"Login required to access this page"})

def customer_list(request):
    phone = request.GET['phone']
    data = Message_History.objects.filter(api_number=phone)
    final = {}
    for i, d in enumerate(data):
        final[i] = d.customer_number
    return JsonResponse({"data":final})


def download_sample(request):
    table_name = request.GET['table']
    response = HttpResponse(content_type='application/ms-excel')
    # decide file name
    response['Content-Disposition'] = f'attachment; filename="{table_name}.xls"'

    # creating workbook
    wb = xlwt.Workbook(encoding='utf-8')

    # adding sheet
    ws = wb.add_sheet("sheet1")

    # Sheet header, first row
    row_num = 0

    font_style = xlwt.XFStyle()
    # headers are bold
    font_style.font.bold = True

    # get your data, from database or from a text file...
    if table_name == "AddReminderUser":
        # column header names, you can use your own headers here
        columns = ['User Name', 'User Mobile', 'Birthdate', 'Anniversary Date', 'Remark']
        # write column headers in sheet
        for col_num in range(len(columns)):
            ws.write(row_num, col_num, columns[col_num], font_style)
    wb.save(response)
    return response


def reminders(request):
    if "id" in request.COOKIES and User1.objects.get(id=request.COOKIES['id']).is_authenticated():
        if request.method == "POST":
            if request.POST["type"] == "single": 
                if "ru_id" in request.POST and request.POST["ru_id"] != "":
                    uname = request.POST["update-user"]
                    mobile = request.POST["update-mobile"]
                    remark = request.POST['update-remark']
                    adate = datetime.datetime.strptime(request.POST["update-a-date"], "%Y-%m-%d").date()
                    bdate = datetime.datetime.strptime(request.POST["update-b-date"], "%Y-%m-%d").date()
                    
                    wap = WA_MSG_Provider.objects.get(pk=request.POST['u_provider']).id
                    try:
                        sid = Reminder_Setting.objects.get(wap_id=wap).id
                    except:
                        return JsonResponse({"message":"Please configure reminder settings"})
                    Reminder_User.objects.filter(pk=request.POST["ru_id"]).update(user_name=uname, birthdate=bdate, anniversary=adate, remark=remark)
                else:
                    uname = request.POST["remind-user"]
                    mobile = request.POST["remind-mobile"]
                    remark = request.POST["remind-remark"]
                    adate = datetime.datetime.strptime(request.POST["remind-a-date"], "%Y-%m-%d").date()
                    bdate = datetime.datetime.strptime(request.POST["remind-b-date"], "%Y-%m-%d").date()
                    
                    wap = WA_MSG_Provider.objects.get(pk=request.POST['u_provider']).id
                    try:
                        sid = Reminder_Setting.objects.get(wap_id=wap).id
                    except:
                        return JsonResponse({"message":"Please configure reminder settings"})
                    Reminder_User.objects.create(user_name=uname, birthdate=bdate, anniversary=adate, user_mobile=mobile, setting_id=sid, remark=remark)
            else:
                file = request.FILES.get('myfile')
                rows, ftype, headers_char = prepare(file, request.COOKIES['id'])
                if ftype == "":
                    for cols in range(1, len(rows) - 1):
                        i = rows[cols].split(",")
                        bdate = datetime.datetime.strptime(i[2], '%d-%m-%Y')
                        adate = datetime.datetime.strptime(i[3], '%d-%m-%Y')
                        is_exist = Reminder_User.objects.filter(user_mobile=i[1])
                        if is_exist:
                            is_exist.update(user_name=i[0], birthdate=bdate, anniversary=adate, remark=i[4])
                        else:
                            wap = WA_MSG_Provider.objects.get(phone_no=request.POST['mul-provider']).id
                            try:
                                sid = Reminder_Setting.objects.get(wap_id=wap).id
                            except:
                                return JsonResponse({"message":"Please configure reminder settings"})
                            Reminder_User.objects.create(user_name=i[0], birthdate=bdate, anniversary=adate, user_mobile=i[1], setting_id=sid, remark=i[4])

                elif ftype == "tup":
                    for i in rows:
                        print(i, type(i))
                        is_exist = Reminder_User.objects.filter(user_mobile=i[1])
                        if is_exist:
                            is_exist.update(user_name=i[0], birthdate=i[2], anniversary=i[3], remark=i[4])
                        else:
                            wap = WA_MSG_Provider.objects.get(phone_no=request.POST['mul-provider']).id
                            try:
                                sid = Reminder_Setting.objects.get(wap_id=wap).id
                            except:
                                return JsonResponse({"message":"Please configure reminder settings"})
                            Reminder_User.objects.create(user_name=i[0], birthdate=i[2], anniversary=i[3], user_mobile=i[1], setting_id=sid, remark=i[4])
            return redirect("/reminders")
        else:
            iml2 = "https://www.kindpng.com/picc/m/294-2944583_birthday-party-clipart-celebration-happy-birthday-whatsapp-sticker.png"
            iml = "https://img.freepik.com/free-vector/detailed-birthday-lettering_52683-58875.jpg?w=150"
            providers = WA_MSG_Provider.objects.filter(user_id=request.COOKIES['id'])
            try:
                data = Reminder_User.objects.filter(setting_id=Reminder_Setting.objects.get(wap_id=providers[0].id))
            except:
                data = []
            return render(request, "reminders.html", {"data":data,"im_link":iml,"im_link2":iml2, "providers":providers})
    else:
        return JsonResponse({"Error":"Login required to access this page"})

def get_remindU(request):
    ruid = request.GET["rid"]
    data = Reminder_User.objects.get(pk=ruid)
    pid = Reminder_Setting.objects.get(pk=data.setting_id).wap_id
    ret_data = {"uname":data.user_name, "mob":data.user_mobile, "bdate":data.birthdate, "adate":data.anniversary, 'pid':pid}
    return JsonResponse({"data":ret_data})

def createReminderTemp(request):
    if "id" in request.COOKIES and User1.objects.get(id=request.COOKIES['id']).is_authenticated():
        if request.method == "POST":
            provider = request.POST["provider"]
            if provider:
                template_name = str(request.POST['temp-name']).replace(" ","_").lower()
                data = WA_MSG_Provider.objects.get(phone_no=provider)
                theader = request.POST["header"]
                body = request.POST["temp-body"]
                language = request.POST["language"]
                category = request.POST['category']
                print(category)
                body = body.replace("{client_name}", "{{1}}")                

                url = f"https://graph.facebook.com/v15.0/{data.business_id}/message_templates?access_token={data.token}"
                header = {"Content-Type": "application/json", "Authorization": f"{data.token}"}

                payload = {
                            "name": template_name,
                            "components":[
                                {
                                    "type":"HEADER",
                                    "format":"IMAGE",
                                    "example": {
                                            "header_handle": [theader]
                                        }
                                },
                                {
                                    "type":"BODY",
                                    "text":body,
                                    "example": {
                                        "body_text":[["Mr. Bonrix"]]
                                    }
                                }
                            ],
                            "language":language,
                            "category":str(category).upper()
                        }
                print(payload)
                if "isbutton" in request.POST:
                    payload["components"].append({"type": "BUTTONS","buttons": [{"type": "QUICK_REPLY","text": request.POST['button-text']}]})
                payload = json.dumps(payload)
                response = requests.post(url=url, data=payload,headers=header)

                print(response.text)
                try:
                    id = json.loads(response.text)["id"]
                    return redirect("/reminders")
                except KeyError:
                    return JsonResponse(json.loads(response.text))

            else:
                return JsonResponse({"response":"Select provider first"})
    else:
        return JsonResponse({"Error":"Login required to access this page"})

def reminderSettings(request):
    if "id" in request.COOKIES and User1.objects.get(id=request.COOKIES['id']).is_authenticated():
        provider_number = request.POST['provider']
        b_template = request.POST['b_template']
        a_template = request.POST['a_template']
        schedule_time = request.POST['s_time']
        schedule_time = datetime.datetime.strptime(schedule_time, "%H:%M")
        
        pid = WA_MSG_Provider.objects.get(phone_no=provider_number).id

        bd_temp = Templates.objects.get(temp_name=b_template.split('-')[0], lang_code=b_template.split('-')[1], 
                                        message_provider_id=pid).temp_id
        an_temp = Templates.objects.get(temp_name=a_template.split('-')[0], lang_code=a_template.split('-')[1], 
                                        message_provider_id=pid).temp_id
        print(b_template, bd_temp)
        print(a_template, an_temp)
        is_set = Reminder_Setting.objects.filter(wap_id=pid)
        if is_set:
            is_set.update(birthday_temp=bd_temp, anyversary_temp=an_temp, scheduled_time=schedule_time)
        else:
            Reminder_Setting.objects.create(user_id=request.COOKIES['id'], wap_id=pid,
                birthday_temp=bd_temp, anyversary_temp=an_temp, scheduled_time=schedule_time)
        return redirect("/reminders")
    else:
        return JsonResponse({"Error":"Login required to access this page"})

def hit_reminder(requets, key):
    if key == settings.PRIVATE_TOKEN:
        print("Hit Reminder")
        today = datetime.date.today()
        bday = Reminder_User.objects.filter(birthdate=today)
        aday = Reminder_User.objects.filter(anniversary=today)
        for b in bday:
            sets = Reminder_Setting.objects.get(pk=b.setting_id)
            b_temp = Templates.objects.get(temp_id=sets.birthday_temp)
            at = datetime.datetime.now().time()
            check_at = sets.scheduled_time
            if f"{check_at.hour}:{check_at.minute}" == f"{at.hour}:{at.minute}" and (b.b_sent != datetime.date.today()):
                p = WA_MSG_Provider.objects.get(pk=sets.wap_id)
                api_setting = Voice_API.objects.get(whatsapp_name=p.provider_name)
                if b_temp.is_media:
                    if b_temp.med_id is None:
                        return JsonResponse({"message": "Please Upload media content first."})
                    else:
                        js = json.loads(b_temp.med_id)
                        payload = json.dumps({
                            "messaging_product": "whatsapp",
                            "recipient_type": "individual",
                            "to": f"{b.user_mobile}",
                            "type": "template",
                            "template": {
                                "name": f"{b_temp.temp_name}",
                                "language": {
                                    "code": f"{b_temp.lang_codeg}"
                                },
                                "components": [
                                    {
                                        "type": "header",
                                        "parameters": [
                                            {
                                                "type": "image",
                                                "image": {"link": f"{js['link']}"} if js["type"] == "what" else {
                                                    "id": f"{js['med_obj']}"}
                                            }
                                        ]
                                    }
                                ]
                            }
                        })
                else:
                    payload = json.dumps({
                        "messaging_product": "whatsapp",
                        "recipient_type": "individual",
                        "to": f"{a.user_mobile}",
                        "type": "template",
                        "template": {
                            "name": f"{b_temp.temp_name}",
                            "language": {
                                "code": f"{b_temp.lang_code}"
                            },

                        }
                    })
                
                response = requests.post(url=api_setting.message_API, data=payload,headers=api_setting.header)
                print(response.text)
                try:
                    id = json.loads(response.text)["messages"][0]["id"]
                    print("here")
                    b.b_sent = datetime.date.today()
                    b.b_msg_id = id
                    b.save() 
                except KeyError:
                    print("here")
                    continue
        
        for a in aday:
            sets = Reminder_Setting.objects.get(pk=a.setting_id)
            a_temp = Templates.objects.get(temp_id=sets.anyversary_temp)
            at = datetime.datetime.now().time()
            check_at = sets.scheduled_time
            
            if f"{check_at.hour}:{check_at.minute}" == f"{at.hour}:{at.minute}" and (a.a_sent != datetime.date.today()):
                p = WA_MSG_Provider.objects.get(pk=sets.wap_id)
                api_setting = Voice_API.objects.get(whatsapp_name=p.provider_name)
                if a_temp.is_media:
                    if a_temp.med_id is None:
                        return JsonResponse({"message": "Please Upload media content first."})
                    else:
                        js = json.loads(a_temp.med_id)
                        payload = json.dumps({
                            "messaging_product": "whatsapp",
                            "recipient_type": "individual",
                            "to": f"{a.user_mobile}",
                            "type": "template",
                            "template": {
                                "name": f"{a_temp.temp_name}",
                                "language": {
                                    "code": f"{a_temp.lang_codeg}"
                                },
                                "components": [
                                    {
                                        "type": "header",
                                        "parameters": [
                                            {
                                                "type": "image",
                                                "image": {"link": f"{js['link']}"} if js["type"] == "what" else {
                                                    "id": f"{js['med_obj']}"}
                                            }
                                        ]
                                    }
                                ]
                            }
                        })
                else:
                    payload = json.dumps({
                        "messaging_product": "whatsapp",
                        "recipient_type": "individual",
                        "to": f"{a.user_mobile}",
                        "type": "template",
                        "template": {
                            "name": f"{a_temp.temp_name}",
                            "language": {
                                "code": f"{a_temp.lang_code}"
                            },

                        }
                    })

                response = requests.post(url=api_setting.message_API, data=payload,headers=api_setting.header)
                print(response.text)
                try:
                    id = json.loads(response.text)["messages"][0]["id"]
                    a.a_sent = datetime.date.today()
                    a.a_msg_id = id
                    a.save() 
                except KeyError:
                    continue
        return JsonResponse({"Status":True})
    else:
        return JsonResponse({"Status":False})


def PdfTemplate(request):
    return render(request, "pdfTemplate.html")

