import datetime
import re

# data = '''(.*) LOAD Transfer from your account to (.*). Your Remaining balance is (.*) (.*) Thank you'''
# # data = (data).replace("{#var#}", "(.*)")
# print(data)
# p = re.compile(data)
s = '''2000.00 LOAD Transfer from your account to 9766667549. Your Remaining   balance is 344420.23  11-Dec-2022 03:08:47 PM'''
print(s.replace("  ", " "))

# print(p.findall(s))

# my = "['stop please', 'hii', '1001']"
# ar = my.split(",")
# ar = [x.replace("[","").replace("]","").replace("'","").strip() for x in ar]
# print(ar)
# print("1001" in ar)

# for i, v in enumerate(ar):
#     print(i, v)
# print((datetime.date(2022, 11, 29) - datetime.date.today()).days)
# print("yes" if [''] else "no")
# print("Yes" if "हां" in ["Yes", "हां"] else "हां")
# data = [{
# "name": "testing_statusupdate",
# "components": [
# {
# "type": "HEADER",
# "format": "TEXT",
# "text": "Dear User"
# },
# {
# "type": "BODY",
# "text": "Dear Partner, Your account received Rs. {{1}} as balance transfer from Admin on {{2}}. Your new balance is Rs. {{3}}.Thank you"
# },
# {
# "type": "FOOTER",
# "text": "By Jaymin_Test"
# }
# ],
# "language": "en",
# "status": "APPROVED",
# "category": "TRANSACTIONAL",
# "id": "457848186514942"
# },
# {
# "name": "checking_otp",
# "components": [
# {
# "type": "HEADER",
# "format": "TEXT",
# "text": "Dear User"
# },
# {
# "type": "BODY",
# "text": "Your OTP for account registration is {{1}}. Don't share this code with anyone. Contact us on {{2}}. In case of query.  Thank you"
# },
# {
# "type": "FOOTER",
# "text": "By Jaymin_Test"
# }
# ],
# "language": "en",
# "status": "APPROVED",
# "category": "OTP",
# "id": "936339700680844"
# }]

# for d in data:
#     print("Comp check")
#     if d['components']:
        
#         if d['components'][1]['type'] == "BODY":
#             continue
#         else:
#             print("pass")
#             pass