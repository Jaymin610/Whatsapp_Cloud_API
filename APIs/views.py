from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
import pytz
from user.models import *
import datetime as dt

# Create your views here.
def index(request):
    token = request.GET["token"]
    try:
        sets = Whatsapp_Token.objects.get(token=token)
    except Exception as e:
        return JsonResponse({"message":"Invalid token"})
    is_valid = True if sets.created_at + dt.timedelta(hours=sets.valid_till) > dt.datetime.now(pytz.timezone('Asia/Kolkata')) else False
    if is_valid:
        if sets.user_vice:
            data = list(Message_History.objects.filter(user_id=sets.user_id).values())
            return JsonResponse({"message":"success", "data":data}, safe=False)
        elif sets.provider_vice:
            data = list(Message_History.objects.filter(provider_id=sets.prod_id).values())
            return JsonResponse({"message":"success", "data":data}, safe=False)
        elif sets.provider_cus_pair:
            data = list(Message_History.objects.filter(provider_id=sets.prod_id, customer_number=sets.customer_num).values())
            return JsonResponse({"message":"success", "data":data}, safe=False)
        elif sets.campaign_vice:
            if sets.campaign_id:
                to_filter = Data_Summary.objects.filter(recordID_id=sets.campaign_id)
                client_num = list(to_filter.values("mobile"))
                cl_lis = []
                for c in client_num:
                    cl_lis.append(c['mobile'])
                api_num = to_filter.values("sender_name")
                ph_lis = []
                for a in api_num:
                    apn = WA_MSG_Provider.objects.get(provider_name=a['sender_name']).phone_no
                    ph_lis.append(apn)
            else:
                to_filter = AdvanceCampaign.objects.filter(pk=sets.adv_campaign_id)
                client_num = list(to_filter.values("mobile"))
                cl_lis = []
                for c in client_num:
                    cl_lis.append(c['mobile'])
                api_num = to_filter.values("sender_name")
                ph_lis = []
                for a in api_num:
                    apn = WA_MSG_Provider.objects.get(provider_name=a['sender_name']).phone_no
                    ph_lis.append(apn)
            data = list(Message_History.objects.filter(customer_number__in=cl_lis, api_number__in=ph_lis).values())
            return JsonResponse({"message":"success", "data":data})
    else:
        return JsonResponse({"message":"Token has been expired"})
