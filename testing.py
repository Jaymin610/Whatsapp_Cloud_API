import datetime
from django.utils import timezone
import pytz

print(datetime.datetime.now(pytz.timezone('Asia/Kolkata')) + datetime.timedelta(hours=5.5))
print(datetime.datetime.now(timezone.utc))

data = {{"hello"}:"Yes welcom"}
print(data)