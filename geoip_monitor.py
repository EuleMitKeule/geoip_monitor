#!/usr/bin/python3 -u
from datetime import datetime
import time
import subprocess
import mysql.connector as mariadb
import csv
import pytz
import logging
import sys, os


log_file = 'geoip_monitor.log'
countries_csv = 'countries.csv'
iptables_log = '/var/log/iptables.log'

ips_to_exclude = ["192", "172", "127"]
check_interval = 10

local_tz = pytz.timezone('xxxx/xxxx')
target_tz = pytz.timezone('UTC')

logging.basicConfig(filename=log_file, level=logging.DEBUG)

logging.info(">> GEOIP_MONITOR STARTED")

last_time = datetime.now()

try:
    db = mariadb.connect(host='xxx.xxx.xxx.xxx', user='geoip', password='xxxxxxxxxxxx', database='geoip')
    cursor = db.cursor()
except Exception as ex:
    logging.warn(datetime.now().strftime("%b %d %X") + f" >> ERROR: Connection to database failed!\n>>" + str(ex))
    quit()

logging.info(datetime.now().strftime("%b %d %X") + f" >> INFO: Connected to GEOIP_MONITOR database successfully.")

def get_coordinates(country):
    try:
        try:
            countries = csv.DictReader(open(countries_csv))
        except Exception as ex:
            logging.warn(datetime.now().strftime("%b %d %X") + f" >> ERROR: Opening the coordinate database failed!\n>>" + str(ex))
            quit()
        for row in countries:
            if (row['country'] == country):
                lat = row['latitude']
                long = row['longitude']
                return lat, long
        logging.warn(datetime.now().strftime("%b %d %X") + f" >> WARN: Country code '{country}' not found in coordinate database!")
        return 0, 0
    except Exception as ex:
        logging.warn(datetime.now().strftime("%b %d %X") + f" >> ERROR: Coordinate lookup failed for country code '{country}'!\n>>" + str(ex))
        return 0, 0
    
logging.info(datetime.now().strftime("%b %d %X") + f" >> INFO: Starting up traffic monitoring.")

try:
    while True:
        try:
            lines = open(iptables_log).readlines() #maybe put this outside the while loop
        except Exception as ex:
            logging.warn(datetime.now().strftime("%b %d %X") + f" >> ERROR: Opening the iptables log file failed!\n>>" + str(ex))
            quit()

        for i, line in enumerate(lines):

            line = line.replace('  ', ' ')
            month, day, timestamp = line.split(' ', 3)[:3]
            cur_time = datetime.strptime(month + " " + day + " " + timestamp, "%b %d %X")
            cur_time = cur_time.replace(year=datetime.now().year)

            if (last_time >= cur_time):
                continue

            last_time = datetime.now()
            last_time = last_time.replace(minute=(last_time.minute - 1) % 60)
            ip_index = line.find("SRC=")
            dst_index = line.find("DST=")

            ip = line[ip_index:dst_index]
            ip = ip.split("=")[1]
            ip = ip.replace(" ", "")

            dpt_index = line.find("DPT=")
            wd_index = line.find("WINDOW=")

            port = line[dpt_index:wd_index]
            port = port.split("=")[1]
            port = port.replace(" ", "")

            print(port)

            if (any(ip.startswith(ip_ex) for ip_ex in ips_to_exclude)):
                continue

            try:
                result = subprocess.run(["geoiplookup", ip], stdout=subprocess.PIPE)
                country = result.stdout.decode('utf-8')
            except Exception as ex:
                logging.warn(datetime.now().strftime("%b %d %X") + f" >> ERROR: Subprocess for 'geoiplookup' failed! Maybe 'apt install geoiplookup'?\n>>" + str(ex))
                continue

            country = country.split(" ")[3].replace(",", " ")
            country = country.replace(" ", "")

            latitude, longitude = get_coordinates(country)

            cur_time = local_tz.localize(cur_time)
            cur_time = target_tz.normalize(cur_time)

            cur_time_min1 = cur_time.replace(minute=(cur_time.minute - 1) % 60)

            try:
                cursor.execute(f"SELECT * FROM geoip1 WHERE DATETIME >= '{cur_time_min1.strftime('%Y-%m-%d %X')}' AND DATETIME <= '{cur_time.strftime('%Y-%m-%d %X')}' AND ip = '{ip}' AND port = '{port}';")
                cursor.fetchall()
            except Exception as ex:
                logging.warn(datetime.now().strftime("%b %d %X") + f" >> ERROR: IP lookup in GEOIP_MONITOR database failed!\n>>" + str(ex))
                try:
                    db = mariadb.connect(host='127.0.0.1', user='geoip', password='ZWQbGrECmn3A2Z8PytfuPCJeHxZbcNvJnbVkyRUXbUfpfQRjVreM79vJURFc7trf', database='geoip')
                    cursor = db.cursor()
                except Exception as ex:
                    logging.warn(datetime.now().strftime("%b %d %X") + f" >> ERROR: Connection to database failed!\n>>" + str(ex))
                    quit()
                continue

            if (cursor.rowcount != 0):
                continue        

            try:
                cursor.execute(f"INSERT INTO geoip1(latitude,longitude,datetime,country,ip,port) VALUES ({latitude},{longitude},'{cur_time.strftime('%Y-%m-%d %X')}','{country}','{ip}',{port});")
                db.commit()
            except Exception as ex:
                logging.warn(datetime.now().strftime("%b %d %X") + f" >> ERROR: IP insert into GEOIP_MONITOR database failed!\n>>" + str(ex))
                continue                                                                                                                                                                                                                     
            
        time.sleep(check_interval)
except Exception as ex:
    logging.warn(datetime.now().strftime("%b %d %X") + f" >> ERROR: Something went wrong!\n>> {str(ex)}")
