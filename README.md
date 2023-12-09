# smsPi-relay

This is a raspberry pi project, that activates a relay when SMS with defined keyword is recieved.



Prerequisites
- Raspbery Pi  (Raspbian OS installed) 
- USB modem with sim card (Huawei E176g was used)


1. To handle sending and recieving of messages we have to install gammu and gammu-smsd:
>sudo apt install gammu gammu-smsd



2. We need php to serve API that will provide json of recieved messages and http endpoint to send message.
>sudo apt install php php-json


3. Plug in USB modem with simcard inserted and restart Raspberry pi.


4. Some dongles are recognized as storage devices, in this case you have to use mode-switch to put it in modem mode. 
>ls -al /dev/ttyUSB0
![image](https://github.com/hrch3k/smsPi-relay/assets/24423488/4ea73a80-cdb1-44e2-bac9-b34877f95b41)
if you got output similar to this, it means your dongle is in modem mode. If not check here: (https://wiki-ubuntuusers-de.translate.goog/USB_ModeSwitch/?_x_tr_sl=de&_x_tr_tl=en&_x_tr_hl=de)


6. Run lsusb to check if raspberry has recognized your modem.
   ![image](https://github.com/hrch3k/smsPi-relay/assets/24423488/ed6fd849-89bc-4e2b-ba17-b90bfdf3ef8c)

   

7. To check if your dongle is recognized run gammu identify:
![image](https://github.com/hrch3k/smsPi-relay/assets/24423488/1ec949cc-539f-419c-9710-b638530328dc)


8. Edit gammu config file.
   ```bash
   sudo nano /etc/gammurc

10. Insert

   <pre>
   [gammu]
   device = /dev/ttyUSB0
   name = Telekom
   connection = at
   logfile = /var/log/gammu.log

   [smsd]
   service = files
   logfile = syslog
   #PIN = 1234 #use this if your simcard is locked
   # Increase for debugging information
   debuglevel = 0
   # Paths where messages are stored
   inboxpath = /var/spool/gammu/inbox/
   outboxpath = /var/spool/gammu/outbox/
   sentsmspath = /var/spool/gammu/sent/
   errorsmspath = /var/spool/gammu/error/
   </pre>



9. At this point you should be able to send SMS from command line with:
<pre> 
echo "some message" | gammu --sendsms TEXT 00386xxxxxxx </pre> (Change country code and phone number)


IF everything worked so far, you can now run gammu-smsd and set up API.

10. Create gammu-smsd config file:
    '''bash
    sudo nano /etc/gammu-smsdrc

    Add config:
    
    <pre>
    [gammu]
    # Please configure this!
    port = /dev/ttyUSB0
    connection = at
    # Debugging
    #logformat = textall

    # SMSD configuration, see gammu-smsdrc(5)
    [smsd]
    service = files
    logfile = syslog
    # Increase for debugging information
    debuglevel = 0

    # Paths where messages are stored
    inboxpath = /var/spool/gammu/inbox/
    outboxpath = /var/spool/gammu/outbox/
    sentsmspath = /var/spool/gammu/sent/
    errorsmspath = /var/spool/gammu/error/
    </pre>


12. Create folders:
    '''bash
    mkdir -p /var/spool/gammu/inbox/
    mkdir -p /var/spool/gammu/outbox/
    mkdir -p /var/spool/gammu/sent/
    mkdir -p /var/spool/gammu/error/




14. Start gammu in deamon mode:
    '''bash
    gammu-smsd -d -c /etc/gammurc

16. To check if gammu-smsd is running type:
    '''bash
    sudo systemctl status gammu-smsd


If gammu-smsd is not running due to permission error, you have to set permissions of /dev/ttyUSB0:
   '''bash
   sudo chmod 777 /dev/ttyUSB0



Sending messages
Since we're now have the gammu-smsd daemon talking to the dongle we can no longer use the gammu command from before to send SMS messages.
We still can send them though using the command gammu-smsd-inject which is designed to work with the smsd daemon and just injects the messages
into a local queue where it's then sent by the daemon.

The full example to send SMS messages from command line now would be
    '''bash
    gammu-smsd-inject TEXT 00386xxxxxxx -unicode -text "hello world from the daemon!"




Receiving messages
Okay now it's time to send some message back and see if it registers on the device. Just answer on one of the messages you got before and if everything worked, it should appear in /var/spool/gammu/inbox/ as a file.

Wait a few seconds and then check the folder for contents

'''bash ls /var/spool/gammu/inbox/
IN20211203_194458_00_+386xxxxxxx_00.txt

'''bash
pi:~# cat /var/spool/gammu/inbox/IN20211203_194458_00_++386xxxxxxx_00.txt
Hello also from the outside world!

So each message is contained in its own file. You can guess that the file name IN20211203_194458_00_+43664xxxxxxx_00.txt 
includes the date, time, phone number of the sender and a part number (for sms longer than 140 characters as they will be split up).




The API
We want a simple way to send and receive sms via API without installing hundreds of plugins and packages. Christian Haschek written two very slick php scripts that will do just that. 

Get it at https://github.com/geek-at/gammu-php

Make sure gammu-smsd is already running as the script won't work without it.

Then from the directory where the two php files (send.php and get.php) are stored, run php -S 0.0.0.0:8080 which will serve the two files to anyone on the network.

Sending SMS with the API
Is really straight forward. Just call <pre>http://ip.of.your.pi/send.php?phone=0664xxxxxxx&text=Testmessage</pre> from your browser or curl or python script.

Which will return a JSON object indicating if it failed (status:error), or succeeded (status:ok)

```markdown
```json
{
  "status": "ok",
  "log": "2021-12-04 15:43:39\ngammu-smsd-inject TEXT 0664xxxxxxx -unicode -text 'Testmessage'\ngammu-smsd-inject[2669]: Warning: No PIN code in /etc/gammu-smsdrc file\ngammu-smsd-inject[2669]: Created outbox message OUTC20211204_164340_00_0664xxxxxxx_sms0.smsbackup\nWritten message with ID /var/spool/gammu/outbox/OUTC20211204_164340_00_0664xxxxxxx_sms0.smsbackup\n\n\n"
}





Receiving SMS with the API
Is also very simple. Just call http://ip.of.your.pi/get.php

And it will return you all messages also in a JSON object
'''bash
curl -s http://ip.of.your.pi/get.php | jq .

```markdown
```json
[
  {
    "id": "f0a7789a657bb34eddd17c8e64609c48",
    "timestamp": 1638636342,
    "year": "2021",
    "month": "12",
    "day": "04",
    "time": "16:45",
    "test": "04.12.2021 16:45:42",
    "sender": "+43664xxxxxxx",
    "message": "Hello bob!"
  },
  {
    "id": "c358d0a4ca868c1d7d2eedab181eddd6",
    "timestamp": 1638636414,
    "year": "2021",
    "month": "12",
    "day": "04",
    "time": "16:46",
    "test": "04.12.2021 16:46:54",
    "sender": "+43664xxxxxxx",
    "message": "Hello "
  }
]


References:
https://blog.haschek.at/2021/raspberry-pi-sms-gateway.html#step1



