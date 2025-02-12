# Cortana Chat - Bluesky / AT Protocol based instant messaging client for XBMC4Xbox

A functional, decentralized and easy to use instant messenger, right on your Xbox.

![icon](icon.png)

## Screenshots:
![1](screenshots/1.png)
![2](screenshots/2.png)
![3](screenshots/3.png)
![4](screenshots/4.png)

## Install:
- Before downloading, make sure you're on XBMC 3.6-DEV-r33046 or later, as this most likely requires up to date TLS/SSL libraries!
- Download latest release .zip
- Extract the .zip file and edit "login.txt" to contain your full username (ie; username.bsky.social or username.custom.domain) and app password (do not use your actual password!)
- Edit "default.py" and modify "TIMEZONE_OFFSET = -5" to your local timezone relative to UTC (-5 is EST) for accurate timestamps
- Copy the xChat folder to Q:/scripts/plugins/programs
- (Optional) if using a non-Bluesky AT protocol site, you'll have to modify the BASE_URL in default.py to point at that site! Support outside of Bluesky is entirely unsupported, but testing & contributing is encouraged!
- Run the add-on and enjoy!

## Working
- Sending / receiving messages
- Receiving notifications (via notifier.py)

## Not Working
- TBA

## TODO:
- TBA
