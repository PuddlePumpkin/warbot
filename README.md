To get a bot token:
go to the discord applications page https://discord.com/developers/applications, create a new application, give it a unique name - Go to the "bot" section -> click "add bot" -> click "reset token", this token can only be viewed once without having to reset it so take note of it. tick the intent switches on - Go to "OAuth2" section -> URL Generator -> click "bot" -> click administrator permission, or specific permissions if you know them -> copy and paste generated link into your browser or message it to who has permission to invite the bot to your discord.

To host with google cloud free tier:
cloud console -> compute engine -> google compute engine free tier options and set up instance exactly as says with debian -> click ssh button on the instance to open its console -> git clone https://github.com/PuddlePumpkin/warbot.git -> vim warbot/config/kiwitoken.json -> press i, paste your token from step 1 into token quotes ->press esc, press shift semicolon -> type wq press enter -> pip install -r src/requirements.txt -> then use following stuff to run kiwi in ssh and detach it:

screen -> cd warbot -> python3 src/kiwi.py -> CTRL-A, CTRL-D
to end a detached process:
screen -ls -> copy it's id -> screen -XS <screenid> quit