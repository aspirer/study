@echo off
cd /d d:\curl-7.26.0-rtmp-ssh2-ssl-sspi-zlib-idn-static-bin-w32
:HEARTBEAT
curl -X PUT -d 'heartbeat' http://169.254.169.254/heartbeat 2>nul 1>c:\heartbeat.log
ping 169.254.169.254 -n 6 -w 500 > nul
goto HEARTBEAT
@echo on