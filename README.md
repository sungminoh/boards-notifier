```
>> python snulife.py --help

usage: snulife.py [-h] [--user_id USER_ID] [--password PASSWORD]
                  [--sender SENDER] [--gmail_password GMAIL_PASSWORD]
                  [--receiver RECEIVER] [--title TITLE] [--url URL]
                  [--filter FILTER] [--keep_running KEEP_RUNNING]
                  [--class_name CLASS_NAME]

snulife new post alarm

optional arguments:
  -h, --help            show this help message and exit
  --user_id USER_ID, -u USER_ID
                        snulife user id
  --password PASSWORD, -p PASSWORD
                        snulife password
  --sender SENDER, -s SENDER
                        sender email address or gmail id
  --gmail_password GMAIL_PASSWORD, -gp GMAIL_PASSWORD
                        gmail account password if sender is gmail account
  --receiver RECEIVER, -r RECEIVER
                        receiver (ex. asd@asd.net,qwe@qwe.com)
  --title TITLE, -t TITLE
                        email subject
  --url URL, -l URL     target url
  --filter FILTER, -f FILTER
                        regex filter
  --keep_running KEEP_RUNNING, -k KEEP_RUNNING
                        target class name
  --class_name CLASS_NAME, -c CLASS_NAME
                        target class name
```
