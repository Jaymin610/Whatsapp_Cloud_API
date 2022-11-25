import datetime
import json
import os
import re

from PIL import Image
from django.contrib import messages
import requests
from django.core.files.storage import FileSystemStorage
from django.http import JsonResponse
from django.shortcuts import render, redirect
from user.models import *
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout


# Create your views here.
def loginUser(request):
    if request.method == "POST":
        user = authenticate(username=request.POST['username'], password=request.POST['pass'], is_superuser=True)
        if user:
            login(request, user)
            response = redirect('/admin/dashboard')
            return response
        else:
            messages.error(request, 'User Does not exist.')
    return render(request, "Ad_login.html")


def index(request):
    if request.user.is_authenticated:
        data = User1.objects.all()
        return render(request, "Ad_dashboard.html", {"Data": data})
    else:
        return redirect("/admin")


def logoutUser(request):
    logout(request)
    return redirect("/admin")


def copyTemp(request):
    if request.user.is_authenticated:
        prods = WA_MSG_Provider.objects.all()
        return render(request, "copyTemp.html", {"prod": prods})
    else:
        redirect("/admin")


def fetch_Temp(request):
    phone = request.GET.get('phone')
    result = WA_MSG_Provider.objects.get(phone_no=phone)
    temps = Templates.objects.filter(message_provider_id=result.id)
    yl = {}
    j = 0

    for i in temps:
        yl[j] = [i.temp_name, i.lang_code, i.temp_id]
        j += 1
    return JsonResponse({"data": yl})


def get_tempJson(request):
    temp_id = request.GET.get("id")
    temps = Templates.objects.get(temp_id=temp_id)
    print(temp_id)
    # 665432788290530
    prods = WA_MSG_Provider.objects.get(id=temps.message_provider_id)
    url = f"https://graph.facebook.com/v15.0/{prods.business_id}/message_templates?limit=1&access_token={prods.token}&name_or_content" \
          f"={temps.temp_name}&language={temps.lang_code}"
    print(temps.temp_name)
    response = requests.get(url)
    json_data = json.loads(response.text)
    
    temp_compo = json_data['data'][0]['components']
    temp_preview = {}
    for i in range(len(temp_compo)):
        if temp_compo[i]['type'].lower() == "header" and temp_compo[i]['format'].lower() == "text":
            temp_preview[temp_compo[i]["type"]] = temp_compo[i]["text"]
        elif temp_compo[i]['type'].lower() == "header" and temp_compo[i]['format'].lower() in ["image", "document"]:
            # temp_preview[temp_compo[i]["type"]] = temp_compo[i]["example"]["header_handle"][0]
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
    # print(temp_preview)
    body_var = ""
    header_var = ""
    if "HEADER" in temp_preview:
        header_var = re.findall("{{[0-9]}}", temp_preview["HEADER"])
        header_var = [*set(header_var)]
        header_var.sort()

    if "BODY" in temp_preview:
        body_var = re.findall("{{[0-9]}}", temp_preview["BODY"])
        body_var = [*set(body_var)]
        body_var.sort()

    try:
        del json_data["paging"]
    except:
        pass
    temp_status = ""
    try:
        inter = json_data["data"][0]
        temp_status = inter["status"]
        del inter["status"]
        del inter["id"]
        json_data["data"] = inter
    except:
        pass
    temp_look = {}
    for i in temp_preview:
        temp_look[i] = temp_preview[i]

    print(body_var, header_var)
    return JsonResponse(
        {"data": json_data, "countb": body_var, "counth": header_var, "temp_look": temp_look, "status": temp_status, "date_time":f"{datetime.datetime.now():%b. %d, %Y, %H:%M %p}"})


def get_CheckJSOn(request):
    temp_id = request.GET.get("id")
    temps = Templates.objects.get(temp_id=temp_id)
    print(temps.temp_name, temps.lang_code)
    prods = WA_MSG_Provider.objects.get(id=temps.message_provider_id)
    url = f"https://graph.facebook.com/v15.0/{prods.business_id}/message_templates?limit=1&access_token={prods.token}&name_or_content" \
          f"={temps.temp_name}&language={temps.lang_code}"
    response = requests.get(url)
    json_data = json.loads(response.text)

    temp_compo = json_data['data'][0]['components']
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
    # print(temp_preview)
    body_var = ""
    header_var = ""
    if "HEADER" in temp_preview:
        header_var = re.findall("{{[0-9]}}", temp_preview["HEADER"])
        header_var = [*set(header_var)]

    if "BODY" in temp_preview:
        body_var = re.findall("{{[0-9]}}", temp_preview["BODY"])
        body_var = [*set(body_var)]

    try:
        del json_data["paging"]
    except:
        pass
    try:
        inter = json_data["data"][0]
        del inter["status"]
        del inter["id"]
        json_data["data"] = inter
    except:
        pass
    temp_look = ""
    for i in temp_preview:
        temp_look += f'''
    {temp_preview[i]}\n
    
    '''
    print(body_var, header_var)
    return JsonResponse({"data": json_data, "countb": body_var, "counth": header_var, "temp_look": temp_look})


def create_Temp(request):
    payload = request.POST["temp-json"]
    prod = request.POST["to-provider"]
    data = WA_MSG_Provider.objects.get(phone_no=prod)
    payload = json.dumps(json.loads(payload)['data'])
    print(data.business_id)
    url = f"https://graph.facebook.com/v15.0/{data.business_id}/message_templates?access_token={data.token}"
    header = {"Content-Type": "application/json", "Authorization": f"{data.token}"}

    response = requests.post(url=url, data=payload, headers=header)
    print(response.text)
    return JsonResponse({"res": response.text})


def show_settings(request):
    if request.user.is_authenticated:
        uid = request.GET['uid']
        results = WA_MSG_Provider.objects.filter(user_id=uid)
        data = {'data': results}
        return render(request, 'settings.html', data)
    else:
        return redirect("admin")


def manageTemp(request):
    if request.user.is_authenticated:
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

                object_path = "C:/Whatsapp_Cloud_API_Server/user/media_objects/" + user_name + "/" + provider_name
                if not os.path.exists(object_path):
                    os.mkdir("C:/Whatsapp_Cloud_API_Server/user/media_objects/" + user_name)
                    os.mkdir("C:/Whatsapp_Cloud_API_Server/user/media_objects/" + user_name + "/" + provider_name)

                file = request.FILES['media_obj']
                open_f = file.name
                if file:
                    fss = FileSystemStorage()
                    file = fss.save(file.name, file)

                im = Image.open(r"C:/Whatsapp_Cloud_API_Server/user/media_objects/" + open_f)
                im.convert("RGB")
                file_name_save = template_id + "_" + str(datetime.datetime.now().timestamp()) + ".jpg"
                im.save(object_path + "/" + file_name_save)

                os.remove("C:/Whatsapp_Cloud_API_Server/user/media_objects/" + open_f)

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
                    Templates.objects.filter(temp_id=template_id).update(med_id=result['id'])
                elif platform.lower() == "bonrix":
                    arr = object_path.split("/")
                    obj_id = "http://wotsapp-campaign.bonrix.in:8000/media/" + arr[-2] + "/" + arr[
                        -1] + "/" + file_name_save
                    # {"type": "facebook", "link": obj_id}
                    Templates.objects.filter(temp_id=template_id).update(med_id=obj_id)
                print(platform, file)

        user_id = request.GET['uid']
        data = Templates.objects.filter(user_id=user_id)
        dl_temp = Templates.objects.filter(status="")
        for d in dl_temp:
            d.delete()
        prods = WA_MSG_Provider.objects.filter(user_id=user_id)
        return render(request, 'AdminManageTemp.html', {'data': data, 'prods': prods})


def settings(request):
    u_id = request.GET['uid']
    if request.user.is_authenticated:
        print(u_id)
        data = WA_MSG_Provider.objects.filter(user_id=u_id)
        response = render(request, "Admin_settings.html",
                          {"data": data, "base": "Ad_base", "home": "/admin/dashboard", "addS": "/admin/addSettings",
                           "delete": "/admin/delete_Settings", "edit": "/admin/editSettings"})
        response.set_cookie("id", u_id)
        return response


def addSettings(request):
    if request.user.is_authenticated:
        message = {"MSG": ""}
        if request.method == "POST":
            mobile = request.POST['phone_no'].replace(" ", "")
            mobile = mobile.replace("+", "")
            mobile = mobile.strip()
            if not WA_MSG_Provider.objects.filter(phone_id=request.POST['phone_id'],
                                                  provider_name=request.POST['p_name']):
                WA_MSG_Provider.objects.create(phone_id=request.POST['phone_id'], provider_name=request.POST['p_name'],
                                               phone_no=mobile, token=request.POST['token'],
                                               business_id=request.POST['b_id'], user_id=request.COOKIES['id'])
                Voice_API.objects.create(u_ID_id=request.COOKIES['id'],
                                         message_API=f"https://graph.facebook.com/v15.0/{request.POST['phone_id']}/messages",
                                         header={'Content-Type': 'application/json',
                                                 'Authorization': f'Bearer {request.POST["token"]}'},
                                         whatsapp_name=request.POST['p_name'])
                return redirect(f"/admin/settings?uid={request.COOKIES['id']}")
            else:
                messages.error("API setting already exist")
        return render(request, "Admin_AddSettings.html", {"action": "/admin/addSettings",
                                                    "set": "/admin/settings?uid=" + request.COOKIES['id']})


def editSettings(request):
    if request.user.is_authenticated:
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
            return redirect(f"/admin/settings?uid={request.COOKIES['id']}")
        else:
            sid = request.GET.get('sid')
            data = WA_MSG_Provider.objects.get(id=sid)
            return render(request, "Admin_editSettings.html", {'sid': sid, 'data': data, "action": "/admin/editSettings",
                                                         "set": "/admin/settings?uid=" + request.COOKIES['id']})


def delete_setting(request):
    if request.user.is_authenticated:
        sid = request.GET.get('sid')
        data = WA_MSG_Provider.objects.get(id=sid)
        if Voice_API.objects.filter(u_ID_id=data.user_id, whatsapp_name=data.provider_name):
            Voice_API.objects.get(u_ID_id=data.user_id, whatsapp_name=data.provider_name).delete()
        data.delete()
        return redirect("/admin/settings")



