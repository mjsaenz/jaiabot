#!/usr/bin/env python3

import asyncio
import xml.etree.ElementTree as ET
import pytak
import requests
from configparser import ConfigParser

STATUS_ENDPOINT = "http://localhost:40001/jaia/v0/status"
SLEEP = 8 # seconds

bot_callsigns = {
    1: "JAIA-1",
    2: "JAIA-2",
    3: "JAIA-3",
    4: "JAIA-4",
    5: "JAIA-5",
    6: "JAIA-6",
    7: "JAIA-7",
    8: "JAIA-8",
}

hub_callsigns = {
    1: "JAIA-HUB-1",
    2: "JAIA-HUB-2",
    3: "JAIA-HUB-3",
}

def create_cot_event(status):
            # Creating COT event from provided information:
            cot = ET.Element("xml")                        #<xml
            cot.set("version", "1.0")                      #   version = "1.0" />
            cot.set("encoding", "utf-8")                   #   ecoding = "utf-8" />
            cot.set("standalone", "yes")                   #   standalone = "yes" />

            event = ET.SubElement(cot, 'event')            #<event
            event.set("version", "2.0")                    #   version = "2.0"
            event.set("type", "b-m-p-s-p-i-c")             #   type = "a-k-G"

            if "bot_id" in status:
                 event.set("uid", bot_callsigns.get(status["bot_id"], "JAIABOT")) #   uid = "{callsign}"
            elif "hub_id" in status:
                 event.set("uid", hub_callsigns.get(status["hub_id"], "JAIAHUB"))

            event.set("how", "m-g")                        #   how = "m-g"
            event.set("time", pytak.cot_time())            #   time = "2023-07-04T08:00:01.22Z"
            event.set("start", pytak.cot_time())           #   start = "2023-07-04T08:00:01.22Z"
            event.set("stale", pytak.cot_time(120))        #   stale = "2023-07-04T08:00:03.22Z" />

            point = ET.SubElement(event, 'point')
            point.set("hae", "15.0")
            point.set("ce", "2.009")
            point.set("le", "3.7")

            if "location" in status:
                location = status["location"]
                point.set("lat", str(location["lat"]))
                point.set("lon", str(location["lon"]))

            detail = ET.SubElement(event, 'detail')
            contact = ET.SubElement(detail, 'contact')

            if "bot_id" in status:
                contact.set("callsign", bot_callsigns.get(status["bot_id"], "JAIABOT"))
            elif "hub_id" in status:
                contact.set("callsign", hub_callsigns.get(status["hub_id"], "JAIAHUB"))

            return ET.tostring(cot, encoding='utf-8')  #</xml>

def get_statuses():
    res = requests.get(STATUS_ENDPOINT)

    if res.status_code == 200:
        try:
            data = res.json()
        except Exception as e:
            print(f"Failed to parse JSON: {e}")
            print(f"Raw content: {res.text}")
            data = {}
    else:
        print(f"Failed to fetch status: {res.status_code}")
        data = {}

    return data

#############################
# Class Defintion for asynchronous delegate
#    Processes you Cursor-On-Target events information from above and
#    adds places the formatted XML onto the TX queue facing TAK Sever.
#############################
class AsyncDelegate(pytak.QueueWorker):

    async def handle_data(self, data):
    # This routine places COT events on TX queue.
        event = data
        await self.put_queue(event)

    async def run(self, number_of_iterations=-1):
    # This routine is the loop continually processing pre-COT data into an XML COT
    #    then it passes the data to the routine which puts COT events on the TX queue.
    #    Creates a new event every 30 seconds.
        while 1:
            statuses = get_statuses()
            print(statuses)
            if "bots" in statuses:
                 bot_statuses = statuses["bots"]
                 for bot_id in bot_statuses:
                      status = bot_statuses[bot_id]
                      cot_event = create_cot_event(status)
                      await self.handle_data(cot_event)
                      await asyncio.sleep(SLEEP)
            if "hubs" in statuses:
                hub_statuses = statuses["hubs"]
                for hub_id in hub_statuses:
                    status = hub_statuses[hub_id]
                    cot_event = create_cot_event(status)
                    await self.handle_data(cot_event)
                    await asyncio.sleep(SLEEP)

#############################
#############################


##############################
# MAIN APPLICATION ENTRY POINT
##############################
async def main():
    # Import amd build configuration object required for pyTAK
    config = ConfigParser()
    config.read('initiative.ini')
    config = config["connection"]

    # Initializes worker queues and tasks.
    clitool = pytak.CLITool(config)
    await clitool.setup()

    # Add your serializer to the asyncio task list.
    clitool.add_tasks(set([AsyncDelegate(clitool.tx_queue, config)]))

    # Start all tasks.
    await clitool.run()


if __name__ == "__main__":
    asyncio.run(main())
#############################
# END MAIN APPLICATION
#############################
