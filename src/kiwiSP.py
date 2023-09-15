import asyncio
import pytz
import json
import os
import shutil
import sys
import datetime
import traceback
import hikari
import lightbulb
import warnings
from lightbulb.ext import tasks
epoch_time = datetime.datetime(1970, 1, 1)
os.chdir(str(os.path.abspath(os.path.dirname(os.path.dirname(__file__)))))

# ----------------------------------
# Instantiate a Bot instance
# ----------------------------------
bottoken = ""
with open('config/kiwitoken.json', 'r') as openfile:
    tokendict = json.load(openfile)
    if tokendict["bottoken"] != "" and tokendict["bottoken"] != None:
        bottoken = tokendict["bottoken"]
    else:
        try:
            bottoken = os.environ["kiwitoken"]
        except:
            pass
    if tokendict["guildID"] != None and tokendict["guildID"] != "":
        guildId = int(tokendict["guildID"])
    else: 
        warnings.warn("Commands will not update quickly without a guild ID in config/kiwitoken.json",UserWarning)
        guildId = None
    openfile.close()
if bottoken == None or bottoken == "":
    sys.exit("\nYou need a bot token, see readme.md for usage instructions")
if guildId != None:
    try:
        bot = lightbulb.BotApp(token=bottoken,intents=hikari.Intents.ALL_UNPRIVILEGED,help_class=None,default_enabled_guilds=guildId, logs = "ERROR",force_color=True,banner = "banner")
    except:
        bot = lightbulb.BotApp(token=bottoken,intents=hikari.Intents.ALL_UNPRIVILEGED,help_class=None,default_enabled_guilds=guildId, logs = "ERROR",force_color=True)
else:
    try:    
        bot = lightbulb.BotApp(token=bottoken,intents=hikari.Intents.ALL_UNPRIVILEGED,help_class=None,logs= "ERROR",force_color=True,banner = "banner")
    except:
        bot = lightbulb.BotApp(token=bottoken,intents=hikari.Intents.ALL_UNPRIVILEGED,help_class=None,logs= "ERROR",force_color=True)

# ----------------------------------
# Bot ready event
# ----------------------------------
@bot.listen(hikari.ShardReadyEvent)
async def ready_listener(_):
    pass

# ----------------------------------
# Ping Command
# ----------------------------------
@bot.command
@lightbulb.command("ping", "checks the bot is alive")
@lightbulb.implements(lightbulb.SlashCommand)
async def ping(ctx: lightbulb.SlashContext) -> None:
    await ephemeral_respond("Pong!", ctx, 0x00ff1a)


# ----------------------------------
# BDO command group
# ----------------------------------
@bot.command
@lightbulb.command("bdo","bdo")
@lightbulb.implements(lightbulb.SlashCommandGroup)
async def bdo(ctx: lightbulb.Context) -> None:
    await ctx.respond("invoked main bdo")

async def ephemeral_respond(text: str, ctx: lightbulb.SlashContext, color=0xff0015):
    '''Generate an embed and respond to the context with the input text'''
    await ctx.respond(text, flags=hikari.MessageFlag.EPHEMERAL)

signups = {}

# ----------------------------------
# war command
# ----------------------------------
@bdo.child
@lightbulb.option("reloadfromfile", "reload signups from saved file", required=False, default=False, type=bool)
@lightbulb.option("cannonscap", "max players on cannon team", required=True, max_value=40, min_value=0, type=int)
@lightbulb.option("flexcap", "max players in flex team", required=True, max_value=40, min_value=0, type=int)
@lightbulb.option("defencecap", "max players in defence team", required=True, max_value=40, min_value=0, type=int)
@lightbulb.option("mainballcap", "max players in mainball team", required=True, max_value=40, min_value=0, type=int)
@lightbulb.option("playercap", "max players across all teams", required=True, max_value=100, min_value=1, type=int)
@lightbulb.option("pdtmeetupdatetime", "PDT Day and time for meetup formatted like 12/24/2023 9:54 pm", required=True, type=str)
@lightbulb.option("embedtitle", "title to show at top of embed", required=False, default = "NODE WAR", type=str)
@lightbulb.command("war", "war signups")
@lightbulb.implements(lightbulb.SlashSubCommand)
async def warsignups(ctx: lightbulb.SlashContext) -> None:
    try:
        hasrole = await check_for_roles(ctx,[1152085844128178197,1120170416384790538])
        if not hasrole:
            await ephemeral_respond("You must have staff role to use this command", ctx)
            return
        global signups
        signups = {}
        if(ctx.options.reloadfromfile):
            loadfromfile()
        embed = generate_war_embed(ctx)
        rows = await generate_rows(ctx.bot)
        response = await ctx.respond(embed, components=rows)
        message = await response.message()
        await handle_responses(ctx.bot, ctx.author, ctx.member, message,ctx=ctx, autodelete=False)

    except Exception:
        traceback.print_exc()
        await ephemeral_respond("Sorry, something went wrong...",ctx)
# ----------------------------------
# load signups command
# ----------------------------------
def loadfromfile():
    global signups
    try:
        f = open('config/signuplist.json', 'r')
    except:
        return
    signups = json.load(f)

# ----------------------------------
# add member command
# ----------------------------------
@bdo.child
@lightbulb.option("team", "which team to add to", required=True, choices=["mainball","defence","flex","cannons","bench","tentative","absent"], type=str)
@lightbulb.option("idlist", "ID or ids separated by commas", required=True, type=str)
@lightbulb.command("addplayers", "manually add players")
@lightbulb.implements(lightbulb.SlashSubCommand)
async def addplayer(ctx: lightbulb.SlashContext) -> None:
    global signups
    try:
        int_list = [int(x) for x in ctx.options.idlist.split(',')]
        for id in int_list:
            id = str(id)
            fetchedmember = await bot.rest.fetch_member(ctx.guild_id, id)
            if id in signups:
                signups[id]['role'] = ctx.options.team
            else:
                signups[id] = {"name": str(fetchedmember.display_name), "role": ctx.options.team}

        await ephemeral_respond("Players added. RE-PRESS A TEAM BUTTON TO REFRESH TEAM EMBED" ,ctx)
        return
    except:
        await ephemeral_respond("something went wrong..." ,ctx)

# ----------------------------------
# Remove member command
# ----------------------------------
@bdo.child
@lightbulb.option("remove", "completely remove player from any team and do not bench them", required=False, default=False, type=bool)
@lightbulb.option("id", "ID (right click their name on member list to copy id)", required=True, type=str)
@lightbulb.command("benchplayer", "Remove or bench a player")
@lightbulb.implements(lightbulb.SlashSubCommand)
async def benchplayer(ctx: lightbulb.SlashContext) -> None:
    global signups
    try:
        if ctx.options.remove:
            signups.pop(ctx.options.id)
            savesignup(signups)
            await ephemeral_respond("Player removed, RE-PRESS A TEAM BUTTON TO REFRESH TEAM EMBED" ,ctx)
        else:
            signups[ctx.options.id]["role"] = 'bench'
            savesignup(signups)
            await ephemeral_respond("Player benched, RE-PRESS A TEAM BUTTON TO REFRESH TEAM EMBED" ,ctx)
    except:
        traceback.print_exc()
        await ephemeral_respond("Could not remove player..." ,ctx)
# ----------------------------------
# autotimestamp
# ----------------------------------
def convert_to_unix_timestamp(date_time_str):
    # Convert string to datetime object
    date_time_obj = datetime.datetime.strptime(date_time_str, '%m/%d/%Y %I:%M %p')

    # Set timezone to PDT
    timezone = pytz.timezone('America/Los_Angeles')
    date_time_obj = timezone.localize(date_time_obj)

    # Convert datetime object to Unix timestamp
    unix_timestamp = int(date_time_obj.timestamp())

    return unix_timestamp

# ----------------------------------
# war time command
# ----------------------------------
@bdo.child
@lightbulb.command("timetillwar", "How long until today's war")
@lightbulb.implements(lightbulb.SlashSubCommand)
async def timetillwar(ctx: lightbulb.SlashContext) -> None:
    try:
            # Get the current time
            current_time = datetime.datetime.now()

            # Set the target time to 7:45 PM
            target_time = current_time.replace(hour=19, minute=45, second=0, microsecond=0)

            # Calculate the time difference
            time_difference = target_time - current_time

            # Extract hours and minutes from the time difference
            hours, seconds = divmod(time_difference.seconds, 3600)
            minutes = seconds // 60
            await ctx.respond(f"Time remaining until war: **{hours} hours and {minutes} minutes.**",flags=hikari.MessageFlag.EPHEMERAL)
    except Exception:
        traceback.print_exc()
        await ephemeral_respond("Sorry, something went wrong...",ctx)

async def generate_rows(bot: lightbulb.BotApp):
    rows = []
    row1 = bot.rest.build_message_action_row()
    row1.add_interactive_button(hikari.ButtonStyle.SECONDARY, "mainball", label = "Mainball")
    row1.add_interactive_button(hikari.ButtonStyle.SECONDARY, "defence", label = "Defence")
    row1.add_interactive_button(hikari.ButtonStyle.SECONDARY, "flex", label = "Flex")
    rows.append(row1)
    row2 = bot.rest.build_message_action_row()
    row2.add_interactive_button(hikari.ButtonStyle.SECONDARY, "cannons", label = "Cannons")
    row2.add_interactive_button(hikari.ButtonStyle.SECONDARY, "tentative", label = "Tentative")
    row2.add_interactive_button(hikari.ButtonStyle.SECONDARY, "absent", label = "Absent")
    rows.append(row2)
    return rows
if not os.path.exists(str("config/kiwiconfig.json")):
        shutil.copy2("config/kiwiconfigdefault.json", "config/kiwiconfig.json")

        
# ----------------------------------
# Configs
# ----------------------------------
config = ""
def load_config():
    '''loads admin config file'''
    global config
    if not os.path.exists(str("config/kiwiconfig.json")):
        shutil.copy2("config/kiwiconfigdefault.json", "config/kiwiconfig.json")
    with open('config/kiwiconfig.json', 'r') as openfile:
        config = json.load(openfile)
        openfile.close()
load_config()
def get_admin_list() -> list:
    global config
    return config["AdminList"].replace(", ", "").replace(" ,", "").replace(" , ", "").split(",")

def savesignup(signups):
    f = open('config/signuplist.json', 'w')
    f.write(json.dumps(signups))
    f.close()

async def check_for_roles(ctx, role_ids):
    member = await bot.rest.fetch_member(ctx.guild_id, ctx.author.id)
    roles = member.role_ids
    for id in role_ids:
        if id in roles:
            return True
    return False

def getplayercount() -> int:
    return len(signups)
async def handle_responses(bot: lightbulb.BotApp, author: hikari.User, member, message: hikari.Message, ctx: lightbulb.SlashContext = None, autodelete: bool = False) -> None:
    """Watches for events, and handles responding to them."""
    with bot.stream(hikari.InteractionCreateEvent, 604800).filter(lambda e: (isinstance(e.interaction, hikari.ComponentInteraction) and e.interaction.message == message)) as stream:
        async for event in stream:
            cid = event.interaction.custom_id
            interactionmember = await bot.rest.fetch_member(ctx.guild_id, event.interaction.user.id)
            userid = str(event.interaction.user.id)
            if userid in signups:
                signups[userid]["role"] = cid
            else:
                signups[userid] = {"name": str(interactionmember.display_name), "role": cid}
            savesignup(signups)

            try:
                embed = generate_war_embed(ctx)
                await event.interaction.create_initial_response(hikari.ResponseType.MESSAGE_UPDATE, embed=embed)
            except Exception:
                traceback.print_exc()
            except hikari.NotFoundError:
                pass
    # after timer, remove buttons
    await message.edit(components=[])

def abbreviate_name(name: str) -> str:
    if len(name) <= 15:
        return name
    else:
        return name[:15] + "..."
    
def generate_war_embed(ctx):
    embed = hikari.Embed(title=ctx.options.embedtitle, colour=hikari.Colour(0x09ff00))
    mainballlist = []
    defencelist=[]
    flexlist = []
    cannonslist = []
    absentlist = []
    benchlist = []
    tentativelist = []
    global signups

    #Sort signups by earliest registration
    count = 0
    for id in signups:
        name = abbreviate_name(signups[id]['name'])
        if signups[id]["role"] == "absent":
            absentlist.append(name)
            continue
        if signups[id]["role"] == "bench":
            benchlist.append(name)
            continue

        if count >= ctx.options.playercap:
            benchlist.append(name)
        elif signups[id]["role"] == "tentative" and len(tentativelist) < ctx.options.defencecap:
            tentativelist.append(name)
        elif signups[id]["role"] == "mainball" and len(mainballlist) < ctx.options.mainballcap:
            mainballlist.append(name)
        elif signups[id]["role"] == "defence" and len(defencelist) < ctx.options.defencecap:
            defencelist.append(name)
        elif signups[id]["role"] == "flex" and len(flexlist) < ctx.options.flexcap:
            flexlist.append(name)
        elif signups[id]["role"] == "cannons" and len(cannonslist) < ctx.options.cannonscap:
            cannonslist.append(name)
        else:
            benchlist.append(name)
            
        count = count + 1



    mainballnames = "Empty"
    if len(mainballlist) != 0:
        mainballnames = ""
        for name in mainballlist:
            mainballnames = mainballnames + "**⚔️" + name + "**" + "\n"
    defencenames = "Empty"
    if len(defencelist) != 0:
        defencenames = ""
        for name in defencelist:
            defencenames = defencenames + "**🛡️" + name + "**" + "\n"
    cannonnames = "Empty"
    if len(cannonslist) != 0:
        cannonnames = ""
        for name in cannonslist:
            cannonnames = cannonnames + "**💣" + name + "**" + "\n"
    flexnames = "Empty"
    if len(flexlist) != 0:
        flexnames = ""
        for name in flexlist:
            flexnames = flexnames + "**🗡️" + name + "**" + "\n"
    tentnames = "Empty"
    if len(tentativelist) != 0:
        tentnames = ""
        for name in tentativelist:
            tentnames = tentnames + "**⚖️" + name + "**" + "\n"  
    absentnames = "Empty"
    if len(absentlist) != 0:
        absentnames = ""
        for name in absentlist:
            absentnames = absentnames + "**❌" + name + "**" + "\n"
    benchnames = "Empty"
    if len(benchlist) != 0:
        benchnames = ""
        for name in benchlist:
            benchnames = benchnames + "**🛑" + name + "**" + "\n"
    embed.description = "<t:" + str(convert_to_unix_timestamp(str(ctx.options.pdtmeetupdatetime))) + ":R>"
    embed.description = embed.description + "\n:busts_in_silhouette:**" + str(len(mainballlist) + len(flexlist) + len(defencelist) + len(cannonslist)) + "/" + str(ctx.options.playercap) +"**"
    embed.add_field("⚔️__Mainball__```" + str(len(mainballlist)) + "/" + str(ctx.options.mainballcap) + "```", mainballnames, inline=True)
    embed.add_field("🛡️__Defence__```" + str(len(defencelist)) + "/" + str(ctx.options.defencecap) + "```", defencenames, inline=True)
    embed.add_field("🗡️__Flex__```" + str(len(flexlist)) + "/" + str(ctx.options.flexcap) + "```", flexnames, inline=True)
    embed.add_field("💣__Cannons__```" + str(len(cannonslist)) + "/" + str(ctx.options.cannonscap) + "```", cannonnames, inline=True)
    if len(benchlist)>0:
        embed.add_field("🛑__Benched__```" + str(len(benchlist)) + "```", benchnames, inline=False)
    embed.add_field("⚖️__Tentative__```" + str(len(tentativelist)) + "```", tentnames, inline=False)
    embed.add_field("❌__Not Attending__```" + str(len(absentlist)) + "```", absentnames, inline=False)
    return embed
# ----------------------------------
# Reboot Command
# ----------------------------------
@bot.command()
@lightbulb.command("reboot", "Force reboot kiwi")
@lightbulb.implements(lightbulb.SlashCommand)
async def reboot(ctx: lightbulb.SlashContext) -> None:
    hasrole = await check_for_roles(ctx,[1152085844128178197,1120170416384790538])
    if not hasrole:
        await ephemeral_respond("You must have staff role to use this command", ctx)
        return
    await ctx.respond("Rebooting",flags=hikari.MessageFlag.EPHEMERAL)
    await bot.close()
    await asyncio.sleep(1)
    await quit(1)

# ----------------------------------
# Start Bot
# ----------------------------------
tasks.load(bot)
bot.run()
sys.exit()