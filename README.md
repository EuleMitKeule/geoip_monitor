# geoip_monitor
Basic IP Monitoring for Ubuntu with Grafana World Map Plugin Integration

INSTRUCTIONS:

1. Put geoip_monitor.py and geoip_monitor.log and countries.csv in a folder

2. Run apt install geoiplookup

3. Have python3 and the following python packages installed:
  
  -datetime
  -time
  -subprocess
  -mysql.connector
  -csv
  -pytz
  -logging
  
4. Have a MariaDB MySQL server running

5. Create the Database 'geoip' and a user 'geoip' with access to the database

6. Create table 'geoip1' in the database 'geoip' with these columns:

  -latitude : float
  -longitude: float
  -datetime : datetime
  -country : varchar
  -ip : varchar
  -port : int

6.5 Put the host and password for MariaDB in geoip_monitor.py

7. Configure your iptables logging:

  -Run iptables -I INPUT 1 -p tcp -m tcp --tcp-flags FIN,SYN,RST,ACK SYN -j LOG --log-prefix "iptables: "
  -Run touch /var/log/iptables.log
  -Run touch /etc/rsyslog.d/10-iptables.conf
  -Run nano /etc/rsyslog.d/10-iptables.conf
  -Put in :msg, contains, "iptables: " -/var/log/iptables.log
          & ~
  -Run systemctl restart rsyslog

7.5 Put geoip_monitor.service in /etc/systemd/system/ and enable it via systemctl enable geoip_monitor
  
8. Get the Grafana World Map Plugin

9. Add your MariaDB as a data source to Grafana

10. Create a World Map Panel and feed it via this query:

    SELECT 
      Count(*) as metric, latitude as latitude, longitude as longitude, datetime, ip, country, now()

    FROM 
      geoip1

    WHERE
      datetime >= $__timeFrom() AND datetime <= $__timeTo() 

    GROUP BY 
      country
  
Should be working now.
