import asyncio
import glob
import os
import threading

from disnake.ext import tasks
from datetime import datetime
from pathlib import Path
import random
import disnake
from disnake.ext import commands
import ast
import time
import json
import sqlite3

file = open("token.txt")
token = file.read()

intents = disnake.Intents.default()
intents.members = True
intents.message_content = True

print("DemonBot v1.03 Online!")

bot = commands.Bot(
    command_prefix=['o!', 'demon!'],
    intents=intents,
    case_insensitive=True
)


@bot.check
async def globally_block_dms(ctx):
    if ctx.guild is None:
        await ctx.author.send("You should do this in the server, you know.")
    return ctx.guild is not None


def checkMember(ctx, userID):
    if userID.isnumeric():
        member = ctx.message.guild.get_member(int(userID))
        print(member)
        return member
    else:
        return None


def getMember(ctx, userID):
    member = ctx.message.guild.get_member(int(userID))
    print(member)
    return member


@bot.command(name='warn')
async def _warn(ctx, user='', *args):
    await ctx.message.delete()

    ''' Warns the specified user for the reason provided.'''

    if not ctx.message.author.guild_permissions.manage_messages:
        await ctx.reply("You do not have permission to perform this action!")
        return

    if user == '':
        await ctx.reply("You need to define who you want to warn!")
        return

    try:
        user = ctx.message.mentions[0].id
    except:
        if checkMember(ctx, user) is None:
            await ctx.message.channel.send(
                "That is not a valid user! This user may have left the server or the user ID is invalid.")
            return

    tup = args
    warnReason = ' '.join(tup)

    await ctx.reply(f"Successfully warned {getMember(ctx, user)} for {warnReason}.")

    warnFile = f"warns/{user}_{int(time.time())}.json"

    warnTuple = {
        "user": user,
        "reason": warnReason
    }

    warnJSON = json.dumps(warnTuple)

    f = open(warnFile, "w")
    f.write(warnJSON)
    f.close()
    print(warnJSON)


@bot.command(name='checkwarns', aliases=['warncheck', 'checkwarn', 'warns', 'badtokens'])
async def _warnCheck(ctx, user):
    '''Views the warnings of a specified user.'''

    await ctx.message.delete()

    if not ctx.message.author.guild_permissions.manage_messages:
        await ctx.reply("You do not have permission to perform this action!")
        return

    try:
        userID = ctx.message.mentions[0].id
        validUser = True
    except:
        if checkMember(ctx, user) is None:
            validUser = False
            await ctx.reply("This user has left the server, or the user ID is invalid!")
        else:
            validUser = True
        userID = user

    wC = 0
    warnFiles = []

    for file in glob.glob(f"warns/{userID}_*"):
        print(file)
        wC = wC + 1
        warnFiles.append(file)

    if validUser:
        userDisplay = getMember(ctx, userID)
    else:
        userDisplay = f"{userID} (User has left the server.)"

    if wC == 1:
        plural = ''
    else:
        plural = 's'
    embedVar = disnake.Embed(title=f"Warnings for user {userDisplay}",
                             description=f"{userDisplay} currently has {wC} warning{plural}", color=0xff0000)

    reasonCount = 0

    for i in warnFiles:
        reasonCount = reasonCount + 1
        jsonFile = open(i)
        data = json.load(jsonFile)
        reasonString = data['reason']
        print(reasonString)
        embedVar.add_field(name=f"Warning {reasonCount}:", value=reasonString[0:1023], inline=False)

    await ctx.reply(embed=embedVar)


## EVAL COMMAND. ##


def insert_returns(body):
    # insert return stmt if the last expression is a expression statement
    if isinstance(body[-1], ast.Expr):
        body[-1] = ast.Return(body[-1].value)
        ast.fix_missing_locations(body[-1])

    # for if statements, we insert returns into the body and the orelse
    if isinstance(body[-1], ast.If):
        insert_returns(body[-1].body)
        insert_returns(body[-1].orelse)

    # for with blocks, again we insert returns into the body
    if isinstance(body[-1], ast.With):
        insert_returns(body[-1].body)


@bot.command(name='eval')
@commands.is_owner()
async def eval_fn(ctx, *, cmd):
    fn_name = "_eval_expr"

    cmd = cmd.strip("` ")

    # add a layer of indentation
    cmd = "\n".join(f"    {i}" for i in cmd.splitlines())

    # wrap in async def body
    body = f"async def {fn_name}():\n{cmd}"

    parsed = ast.parse(body)
    body = parsed.body[0].body

    insert_returns(body)

    env = {
        'bot': ctx.bot,
        'discord': discord,
        'commands': commands,
        'ctx': ctx,
        '__import__': __import__
    }
    exec(compile(parsed, filename="<ast>", mode="exec"), env)

    result = (await eval(f"{fn_name}()", env))


@bot.command(name='kick', aliases=['yeet'])
async def _kick(ctx, user='', *args):
    '''Kicks a specified user.'''

    await ctx.message.delete()

    if not ctx.message.author.guild_permissions.kick_members:
        await ctx.reply("You do not have permission to perform this action!")
        return

    if user == '':
        await ctx.reply("You need to select a user to kick!")
        return

    try:
        user = ctx.message.mentions[0].id
    except:
        user = user
    try:
        user = await bot.fetch_user(user)
    except:
        await ctx.reply("That is not a valid Discord user!")
        return

    reason = ''
    reasonT = ''

    try:
        for a in args:
            reasonT = ' '.join(args)
    except:
        reasonT = 'Invalid Syntax!'

    reason = f"{reasonT} [Kicked By {ctx.author} ({ctx.author.id}]"

    await cmdLogger(member=user, reason=reason, func='Kick', activator=ctx.author)

    await ctx.guild.kick(user=user, reason=reason)
    await ctx.reply(f"User {user} has been kicked.")


@bot.command(name='ban', aliases=['banish'])
async def _ban(ctx, user='', *args):
    '''Bans a specified user.'''

    await ctx.message.delete()

    if not ctx.message.author.guild_permissions.ban_members:
        await ctx.reply("You do not have permission to perform this action!")
        return

    if user == '':
        await ctx.reply("You need to select a user to ban!")
        return

    try:
        user = ctx.message.mentions[0].id
    except:
        pass

    banReason = ''

    try:
        for a in args:
            banReason = ' '.join(args)
    except:
        banReason = 'Invalid Syntax!'

    banReason = f"{banReason} [Banned by {ctx.author}]"

    try:
        member = await bot.fetch_user(user)
    except:
        await ctx.reply("That is not a valid Discord user!")
        return

    await ctx.guild.ban(user=member, reason=banReason)
    await cmdLogger(member=member, reason=banReason, func='Ban', activator=ctx.author)
    await ctx.reply(f"User {member} has been banned for {banReason}.")

    guild = ctx.guild
    purgeMsg = 0

    for c in guild.channels:
        purgeMsg = purgeMsg + len(await c.purge(limit=75, check=lambda x: (x.author.id == member.id)))

    await ctx.reply(f"Purged {purgeMsg} messages belonging to {member}.")


@bot.command(name='mute', aliases=['gag', 'silence', 'shutup'])
async def _mute(ctx, user, *args):
    '''Mutes a specified user.'''
    await ctx.message.delete()

    if not ctx.message.author.guild_permissions.manage_messages:
        await ctx.reply("You do not have permission to perform this action!")
        return

    validUser = False

    try:
        user = ctx.message.mentions[0].id
        validUser = True
    except:
        pass

    try:
        await bot.fetch_user(user)
    except:
        await ctx.reply("That is not a valid user!")
        return

    if not validUser:

        if not checkMember(ctx, user):
            ctx.reply("This user has left the server!")
            return
        else:
            validUser = True

    member = getMember(ctx, user)

    roleList = []

    for i in member.roles:
        if i.name != '@everyone':
            roleList.append(i)
            print(i)
            await member.remove_roles(i)

    addRole = disnake.utils.get(member.guild.roles, name="muted")
    await member.add_roles(addRole)

    for file in glob.glob(f"mutes/{member.id}_*"):
        os.remove(file)

    muteFile = f"mutes/{member.id}_{int(time.time())}.txt"

    f = open(muteFile, "w")
    for l in roleList:
        roleID = l.id
        f.write(str(roleID) + '\n')
    f.close()
    print("Muted Member!")

    print(roleList)

    await ctx.reply(f"User {member} has been muted!")


@bot.command(name='unmute', aliases=['free'])
async def unmute(ctx, user):
    '''Unmutes a muted user.'''

    if not ctx.message.author.guild_permissions.manage_messages:
        await ctx.reply("You do not have permission to perform this action!")
        return

    await ctx.message.delete()

    validUser = False

    try:
        user = ctx.message.mentions[0].id
        validUser = True
    except:
        pass

    try:
        await bot.fetch_user(user)
    except:
        await ctx.reply("That is not a valid user!")
        return

    if not validUser:

        if not checkMember(ctx, user):
            ctx.reply("This user has left the server!")
            return
        else:
            validUser = True

    member = getMember(ctx, user)
    roles = []

    try:
        file, = glob.glob(f"mutes/{user}_*")
    except:
        await ctx.reply(f"{member} is not muted!")
        return

    print(file)

    f = open(file)

    roles = f.read().splitlines()
    for r in roles:
        print(r)
        rI = int(r)
        rG = disnake.utils.get(ctx.guild.roles, id=rI)
        print(rG)
        if rG:
            await member.add_roles(rG)

    silRole = disnake.utils.get(member.guild.roles, name="muted")
    await member.remove_roles(silRole)

    f.close()

    await ctx.reply(f"{member} has been unmuted.")

    for file in glob.glob(f"mutes/{member.id}_*"):
        os.remove(file)


@bot.command(name='roleban', aliases=['toss', 'dungeon', 'torture'])
async def roleban(ctx, user):
    await _stripRoles(ctx, user)


async def _stripRoles(ctx, user=0):
    await ctx.message.delete()

    if not ctx.message.author.guild_permissions.manage_messages:
        await ctx.reply("You do not have permission to perform this action!")
        return

    validUser = False

    try:
        user = ctx.message.mentions[0].id
        validUser = True
    except:
        pass

    try:
        await bot.fetch_user(user)
    except:
        await ctx.reply("That is not a valid user!")
        return

    if not validUser:

        if not checkMember(ctx, user):
            ctx.reply("This user has left the server!")
            return
        else:
            validUser = True

    member = getMember(ctx, user)

    roleList = []

    for i in member.roles:
        if i.name != '@everyone':
            roleList.append(i)
            print(i)
            await member.remove_roles(i)

    addRole = disnake.utils.get(member.guild.roles, name="rolebanned")
    await member.add_roles(addRole)

    for file in glob.glob(f"rolebans/{member.id}_*"):
        os.remove(file)

    muteFile = f"rolebans/{member.id}_{int(time.time())}.txt"

    f = open(muteFile, "w")
    for l in roleList:
        roleID = l.id
        f.write(str(roleID) + '\n')
    f.close()
    print("Rolebanned Member!")
    print(roleList)
    await ctx.reply(f"User {member} has been rolebanned!")


@bot.command(name='unroleban', aliases=['untoss', 'excuse'])
async def _unStrip(ctx, user):
    '''Unrolebans specified user..'''

    if not ctx.message.author.guild_permissions.manage_messages:
        await ctx.reply("You do not have permission to perform this action!")
        return

    await ctx.message.delete()

    validUser = False

    try:
        user = ctx.message.mentions[0].id
        validUser = True
    except:
        pass

    try:
        await bot.fetch_user(user)
    except:
        await ctx.reply("That is not a valid user!")
        return

    if not validUser:

        if not checkMember(ctx, user):
            ctx.reply("This user has left the server!")
            return
        else:
            validUser = True

    member = getMember(ctx, user)
    roles = []

    try:
        file, = glob.glob(f"rolebans/{user}_*")
    except:
        await ctx.reply(f"{member} is not rolebanned!")
        return

    print(file)

    f = open(file)

    roles = f.read().splitlines()
    for r in roles:
        print(r)
        rI = int(r)
        rG = disnake.utils.get(ctx.guild.roles, id=rI)
        print(rG)
        if rG:
            await member.add_roles(rG)

    silRole = disnake.utils.get(member.guild.roles, name="rolebanned")
    await member.remove_roles(silRole)

    f.close()

    await ctx.reply(f"{member} has been unrolebanned.")

    for file in glob.glob(f"rolebans/{member.id}_*"):
        os.remove(file)


@bot.command(name='clearwarns', aliases=['forgive', 'pardon'])
async def _clearwarns(ctx, user):
    '''Removes all warnings for the specified user.'''

    await ctx.message.delete()

    try:
        user = ctx.message.mentions[0].id
    except:
        pass

    waRe = 0

    for file in glob.glob(f"warns/{user}_*"):
        os.remove(file)
        waRe = waRe + 1

    if waRe == 0:
        await ctx.reply("There was no warnings to remove!")
    else:
        plural = 's'
        if (waRe == 1): plural = ''
        await ctx.reply(f"Successfully removed {waRe} warning{plural}!")


@bot.command(name='announce', aliases=['a'])
async def _announce(ctx, channel: disnake.TextChannel, title, content):
    '''Sends an announcement to the specified channel.

    For Example
    o!announce #general "Generic Announcement" "This is a generic announcement!"

    Both the Title and Content fields have to be put in quotes, or it will not work!

    '''

    await ctx.message.delete()

    if not ctx.message.author.guild_permissions.manage_messages:
        await ctx.reply("You do not have permission to perform this action!")
        return

    print(channel, title, content)
    emA = disnake.Embed(title=title,
                        description=content, color=0xff0000)

    await channel.send(embed=emA)

    pass


@_announce.error
async def _announce_error(ctx, args):
    await ctx.reply(
        "Unable to send announcement! Please check your formatting is correct. For more help, please do o!help announce")


## Mod Log Stuff ##

async def sendLog(embed, data):
    channel = bot.get_channel(770145741682638848)
    await channel.send(data, embed=embed)


@bot.event
async def on_member_join(member):  # On Member Join - Shows how old their account is and warns if new account.

    banwords = ['h0nde', 'twitter.com/h0nde']

    if any(banword in member.name.lower() for banword in banwords):
        await member.guild.ban(member, reason='Autoban by Demon Bot. - Known Spambot/Raidbot/Scraper')

    data = f":inbox_tray: `{(datetime.now()).strftime('%Y-%m-%d %H:%M:%S')}` `[Member Join]`: {member} ({member.id}) {member.mention}"

    newM = ''

    print(member.created_at.day)

    if member.created_at.day > 7:
        newM = " :warning: New Account! "

    embedV = disnake.Embed(title=f"{member.guild.member_count} Members",
                           description=f"Account Created On: {member.created_at.strftime('%Y-%m-%d %H:%M:%S')}{newM}",
                           color=0x00ff00)

    await sendLog(embedV, data)


@bot.event
async def on_member_remove(member):  # On Member Leave - Tracks who leaves, shows how long they were in the server for.
    data = f":outbox_tray: `{(datetime.now()).strftime('%Y-%m-%d %H:%M:%S')}` `[Member Remove]`: {member} ({member.id}) <@{member.id}>"

    dur = datetime.now() - member.joined_at

    hours, remainder = divmod(int(dur.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)
    days, hours = divmod(hours, 24)
    weeks, days = divmod(days, 7)
    months, weeks = divmod(weeks, 4)
    years, months = divmod(months, 12)

    memTime = f"{minutes}m:{seconds}s"
    if weeks < 1:
        memTime = f"{days} Day(s), {hours} Hour(s), {minutes} Minute(s) and {seconds} Seconds"
    elif weeks >= 4:
        memTime = f"{months} Month(s), {weeks} Week(s), {days} Day(s) and {hours} Hour(s)"
    elif weeks > 51:
        memTime = f"{months} Year(s) {weeks} Week(s), {days} Day(s) and {hours} Hour(s)"
    else:
        memTime = f"{weeks} Week(s), {days} Day(s), {hours} Hour(s) and {minutes} Minutes"

    embedV = disnake.Embed(title=f"{member.guild.member_count} Members",
                           description=f"Member for {memTime}",
                           color=0xff0000)

    await sendLog(embedV, data)


async def cmdLogger(member, activator, func, reason):
    funcD = func

    if funcD == "Ban":
        funcD = "Bann"
        print("Hello!")

        print(func + funcD)

    embLog = disnake.Embed(title=f"{func}",
                           description=f"User {member} was {funcD.lower()}ed by {activator} for:\n{reason}",
                           color=0xfd6a02)

    await sendLog(embed=embLog, data='')


## DemonPoints! ##

database = 'dpoints.db'


def create_connection(db_file):
    conn = None
    try:

        file = Path(database)

        if file.is_file():
            conn = sqlite3.connect(db_file)
        else:
            print("Database does not exist! Generating new Database")
            conn = sqlite3.connect(db_file)
            cur = conn.cursor()
            sql = '''CREATE TABLE "pointDB" (
"ownerid"	INTEGER,
"points"	INTEGER,
"streak"	INTEGER
)'''
            cur.execute(sql)
            conn.commit()

        print(sqlite3.version)
    except sqlite3.Error as e:
        print("Connection Failed! - " + e)

    return conn


conn = create_connection(database)


@bot.event
async def on_message(message):
    dPoints = random.randint(5, 15)
    lucky = random.randint(1, 50)
    if lucky == 50:
        dPoints = dPoints * 2

    if message.author.bot:
        return

    author = message.author.id

    cur = conn.cursor()
    sql = '''SELECT * FROM pointDB where ownerid IS ?'''
    cur.execute(sql, [author])
    authorData = cur.fetchone()

    if authorData is None:
        ownerid = author
        streak = 9
        fPoints = dPoints * 10
        sql = '''INSERT INTO pointDB(ownerid, points, streak) VALUES(?,?,?)'''
        cur.execute(sql, [ownerid, fPoints, streak])
        conn.commit()
    else:
        ownerid, points, streak = authorData
        if points > 100000:
            dPoints = dPoints * 0.3
            streak = 1
        points = int(points + (dPoints * streak))
        if streak > 1:
            streak = streak - 1
        sql = '''UPDATE pointDB SET points = ? WHERE ownerid is ?'''
        cur.execute(sql, [points, ownerid])
        sql = '''UPDATE pointDB SET streak = ? WHERE ownerid is ?'''
        cur.execute(sql, [streak, ownerid])

        conn.commit()
    await bot.process_commands(message)


@tasks.loop(minutes=15)
async def resStreak():
    cur = conn.cursor()
    sql = '''SELECT * FROM pointDB'''
    cur.execute(sql)

    oldData = cur.fetchall()

    for ownerid, points, streak in oldData:
        sql = '''UPDATE pointDB SET streak = ? WHERE ownerid is ?'''
        if streak < 10:
            streak = 10
        cur.execute(sql, [streak, ownerid])

    conn.commit()


@bot.command()
async def leaderboard(ctx):
    cur = conn.cursor()
    sql = '''SELECT * FROM pointDB ORDER BY points DESC'''
    cur.execute(sql)

    rawvalue = cur.fetchall()

    embed = disnake.Embed(title="Showing Points Leaderboard", description="Top 10 Earners", color=0x007DFF)

    n = 0
    total = 0
    attempts = 0
    while total < 10:
        if attempts > 20:
            break
        n += 1
        attempts += 1
        print(n)
        temp = rawvalue[n - 1]
        user = ctx.guild.get_member(temp[0])
        if user is None:
            print("none")
        else:
            total += 1
            attempts = 0
            embed.add_field(name=f"Position {total}: {user}", value=f"{int(temp[1])} Points", inline=False)
    await ctx.reply("Here are the current rankings.", embed=embed)


def getPointData(user):
    cur = conn.cursor()

    sql = '''SELECT * FROM pointDB WHERE ownerid IS ?'''
    cur.execute(sql, [user])

    data = cur.fetchone()
    return data


@bot.command()
async def points(ctx):
    if ctx.message.mentions:
        user = ctx.message.mentions[0]
    else:
        user = ctx.author

    position = getPos(user)

    oID, points, streak = getPointData(user.id)

    embedP = disnake.Embed(title=f"Showing points for {user}",
                           description=f'{round(points)} Points (Position: {position})',
                           colour=0xFFFA00)
    await ctx.reply(f"Showing points for {ctx.guild.get_member(user) or user}", embed=embedP)


def getPos(user):
    cur = conn.cursor()

    sql = '''SELECT * FROM pointDB ORDER BY points DESC'''

    cur.execute(sql)

    value = cur.fetchall()

    pos = 0

    for i in value:
        pos += 1
        if i[0] == user.id:
            return pos


@bot.command()
async def gamble(ctx, pointsIn=''):
    if pointsIn.isnumeric():
        points = int(pointsIn)
    else:
        await ctx.reply("That is not a valid number of points to Gamble!")
        return

    user, currentpoints, streak = getPointData(ctx.author.id)

    if points > currentpoints:
        await ctx.reply("You do not have that many points to gamble!")
        return

    luck = random.randint(0, 100)

    if luck > 99:
        winnings = (points * 5) - points
        await ctx.reply(f":bank: ULTRA JACKPOT\nYOU WON: {winnings + points} Points!")
        modifyPoints(user, winnings)
        return
    if luck > 92:
        winnings = (points * 3) - points
        await ctx.reply(f":moneybag: MEGA JACKPOT\nYOU WON: {round(winnings + points)} Points!")
        modifyPoints(user, round(winnings))
        return
    if luck > 85:
        winnings = (points * random.uniform(1.5, 2.5)) - points
        await ctx.reply(f":coin: WIN\nYOU WON: {round(winnings + points)} Points!")
        modifyPoints(user, round(winnings))
        return
    if luck > 65:
        winnings = (points * random.uniform(1.01, 1.5)) - points
        await ctx.reply(f":coin: WIN\nYOU WON: {round(winnings + points)} Points!")
        modifyPoints(user, round(winnings))
        return
    if luck < 5:
        losing = points * 0.1
        winnings = 0 - (points - losing)
        await ctx.reply(f":poop: UNLUCKY\nYOU LOST: {round(winnings)} Points!")
        modifyPoints(user, round(winnings))
        return
    if luck < 2:
        winnings = 0 - points
        await ctx.reply(f":poop: UNLUCKY\nYou lost all your points!")
        modifyPoints(user, round(winnings))
        return
    else:
        losing = points * random.uniform(0.2, 0.9)
        winnings = round(0 - losing)
        await ctx.reply(f":roll_of_paper: LOSS\nYOU LOST: {winnings} Points!")
        modifyPoints(user, round(winnings))
        return


steal_active = False
steal_value = 0
steal_users = []
steal_message = None
steal_author = None
steal_components = []
steal_boost = []
steal_time = 0


@commands.is_owner()
@commands.cooldown(1, 3600, commands.BucketType.guild)
@bot.command()
async def steal(ctx):
    global steal_active, steal_value, steal_users, steal_message, steal_components, steal_author, steal_boost, steal_time
    steal_value = random.randint(25, 35)
    steal_author = ctx.author
    steal_components.append(disnake.ui.Button(label='💰 Join Heist', custom_id='join', style=1))
    steal_components.append(disnake.ui.Button(label='💵 Boost Heist', custom_id='fund', style=3))

    steal_time = time.time() + 300

    emb = disnake.Embed(title="A Heist for the Ages!",
                        description=f"{ctx.author.name} has started planning a heist!\nCurrently the heist has a **{steal_value}%** chance of success and a **0%** Bonus Modifier.\nThe heist takes place <t:{int(steal_time)}:R>")
    emb.add_field(name="Heist Members", value=f"{ctx.author.name} (0% Boost)")
    steal_message = await ctx.reply(embed=emb, components=steal_components)
    steal_active = True
    steal_users.append(ctx.author)
    steal_boost.append(0.0)

    await asyncio.sleep(3)
    return
    steal_components = []
    steal_components.append(disnake.ui.Button(label='💰 Join Heist', custom_id='join', style=1, disabled=True))
    steal_components.append(disnake.ui.Button(label='💵 Boost Heist', custom_id='fund', style=3, disabled=True))
    await update_steal(title='Heist Complete!')

    roll = random.randint(1, 100)
    heist_success = "Successful!"
    if roll > steal_value:
        heist_success = "Failed!"

    success_msg = [
        "You all manage to sneak into the Amazon Warehouse undetected, and make out with several boxes of loot!",
        "After a raid on the  TLDG PayPal account, you all make out with an abundance of points!",
        ""
    ]

    mixed_msg = [

    ]

    failed_msg = [

    ]

    # emb2 = disnake.Embed(title=f"Heist {heist_success}")

    # await steal_message.reply()


@bot.event
async def on_button_click(interaction):
    global steal_active, steal_value, steal_users, steal_message, steal_data
    if interaction.data.custom_id == 'join':
        if interaction.author in steal_users:
            await interaction.response.send_message("You've already joined this heist!", ephemeral=True)
            return
        steal_users.append(interaction.author)
        steal_boost.append(0.0)
        if steal_value > 90:
            steal_value = 90
            additional_success = 0
            await interaction.response.send_message(
                f"You've joined the heist!", ephemeral=True)
        else:
            additional_success = random.randint(3, 8)
            steal_value += additional_success
            if (steal_value - 90) > 0:
                additional_success -= steal_value - 90
                steal_value = 90
            await interaction.response.send_message(
                f"You've joined the heist and boosted its success chances by {additional_success}%!", ephemeral=True)
    if interaction.data.custom_id == 'fund':
        points = getPointData(interaction.author.id)[1]
        if points < 500:
            await interaction.response.send_message("You need at least 500 points to boost a heist!", ephemeral=True)
            return
        await interaction.response.send_message(
            "You spend 500 Points equipping the crew, and boost the total heist income by 5%!", ephemeral=True)
        steal_boost[steal_users.index(interaction.author)] += 0.05
        print(steal_boost)
    await update_steal()


async def update_steal(title=None, description=None):
    global steal_active, steal_value, steal_users, steal_message, steal_components, steal_author, steal_boost, steal_time

    total_bonus = 0
    for i in steal_boost:
        total_bonus += i * 100
    emb = disnake.Embed(title=title or "A Heist for the Ages!",
                        description=description or f"{steal_author.name} has started planning a heist!\nCurrently the heist has a **{steal_value}%** chance of success and a **{int(total_bonus)}%** Bonus Modifier.")
    temp = ""
    for i in steal_users:
        temp = f"{temp}{i.name} ({int(steal_boost[steal_users.index(i)] * 100)}% Boost)\n"
    emb.add_field(name="Heist Members", value=f"{temp}")
    await steal_message.edit(embed=emb, components=steal_components)


def remove_values_from_list(the_list, val):
    return [value for value in the_list if value != val]


def modifyPoints(user, points):
    user, oldPoints, streak = getPointData(user)

    newPoints = points + oldPoints

    sql = '''UPDATE pointDB SET points = ? WHERE ownerid is ?'''
    cur = conn.cursor()
    cur.execute(sql, [newPoints, user])
    conn.commit()


@bot.command()
async def defend(ctx):
    global currentlyDefending

    if ctx.author.id in currentlyDefending:
        await ctx.reply("Successfully defended your points from the attacker!")
        currentlyDefending = remove_values_from_list(currentlyDefending, ctx.author.id)
    else:
        await ctx.reply("You are not currently being stolen from!")
    return


raffleEntries = []
raffleOngoing = False


async def job():
    global raffleEntries
    global raffleOngoing

    channel = bot.get_channel(765310903871733783)
    await channel.send("The Daily Raffle is starting! The raffle will end in 6 hours.\n"
                       "Each Raffle entry costs 1000 Points. You may buy up to 100 entries to any given raffle.\n"
                       "To enter, do o!raffle <Number of Entries>")

    raffleEntries = []
    raffleOngoing = True

    await asyncio.sleep(21600)

    listlen = len(raffleEntries)

    if listlen == 0:
        await channel.send("There were no entries in the raffle!")
        return

    validWinner = False
    iterations = 0

    while not validWinner:
        winner = random.randint(0, listlen - 1)
        if winner != 312717190128467969 or iterations > 100:
            validWinner = True
        iterations += 1
    winnerID = raffleEntries[winner]

    await channel.send(
        f"Congratulations to <@{winnerID}> on winning the daily raffle!\nThey have won {listlen * 1000} points!")
    modifyPoints(winnerID, (listlen * 1000))

    raffleOngoing = False
    raffleEntries = []


@bot.command()
async def raffle(ctx, entries=''):
    '''o!raffle <entries> - Each entry costs 1000 points. You can purchase up to 100 entries, and can only enter once!'''

    global raffleEntries
    global raffleOngoing

    for i in raffleEntries:
        if i == ctx.author.id:
            await ctx.reply("You are already entered in the raffle!")
            return

    if not raffleOngoing:
        await ctx.reply("There is not an ongoing raffle!")
        return

    if not entries.isnumeric():
        await ctx.reply("You need to define how many entries you want to buy!")
        return

    pointData = getPointData(ctx.author.id)

    id, points, streak = pointData

    entryNo = int(entries)

    if entryNo > 100:
        entryNo = 100

    if (entryNo * 1000) > points:
        await ctx.reply(
            "You do not have enough points to buy that many entries!\nRemember, each entry costs 1000 Points!")
        return

    for i in range(entryNo):
        raffleEntries.append(ctx.author.id)

    modifyPoints(ctx.author.id, 0 - (entryNo * 1000))

    await ctx.reply(f"You have successfully bought {entryNo} entries to the raffle!")


@bot.command()
async def send(ctx, mention, points):
    if ctx.message.mentions:
        uID = ctx.message.mentions[0].id
    else:
        uID = bot.get_user(int(mention))

    if uID == None:
        await ctx.reply("That is not a valid user to send points to!")
        return

    if not points.isnumeric():
        await ctx.reply("That is not a valid amount of points to send!")
        return

    points = int(points)

    senderID, senderPo, senderSt = getPointData(ctx.author.id)
    recID, recPo, recSt = getPointData(uID)

    if recID == None:
        await ctx.reply(
            "I do not recognise that user! If they are new, they will need to send a message before they can receive any points!")
        return

    if points > senderPo:
        await ctx.reply("You do not have that many points to send!")
        return

    modifyPoints(ctx.author.id, (0 - points))
    modifyPoints(uID, points)

    await ctx.reply(f"Successfully sent {points} Points to {bot.get_user(uID).mention}!")


@bot.command()
@commands.is_owner()
async def addpoints(ctx, points):
    if points.isnumeric():
        points = int(points)
        modifyPoints(ctx.author.id, points)
        await ctx.reply(f"You gave yourself {points} Points!")
        return
    await ctx.reply("Not a valid number of points to add!")


@bot.command()
@commands.is_owner()
async def removepoints(ctx, points):
    if points.isnumeric():
        points = int(points)
        modifyPoints(ctx.author.id, 0 - points)
        await ctx.reply(f"You removed {points} Points from yourself!")
        return
    await ctx.reply("Not a valid number of points to remove!")


@bot.command()
async def forceRaffle(ctx):
    if ctx.author.id == 110399543039774720:
        await job()


@tasks.loop(seconds=60)
async def startRaffle():
    t = datetime.now()
    c_t = t.strftime("%H:%M")
    if c_t == "00:00":
        await job()


@bot.event
async def on_ready():
    print("Bot Online!")
    resStreak.start()
    startRaffle.start()


bot.run(token)
