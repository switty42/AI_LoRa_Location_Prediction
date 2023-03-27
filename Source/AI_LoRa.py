# LoRa Location Algorithm
# Author Stephen Witty
# 3-10-23
# ChatGPT version (example code from rollbar.com)
#
# V1 3-21-23 - Initial dev
# V2 3-23-23 - Try / Catch logic, better parsing

import json
import math
import datetime
import openai
import time
import sys

openai.api_key = "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"

gpt_model='gpt-3.5-turbo'

# Constants ##########################################################################################################
DATA_SET = "Red_October_DS_030923.txt" # File name of data-set to process
MAX_MILES = 10                         # Max miles for hotspot distance before flagging possible misplacement 
MAX_RSSI = -95                         # Max RSSI for hotspot before flagging possible misplacement
                                       # Hotspots that might be misplaced
BLOCKED_LIST = ["short-tin-pig", "ancient-marmalade-wren", "huge-paisley-ostrich"]
######################################################################################################################

gpt_message="Provide back the estimated latitude and longitude  of the transmitting device \
given the data set at the end of this message that contains the latitude, longitude, rssi, snr and frequency \
values of the radio receivers getting the transmission.  The radios involved are LoRa based.  \
Remove radio receiver outliers as needed.  \
When determining if a receiver is an outlier assume that the rssi, snr, and ferquency are correct but the \
latitude and longitude positional information might be wrong.  \
If there is not enough information for better methods  \
average the remaining reciever positions to provide the position of the transmitter answer.  \
Provide back the latitude and longitude answer inside braces \
with a space in between the latitude and longitude numerical answer.  \
Let's take it step by step.  \
Describe how you arrived at the answer.  Always provide an answer even if uncertain.  \
Here is an example of the answer format {36.2248 -94.14006}.  The data set follows. "

######################################################################################
# Distance between pairs of lat / longs
# from here:
# https://stackoverflow.com/questions/27928/calculate-distance-between-two-latitude-longitude-points-haversine-formula */

def getDistanceFromLatLon(lat1,lon1,lat2,lon2):
   R = 6371 # Radius of the earth in km
   dLat = math.radians(lat2-lat1)  # deg2rad below
   dLon = math.radians(lon2-lon1)

   a = math.sin(dLat/2) * math.sin(dLat/2) + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dLon/2) * math.sin(dLon/2)

   c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
   d = R * c # Distance in km
   d = d * .621371 # Convert to miles
   return d

################################# Print and format a string #############################################
def print_string(string):
   cnt = 0
   last_letter = ""
   for letter in string:
      if (cnt > 60 and last_letter == " " and letter != " "):
         print("")
         cnt = 0
      print (letter,sep='',end='')
      last_letter = letter
      cnt = cnt + 1
      if (letter == '\n' or letter == '\r'):
         cnt = 0
   print("")
   sys.stdout.flush()
#########################################################################################################

print("ChatGPT LoRa Location Prediction V2") 

ap_start_time = time.time()

print("Data set name:",DATA_SET)

# Read in JSON file with dataset
f = open(DATA_SET)
data = json.load(f)
f.close()

print("Number of position / transmit records:",len(data))

first_time_stamp = data[0]["decoded"]["payload"]["timestamp"]
last_time_stamp = data[len(data)-1]["decoded"]["payload"]["timestamp"]

print("Data set start time:",datetime.datetime.fromtimestamp(first_time_stamp).strftime("%m-%d-%y %H:%M:%S"))
print("Run time in minutes:","%.0f"%((last_time_stamp - first_time_stamp) / 60))

################################### Calculate stats ##########################################
distance = 0
max = 0
index = 0
avg = 0
hotspot_list=[]
hot_spot_cnt = 0
only_one_hotspot = 0
blocked_hotspots=BLOCKED_LIST.copy() # Verify that there is no typo in blocked list

for rec in data:
   if (index > 0):
      distance = distance + getDistanceFromLatLon(rec["decoded"]["payload"]["lat"],rec["decoded"]["payload"]["long"],current_lat,current_long)
   current_lat = rec["decoded"]["payload"]["lat"]
   current_long = rec["decoded"]["payload"]["long"]
   avg = avg + len(rec["hotspots"])
   if (len(rec["hotspots"]) == 1):
      only_one_hotspot = only_one_hotspot + 1
   if (max < len(rec["hotspots"])):
      max = len(rec["hotspots"])
      max_lat = current_lat
      max_long = current_long
   for hotspot in rec["hotspots"]:
      hot_spot_cnt = hot_spot_cnt + 1
      if (hotspot["name"] in blocked_hotspots): # Verify that there is no typo in blocked list
         blocked_hotspots.remove(hotspot["name"])
      if (hotspot["name"] not in hotspot_list):
         hotspot_list.append(hotspot["name"])
   index = index + 1

avg = avg / len(data)

print("Number of hotspots seen:",hot_spot_cnt)
print("Number of unique hotspots:",len(hotspot_list))
print("Max number of hotspots seen on a single transmit: ",max," (",max_lat,", ",max_long,")",sep="")
print("Average number of hotspots per transmit:","%.2f"%avg)
print("Data set distance in miles:","%.1f"%distance)
print("Number of transmits with only one hotspot seen:",only_one_hotspot)

if (len(blocked_hotspots) != 0):
   print("\n****** WARNING - Not all blocked hotspots are in data set")

########################## Check for any duplicate hotspot names by id (I have read this happens) ###############
hotspot_list = {}
dup_found = False
for rec in data:
   for hotspot in rec["hotspots"]:
      if (hotspot["name"] in hotspot_list):
         if (hotspot_list[hotspot["name"]] != hotspot["id"]):
            dup_found = True
      else:
         hotspot_list[hotspot["name"]]=hotspot["id"]
if (dup_found == True):
   print("******* WARNING - Found duplicated hotspot name id pair")

########################### Look for hotspots that might be misplaced we be used to construct a blocked list ###########################
index = 0

print("\nHotspots that are more than",MAX_MILES,"miles from GPS coordinates and RSSI greater than",MAX_RSSI,"-> possible placement error")
print("**********************************************************************************")

for rec in data:
   gps_lat = rec["decoded"]["payload"]["lat"]
   gps_long = rec["decoded"]["payload"]["long"]
   for hotspot in rec["hotspots"]:
      lat = hotspot["lat"]
      long = hotspot["long"]
      rssi = hotspot["rssi"]
      error = getDistanceFromLatLon(gps_lat,gps_long,lat,long)
      name = hotspot["name"]
      name = name.ljust(25," ")
      if (error > MAX_MILES and rssi > MAX_RSSI):
         print("%.0f"%error,index,name,rssi,"%.5f"%gps_lat,"%.5f"%gps_long,"%.5f"%lat,"%.5f"%long)
   index = index + 1

############################## ChatGPT ##################################################
print("\n\nPrompt being sent to ChatGPT with appended Hotspot information:\n\n")

print_string(gpt_message)

index = 0
avg_error = 0
previous_time_stamp = 0

for rec in data:

   print("\n*********************** Message index:",index,"*************************\n")

   gps_lat = rec["decoded"]["payload"]["lat"]
   gps_long = rec["decoded"]["payload"]["long"]
   current_time_stamp = rec["decoded"]["payload"]["timestamp"]

   print("Unix epoch timestamp of this record:",current_time_stamp)
   if (previous_time_stamp != 0):
      print("Previous timestamp:",previous_time_stamp,"Seconds from current:",current_time_stamp-previous_time_stamp)
   print("\nName                            RSSI  SNR                 Frequency           Latitude            Longitude\n")
   for hotspot in rec["hotspots"]:
      print(hotspot["name"].ljust(31),str(hotspot["rssi"]).ljust(5),str(hotspot["snr"]).ljust(19),str(hotspot["frequency"]).ljust(19),str(hotspot["lat"]).ljust(19),str(hotspot["long"]).ljust(19))

   gpt_message_send = gpt_message

   for hotspot in rec["hotspots"]:
      rssi = hotspot["rssi"]
      lat = hotspot["lat"]
      long = hotspot["long"]
      snr = hotspot["snr"]
      frequency = hotspot["frequency"]

      gpt_message_send = gpt_message_send + "(latitude="+str(lat)+", "+"longitude="+str(long)+", "+"rssi="+str(rssi)+", "+"snr="+str(snr)+", "+"frequency="+str(frequency)+") "

   if (index > 0):
      gpt_message_send = gpt_message_send + "The last known position for the transmitter was (latitude="+str(gpt_lat)+", "+"longitude="+str(gpt_long)+") "+str(current_time_stamp-previous_time_stamp)+" seconds ago.  The tranimser is likley nearby."

   if (index < 3):
      print("\nComplete message being sent to AI %%%%%%%%%%%%\n")
      print_string(gpt_message_send)

   sys.stdout.flush()

   if (len(rec["hotspots"]) > 1): # Only call GPT if the number of hotspots is more than one

      # GPT query
      GPT_complete = False
      total_retries = 0
      while GPT_complete == False:
         time.sleep(1)
         if (total_retries > 15): # Exit program if we have tried too many times
            sys.exit()

         GPT_complete = True
         try:
            response = openai.ChatCompletion.create(model=gpt_model, messages=[ {"role": "system", "content": "You are a helpful assistant."}, {"role": "user", "content": gpt_message_send},])
         except Exception as e:
            print("SYSTEM_ERROR1 during ChatGPT call, Retrying...\n",e,sep='')
            total_retries = total_retries + 1
            GPT_complete = False
            sys.stdout.flush()
            continue

         message = response.choices[0]['message']

         print("\nBegin GPT answer >>>>>>>>\n")
         print_string(message['content'])
         print("\n\nEnd GPT answer ########")

         sys.stdout.flush()

         gpt_lat = 0 # These two defines are required incase an exception occurs for NaN check
         gpt_long = 0

         try:
            # Parse out lat long inside of {} inside GPT answer
            cnt = 0
            buf = message['content']
            buf2 = ""

            while(buf[cnt] != '{'):
               cnt = cnt + 1

            cnt = cnt + 1 # Skip over open bracket
            while(buf[cnt] != '}'):
               buf2 = buf2 + buf[cnt]
               cnt = cnt + 1

            buf2 = buf2.replace(","," ")
            token = buf2.split()

            gpt_lat = float(token[0])
            gpt_long = float(token[1])
         except Exception as e:
            print("SYSTEM_ERROR2 decoding message, Retrying......\n",e,sep='')
            total_retries = total_retries + 1
            GPT_complete = False # Will retry GPT call if decoding failed
            sys.stdout.flush()
         if (math.isnan(gpt_lat) == True or math.isnan(gpt_long) == True):
            GPT_complete = False
            print("SYSTEM_ERROR3 received NaN, Retrying......\n",sep='')

      print("\nGPT location:",str(gpt_lat).ljust(18),str(gpt_long).ljust(18))
   ######### End of if statement for more than one hotspot

   index = index + 1

   if (len(rec["hotspots"]) == 1): # We skipped GPT if only one hotspot for this record
      print("\nSince number of hotspots is one, skipping Chat_GPT")
      gpt_lat =  lat       # In this case, this is the lat of the only hotspot from above loop
      gpt_long = long      # In this case, this is the long of the only hotspot from above loop
      print("Single hotspot location: ",lat,long)

   error = getDistanceFromLatLon(gps_lat,gps_long,gpt_lat,gpt_long)
   avg_error = avg_error + error
   total_avg_error = avg_error / index
   current_run_time = (time.time()-ap_start_time)/60
   run_time_per_record = current_run_time / index
   estimated_remaining_time = (len(data) - index) * run_time_per_record

   print("GPS location:",str(gps_lat).ljust(18),str(gps_long).ljust(18))
   print("\nDistance error in miles: ","%.3f"%error,sep='')

   if (error > 5):
      print("WARNING - error greater than 5 miles")

   print("Current running error average in miles:","%.3f"%total_avg_error)
   print("\nAp runtime so far in minutes:","%.2f"%current_run_time)
   print("Runtime per record in minutes:","%.2f"%run_time_per_record)
   print("Time remaining in minutes:","%.2f"%estimated_remaining_time)

   print("\nCSV",current_time_stamp,index,"%.3f"%error,"%.3f"%total_avg_error,gps_lat,gps_long,gpt_lat,gpt_long)

   previous_time_stamp = current_time_stamp
#   if (index == 3):
#      break

   sys.stdout.flush()

print("\n#################################################\n")
print("Ap run time in minutes:","%.1f"%((time.time()-ap_start_time)/60))
print("Final average error in miles for data set:","%.3f"%total_avg_error)
