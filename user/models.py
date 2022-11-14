from django.db import models


# Create your models here.

class User1(models.Model):

    def __str__(self):
        return self.user_name
    class Meta:
        verbose_name_plural = 'Users'
    @staticmethod
    def authenticate(email, passw):
        return User1.objects.filter(email=email.lower(), password=passw, is_active=True)

    def login(self):
        self.is_auth = True
        self.save()

    def logout(self):
        self.is_auth = False
        self.save()

    def is_authenticated(self):
        print(self.is_auth)
        return self.is_auth

    user_name = models.CharField(max_length=32, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    password = models.CharField(max_length=25, blank=True, null=True)
    phone_no = models.CharField(max_length=15, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=False)
    updated_at = models.DateTimeField(auto_now=True, blank=False)
    is_auth = models.BooleanField(default=False)


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
    msg_id = models.CharField(max_length=255, blank=True, null=True)
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
    msg_id = models.CharField(max_length=255, blank=True, null=True)
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


class MessageLog(models.Model):
    user = models.ForeignKey(User1, on_delete=models.CASCADE, null=True)
    sender_number = models.CharField(max_length=15)
    received_msg = models.CharField(max_length=1000, null=True, blank=True)
    received_time = models.DateTimeField()
    is_read = models.BooleanField(default=0)
    reply = models.CharField(max_length=1000, null=True, blank=True)
    send_time = models.DateTimeField(null=True)
    reply_number = models.CharField(max_length=15)
    status = models.CharField(max_length=10, null=True)
    json = models.JSONField(max_length=1000, null=True)
    request = models.CharField(max_length=255, null=True)
    response = models.CharField(max_length=1000, null=True)
    msg_id = models.CharField(max_length=255, blank=True, null=True)


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
    msg_id = models.CharField(max_length=255, blank=True, null=True)


class CallBack_Data(models.Model):
    user = models.ForeignKey(User1, on_delete=models.CASCADE, null=True)
    Received = models.TextField(null=True)
    received_time = models.DateTimeField(null=True)
    msg_id = models.CharField(max_length=255, blank=True, null=True)
    msg_status = models.CharField(max_length=50, blank=True, null=True)


class OutBox(models.Model):
    user = models.ForeignKey(User1, on_delete=models.CASCADE, null=True)
    to_number = models.CharField(max_length=15, null=True)
    message = models.CharField(max_length=1000, null=True, blank=True)
    send_time = models.DateTimeField(null=True)
    reply_number = models.CharField(max_length=100)
    msg_id = models.CharField(max_length=255, blank=True, null=True)
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


class Conversation_Status(models.Model):
    to = models.CharField(max_length=15, null=True)
    provider = models.CharField(max_length=100, null=True)
    inbox_msg = models.CharField(max_length=255, null=True, blank=True)
    template = models.CharField(max_length=100, null=True, blank=True)
    send_time = models.DateTimeField()
    received_time = models.DateTimeField(null=True)
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
    bot = models.ForeignKey(What_Bot, on_delete=models.CASCADE, null=True)
    provider = models.ForeignKey(WA_MSG_Provider, on_delete=models.CASCADE, null=True)


class CustomerBotStop(models.Model):
    user_number = models.CharField(max_length=15, null=True)
    provider_name = models.CharField(max_length=100, null=True)
    bot = models.ForeignKey(What_Bot, on_delete=models.CASCADE, null=True)
    provider = models.ForeignKey(WA_MSG_Provider, on_delete=models.CASCADE, null=True)