from __future__ import print_function
from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime
from requests import get
from xml.etree import ElementTree
from yagmail import SMTP
import os

items_wanted = {
    "Lagkapten 120 svart": "40488536"#,
#    "Adils leg":"00217976",
#    "Millberget vit chair":"00339416"
}
local_stores = {
    "Bangna": "057",
    "Bang Yai": "479"
}
region = 'th'
locale = 'en'
availability_url = 'http://www.ikea.com/{region}/{locale}/iows/catalog/availability/{item_id}'


def query():
    available = False
    output = []
    gmail_user = os.environ.get('GMAIL_USER')
    gmail_password = os.environ.get('GMAIL_PASSWORD')

    for item_name, item_id in items_wanted.items():
        availability_data = get(availability_url.format(region=region, locale=locale,
                                                        item_id=item_id))
        print(availability_data.content[:400])
        for city, code in local_stores.items():
            available_qty = int(ElementTree.fromstring(availability_data.content)
                                .find(".//localStore[@buCode='{code}']".format(code=code))
                                .find('.//availableStock').text)
            restock_date = ElementTree.fromstring(availability_data.content)\
                .find(".//localStore[@buCode='{code}']".format(code=code))\
                .find('.//restockDate').text
            print(f"Restock Date: {city} {item_name} {restock_date}")
            if available_qty > 0:
                available = True
                message = "{} available {} ({}) {} @ {}".format(
                    available_qty, item_name, item_id, city, datetime.now())
                output.append(message)
                print(message)

    if available and gmail_user and gmail_password:
        # SMTP(gmail_user, gmail_password).send(to=gmail_user, subject='Ikea Availability',
        #                                       contents='\n'.join(output))
        # print("sending mail")
        try:
            #initializing the server connection
            yag = SMTP(user=gmail_user, password=gmail_password)
            #sending the email
            yag.send(to=gmail_user, subject='Ikea Availability', contents='\n'.join(output))
            print("Email sent successfully")
        except:
            print("Error, email was not sent")
    else:
        print('No items available @ {}'.format(datetime.now()))


if __name__ == '__main__':
    scheduler = BlockingScheduler()
    scheduler.add_job(query, 'interval', hours=6)
    query()
    print('Press Ctrl+{} to exit'.format('Break' if os.name == 'nt' else 'C'))

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print('See ya!')

