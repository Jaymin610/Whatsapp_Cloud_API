import re

# data = "Your account debit {#var#} Rs. LOAD Transfer from to account to {#var#} . Your Remaining balance is {#var#} RS. AT {#var#}.{#var#}Thank You"
# data = data.replace("{#var#}", "(.*)")
# p = re.compile(data)
# s = "Your account debit 5000 Rs. LOAD Transfer from to account to 81550 . Your Remaining balance is 15000 RS. AT this.GoodThank You"
# print(p.findall(s))

# my = "['stop please', 'hii', '1001']"
# ar = my.split(",")
# ar = [x.replace("[","").replace("]","").replace("'","").strip() for x in ar]
# print(ar)
# print("1001" in ar)

# for i, v in enumerate(ar):
#     print(i, v)
from time import sleep
from threading import Thread
 
# custom task function
def task():
    # execute a task in a loop
    for i in range(5):
        # block for a moment
        sleep(1)
        # report a message
        print('Worker thread running...')
    print('Worker closing down')
 
# create and configure a new thread
thread = Thread(target=task)
# start the new thread
thread.start()
# wait for the new thread to finish
thread.join()