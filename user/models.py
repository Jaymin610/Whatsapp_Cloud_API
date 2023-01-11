from django.db import models


# Create your models here.

class Staff(models.Model):
    s_name = models.CharField(max_length=32, blank=True, null=True)
    mobile = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    password = models.CharField(max_length=25, blank=True, null=True)
    is_active = models.BooleanField(default=True)

class User1(models.Model):

    def __str__(self):
        return self.user_name
    class Meta:
        verbose_name_plural = 'Users'
    
    @staticmethod
    def authenticate(email, passw):
        return User1.objects.filter(email=email, password=passw)

    def login(self):
        if self.is_active:
            self.is_auth = True
            self.save()
        else:
            self.is_auth = False
            self.save()

    def logout(self):
        self.is_auth = False
        self.save()

    def is_authenticated(self):
        print(self.is_auth)
        return self.is_auth

    user_name = models.CharField(max_length=32, blank=True, null=True)
    staff = models.ForeignKey(Staff, on_delete=models.DO_NOTHING, null=True)
    staff_name = models.CharField(max_length=32, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    password = models.CharField(max_length=25, blank=True, null=True)
    phone_no = models.CharField(max_length=15, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=False)
    updated_at = models.DateTimeField(auto_now=True, blank=False)
    validity = models.DateField(null=True, db_index=True)
    is_auth = models.BooleanField(default=False)
    is_mark_for_delete = models.BooleanField(default=False)
    remark = models.CharField(max_length=1000, blank=True, null=True)


class Voice_API(models.Model):
    u_ID = models.ForeignKey(User1, on_delete=models.CASCADE, null=True)
    message_API = models.CharField(max_length=255, default="")
    header = models.JSONField(max_length=255, null=True, blank=True)
    whatsapp_name = models.CharField(max_length=255, null=True, blank=True)


class Campaign(models.Model):
    user_key = models.ForeignKey(User1, on_delete=models.CASCADE, null=True)
    CampaignName = models.CharField(max_length=255, null=True, blank=True)
    Description = models.CharField(max_length=255, null=True, blank=True)
    record_count = models.IntegerField(null=True, blank=True)
    CampaignStatus = models.CharField(max_length=255, null=True, blank=True)


class AdvanceCampaign(models.Model):
    user_key = models.ForeignKey(User1, on_delete=models.CASCADE, null=True)
    CampaignName = models.CharField(max_length=255, null=True, blank=True)
    Description = models.CharField(max_length=255, null=True, blank=True)
    record_count = models.IntegerField(null=True, blank=True)
    CampaignStatus = models.CharField(max_length=255, null=True, blank=True)


class Data_Summary(models.Model):
    recordID = models.ForeignKey(Campaign, on_delete=models.CASCADE, null=True)
    mobile = models.CharField(max_length=15, null=False, blank=True)
    sender_name = models.CharField(max_length=255, null=True, blank=True)
    template = models.CharField(max_length=255, null=True, blank=True)
    lang = models.CharField(max_length=20, null=True, blank=True)
    text = models.CharField(max_length=1000, null=True, blank=True)
    msg_id = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    voiceshoot_req = models.CharField(max_length=255, null=True, blank=True)
    voiceshoot_res = models.JSONField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=10, default="Pending")
    what_status = models.CharField(max_length=10, null=True)


class Advance_Data(models.Model):
    recordID = models.ForeignKey(AdvanceCampaign, on_delete=models.CASCADE, null=True)
    mobile = models.CharField(max_length=15, null=False, blank=True)
    sender_name = models.CharField(max_length=255, null=True, blank=True)
    template = models.CharField(max_length=255, null=True, blank=True)
    lang = models.CharField(max_length=20, null=True, blank=True)
    variables = models.JSONField(max_length=1000, null=True, blank=True)
    text = models.CharField(max_length=1000, null=True, blank=True)
    msg_id = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    voiceshoot_req = models.CharField(max_length=255, null=True, blank=True)
    voiceshoot_res = models.JSONField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=10, default="Pending")
    what_status = models.CharField(max_length=10, null=True)


class WA_MSG_Provider(models.Model):
    class Meta:
        verbose_name_plural = 'WA_MSG_Provider'
    phone_id = models.CharField(max_length=50, default="")
    provider_name = models.CharField(max_length=100, null=True, blank=True)
    phone_no = models.CharField(max_length=15, null=True, blank=True)
    token = models.CharField(max_length=255, default="")
    business_id = models.CharField(max_length=255, null=True, blank=True)
    user = models.ForeignKey(User1, on_delete=models.CASCADE, null=True)
    temp_header = models.CharField(max_length=100, blank=True)
    temp_footer = models.CharField(max_length=100, blank=True)


class Message_History(models.Model):
    user = models.ForeignKey(User1, on_delete=models.CASCADE, null=True)
    provider = models.ForeignKey(WA_MSG_Provider, on_delete=models.CASCADE, null=True)
    message = models.TextField(blank=True, null=True)
    time = models.DateTimeField(auto_now_add=True, blank=True)
    msg_type = models.TextField(null=True)
    media_url = models.CharField(max_length=1000, null=True, blank=True)
    customer_number = models.CharField(max_length=15, null=True)
    api_number = models.CharField(max_length=15, null=True)
    msg_id = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    status = models.CharField(max_length=10, null=True)
    sent_time = models.DateTimeField(null=True)
    delivered_time = models.DateTimeField(null=True)
    read_time = models.DateTimeField(null=True)


class MessageLog(models.Model):
    user = models.ForeignKey(User1, on_delete=models.CASCADE, null=True)
    sender_number = models.CharField(max_length=15)
    received_msg = models.CharField(max_length=1000, null=True, blank=True, db_index=True)
    received_time = models.DateTimeField()
    is_read = models.BooleanField(default=0)
    reply = models.CharField(max_length=1000, null=True, blank=True)
    send_time = models.DateTimeField(null=True)
    reply_number = models.CharField(max_length=15, db_index=True)
    status = models.CharField(max_length=10, null=True)
    json = models.JSONField(max_length=1000, null=True)
    request = models.CharField(max_length=255, null=True)
    response = models.CharField(max_length=1000, null=True)
    msg_id = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    media_content = models.CharField(max_length=500, blank=True, null=True)


class SubMessageLog(models.Model):
    user = models.ForeignKey(User1, on_delete=models.CASCADE, null=True)
    parent_msg = models.ForeignKey(MessageLog, on_delete=models.CASCADE, null=True)
    reply = models.CharField(max_length=1000, null=True, blank=True)
    send_time = models.DateTimeField(null=True)
    reply_number = models.CharField(max_length=15)
    status = models.CharField(max_length=10, null=True)
    json = models.JSONField(max_length=1000, null=True)
    request = models.CharField(max_length=255, null=True)
    response = models.CharField(max_length=1000, null=True)
    msg_id = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    media_content = models.CharField(max_length=500, blank=True, null=True)


class CallBack_Data(models.Model):
    user = models.ForeignKey(User1, on_delete=models.CASCADE, null=True)
    Received = models.TextField(null=True)
    received_time = models.DateTimeField(null=True)
    msg_id = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    msg_status = models.CharField(max_length=50, blank=True, null=True)


class OutBox(models.Model):
    user = models.ForeignKey(User1, on_delete=models.CASCADE, null=True)
    to_number = models.CharField(max_length=15, null=True)
    message = models.CharField(max_length=1000, null=True, blank=True)
    variables = models.CharField(max_length=500, null=True)
    send_time = models.DateTimeField(null=True, db_index=True)
    reply_number = models.CharField(max_length=100)
    msg_id = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    status = models.CharField(max_length=10, null=True)
    request = models.CharField(max_length=255, null=True)
    response = models.TextField(null=True)
    media_url = models.CharField(max_length=1000, null=True, blank=True)


class SMS_OutBox(models.Model):
    user = models.ForeignKey(User1, on_delete=models.CASCADE, null=True)
    to_number = models.CharField(max_length=15, null=True)
    message = models.CharField(max_length=1000, null=True, blank=True)
    send_time = models.DateTimeField(null=True)
    status = models.CharField(max_length=10, null=True)
    request = models.CharField(max_length=255, null=True)
    response = models.TextField(null=True)


class Developers_token(models.Model):
    class Meta:
        verbose_name_plural = 'Developer_Token'
    user = models.ForeignKey(User1, on_delete=models.CASCADE, null=True)
    message_provider = models.ForeignKey(WA_MSG_Provider, on_delete=models.CASCADE, null=True)
    u_token = models.CharField(max_length=1000, null=True, blank=True)
    gen_time = models.DateTimeField(null=True, blank=True)
    template = models.CharField(max_length=255, null=True, blank=True)
    lang = models.CharField(max_length=20, null=True, blank=True)


class Templates(models.Model):
    user = models.ForeignKey(User1, on_delete=models.CASCADE, null=True)
    message_provider = models.ForeignKey(WA_MSG_Provider, on_delete=models.CASCADE, null=True)
    temp_id = models.CharField(max_length=200, blank=True)
    temp_name = models.CharField(max_length=100, null=True, blank=True)
    lang_code = models.CharField(max_length=15, null=True, blank=True)
    is_media = models.BooleanField(blank=True)
    status = models.CharField(max_length=100, blank=True)
    med_id = models.CharField(max_length=255, null=True, blank=True)
    variables = models.CharField(max_length=255, null=True, blank=True)


class Chat_Templates(models.Model):
    user = models.ForeignKey(User1, on_delete=models.CASCADE, null=True)
    message_provider = models.ForeignKey(WA_MSG_Provider, on_delete=models.CASCADE, null=True)
    temp_id = models.CharField(max_length=200, blank=True)
    temp_name = models.CharField(max_length=100, null=True, blank=True)
    lang_code = models.CharField(max_length=15, null=True, blank=True)
    med_id = models.CharField(max_length=255, null=True, blank=True)
    is_media = models.BooleanField(default=0)
    json = models.JSONField(null=True)
    temp_preview = models.JSONField(null=True)
    status = models.CharField(max_length=100, blank=True)


class New_Templates(models.Model):
    user = models.ForeignKey(User1, on_delete=models.CASCADE, null=True)
    message_provider = models.ForeignKey(WA_MSG_Provider, on_delete=models.CASCADE, null=True)
    temp_name = models.CharField(max_length=100, null=True, blank=True)
    text_msg = models.TextField(null=True, blank=True)
    text_converted = models.CharField(max_length=1000, null=True, blank=True)
    lang_code = models.CharField(max_length=15, null=True, blank=True)
    category = models.CharField(max_length=255, null=True, blank=True)
    temp_id = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=100, blank=True)
    has_button = models.BooleanField(default=0)
    

class Conversation_Status(models.Model):
    to = models.CharField(max_length=15, null=True)
    provider = models.CharField(max_length=100, null=True)
    inbox_msg = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    template = models.CharField(max_length=100, null=True, blank=True)
    send_time = models.DateTimeField()
    received_time = models.DateTimeField(null=True, db_index=True)
    conversation_status = models.CharField(max_length=100, default="Pending")
    user_id = models.ForeignKey(User1, on_delete=models.CASCADE, null=True)


class What_Bot(models.Model):
    bot_name = models.CharField(max_length=100, null=True)
    is_on = models.BooleanField(default=0)
    message_pair = models.JSONField()
    provider = models.ForeignKey(WA_MSG_Provider, on_delete=models.CASCADE, null=True)
    user = models.ForeignKey(User1, on_delete=models.CASCADE, null=True)


class Bot_Auto_Reply(models.Model):
    receive_message = models.CharField(max_length=1000, null=True)
    reply_message = models.JSONField(null=True)
    show_reply_message = models.CharField(max_length=1000,null=True)
    msg_type = models.CharField(max_length=50, null=True)
    bot = models.ForeignKey(What_Bot, on_delete=models.CASCADE, null=True)
    provider = models.ForeignKey(WA_MSG_Provider, on_delete=models.CASCADE, null=True)
    is_active = models.BooleanField(default=1)


class CustomerBotStop(models.Model):
    user_number = models.CharField(max_length=15, null=True)
    provider_name = models.CharField(max_length=100, null=True)
    bot = models.ForeignKey(What_Bot, on_delete=models.CASCADE, null=True)
    provider = models.ForeignKey(WA_MSG_Provider, on_delete=models.CASCADE, null=True)


class SMS_Settings(models.Model):
    sms_url = models.CharField(max_length=1000, null=True, blank=True)
    both = models.BooleanField(null=True)
    whatsapp = models.BooleanField(null=True)
    sms = models.BooleanField(null=True)
    selective = models.BooleanField(null=True)
    keywords = models.CharField(max_length=500, blank=True, null=True)
    sel_whatsapp = models.BooleanField(null=True)
    sel_sms = models.BooleanField(null=True)
    usr = models.ForeignKey(User1, on_delete=models.CASCADE, null=True)

class MissMatched_Temps(models.Model):
    text_msg = models.CharField(max_length=1000, null=True)
    provider = models.ForeignKey(WA_MSG_Provider, on_delete=models.CASCADE, null=True)
    usr = models.ForeignKey(User1, on_delete=models.CASCADE, null=True)

class APP_Setting(models.Model):
    key = models.CharField(max_length=100, null=True, unique=True)
    value = models.CharField(max_length=1000, null=True)
    description = models.CharField(max_length=255, null=True, blank=True)

class Whatsapp_Token(models.Model):
    user = models.ForeignKey(User1, on_delete=models.CASCADE, null=True)
    prod = models.ForeignKey(WA_MSG_Provider, on_delete=models.CASCADE, null=True)
    token = models.CharField(max_length=100, null=True, unique=True)
    created_at = models.DateTimeField(null=True)
    valid_till = models.IntegerField(default=8)
    user_vice = models.BooleanField(default=0)
    provider_vice = models.BooleanField(default=0)
    provider_cus_pair = models.BooleanField(default=0)
    campaign_vice = models.BooleanField(default=0)
    customer_num = models.CharField(max_length=15, null=True)
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, null=True)
    adv_campaign = models.ForeignKey(AdvanceCampaign, on_delete=models.CASCADE, null=True)

class Reminder_Setting(models.Model):
    user = models.ForeignKey(User1, on_delete=models.CASCADE, null=True)
    wap = models.ForeignKey(WA_MSG_Provider, on_delete=models.CASCADE, null=True)
    birthday_temp = models.CharField(max_length=255,null=True) 
    anyversary_temp = models.CharField(max_length=255,null=True)
    scheduled_time = models.TimeField(null=True)
    is_active = models.BooleanField(default=1)

class Reminder_User(models.Model):
    user_name = models.CharField(max_length=100, null=True)
    user_mobile = models.CharField(max_length=15, null=True)
    birthdate = models.DateField(null=True)
    anniversary = models.DateField(null=True)
    remark = models.CharField(max_length=500, null=True, blank=True)
    setting = models.ForeignKey(Reminder_Setting, on_delete=models.CASCADE, null=True)
    is_active = models.BooleanField(default=1)
    b_sent = models.DateField(null=True)
    a_sent = models.DateField(null=True)
    b_msg_id = models.CharField(null=True, max_length=500)
    b_status = models.CharField(null=True, max_length=500)
    a_msg_id = models.CharField(null=True, max_length=500)
    a_status = models.CharField(null=True, max_length=500)
