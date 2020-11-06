import glob
import math
import os
import random
from datetime import datetime

import discord
from discord import guild, File
from discord.ext import commands
import sqlite3
from sqlite3 import Error
from collections.abc import Sequence
import ast
from dataclasses import dataclass
import time
import json

from discord.ext.commands import has_permissions

file = open("token.txt")
token = file.read()

intents = discord.Intents.default()
intents.members = True

print("DemonBot v1.02 Online!")

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
        await ctx.send("You do not have permission to perform this action!")
        return

    if user == '':
        await ctx.send("You need to define who you want to warn!")
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

    await ctx.send(f"Successfully warned {getMember(ctx, user)} for {warnReason}.")

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
        await ctx.send("You do not have permission to perform this action!")
        return

    try:
        userID = ctx.message.mentions[0].id
        validUser = True
    except:
        if checkMember(ctx, user) is None:
            validUser = False
            await ctx.send("This user has left the server, or the user ID is invalid!")
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
    embedVar = discord.Embed(title=f"Warnings for user {userDisplay}",
                             description=f"{userDisplay} currently has {wC} warning{plural}", color=0xff0000)

    reasonCount = 0

    for i in warnFiles:
        reasonCount = reasonCount + 1
        jsonFile = open(i)
        data = json.load(jsonFile)
        reasonString = data['reason']
        print(reasonString)
        embedVar.add_field(name=f"Warning {reasonCount}:", value=reasonString[0:1023], inline=False)

    await ctx.send(embed=embedVar)


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
async def _kick(ctx, user='',  *args):
    '''Kicks a specified user.'''

    await ctx.message.delete()

    if not ctx.message.author.guild_permissions.kick_members:
        await ctx.send("You do not have permission to perform this action!")
        return

    if user == '':
        await ctx.send("You need to select a user to kick!")
        return

    try:
        user = ctx.message.mentions[0].id
    except:
        user = user
    try:
        user = await bot.fetch_user(user)
    except:
        await ctx.send("That is not a valid Discord user!")
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
    await ctx.send(f"User {user} has been kicked.")


@bot.command(name='ban', aliases=['banish'])
async def _ban(ctx, user='', *args):
    '''Bans a specified user.'''

    await ctx.message.delete()

    if not ctx.message.author.guild_permissions.ban_members:
        await ctx.send("You do not have permission to perform this action!")
        return

    if user == '':
        await ctx.send("You need to select a user to ban!")
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
        await ctx.send("That is not a valid Discord user!")
        return


    await ctx.guild.ban(user=member, reason=banReason)
    await cmdLogger(member=member, reason=banReason, func='Ban', activator=ctx.author)
    await ctx.send(f"User {member} has been banned for {banReason}.")


@bot.command(name='mute', aliases=['gag', 'silence', 'shutup'])
async def _mute(ctx, user, *args):
    '''Mutes a specified user.'''
    await ctx.message.delete()

    if not ctx.message.author.guild_permissions.manage_messages:
        await ctx.send("You do not have permission to perform this action!")
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
        await ctx.send("That is not a valid user!")
        return

    if not validUser:

        if not checkMember(ctx, user):
            ctx.send("This user has left the server!")
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

    addRole = discord.utils.get(member.guild.roles, name="muted")
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

    await ctx.send(f"User {member} has been muted!")


@bot.command(name='unmute', aliases=['free'])
async def unmute(ctx, user):
    '''Unmutes a muted user.'''

    if not ctx.message.author.guild_permissions.manage_messages:
        await ctx.send("You do not have permission to perform this action!")
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
        await ctx.send("That is not a valid user!")
        return

    if not validUser:

        if not checkMember(ctx, user):
            ctx.send("This user has left the server!")
            return
        else:
            validUser = True

    member = getMember(ctx, user)
    roles = []

    try:
        file, = glob.glob(f"mutes/{user}_*")
    except:
        await ctx.send(f"{member} is not muted!")
        return

    print(file)

    f = open(file)

    roles = f.read().splitlines()
    for r in roles:
        print(r)
        rI = int(r)
        rG = discord.utils.get(ctx.guild.roles, id=rI)
        print(rG)
        if rG:
            await member.add_roles(rG)

    silRole = discord.utils.get(member.guild.roles, name="muted")
    await member.remove_roles(silRole)

    f.close()

    await ctx.send(f"{member} has been unmuted.")

    for file in glob.glob(f"mutes/{member.id}_*"):
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
        await ctx.send("There was no warnings to remove!")
    else:
        plural = 's'
        if (waRe == 1): plural = ''
        await ctx.send(f"Successfully removed {waRe} warning{plural}!")


@bot.command(name='announce', aliases=['a'])
async def _announce(ctx, channel: discord.TextChannel, title, content):
    '''Sends an announcement to the specified channel.

    For Example
    o!announce #general "Generic Announcement" "This is a generic announcement!"

    Both the Title and Content fields have to be put in quotes, or it will not work!

    '''

    await ctx.message.delete()

    if not ctx.message.author.guild_permissions.manage_messages:
        await ctx.send("You do not have permission to perform this action!")
        return

    print(channel, title, content)
    emA = discord.Embed(title=title,
                        description=content, color=0xff0000)

    await channel.send(embed=emA)

    pass


@_announce.error
async def _announce_error(ctx, args):
    await ctx.send(
        "Unable to send announcement! Please check your formatting is correct. For more help, please do o!help announce")


## Mod Log Stuff ##

async def sendLog(embed, data):
    channel = bot.get_channel(770145741682638848)
    await channel.send(data, embed=embed)


@bot.event
async def on_member_join(member): # On Member Join - Shows how old their account is and warns if new account.
    data = f":inbox_tray: `{(datetime.now()).strftime('%Y-%m-%d %H:%M:%S')}` `[Member Join]`: {member} ({member.id}) {member.mention}"

    newM = ''

    print(member.created_at.day)

    if member.created_at.day < 7:
        newM = " :warning: New Account! "

    embedV = discord.Embed(title=f"{member.guild.member_count} Members", description=f"Account Created On: {member.created_at.strftime('%Y-%m-%d %H:%M:%S')}{newM}", color=0x00ff00)

    await sendLog(embedV, data)


@bot.event
async def on_member_remove(member): # On Member Leave - Tracks who leaves, shows how long they were in the server for.
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
    elif weeks >=4:
        memTime = f"{months} Month(s), {weeks} Week(s), {days} Day(s) and {hours} Hour(s)"
    elif weeks > 51:
        memTime = f"{months} Year(s) {weeks} Week(s), {days} Day(s) and {hours} Hour(s)"
    else:
        memTime = f"{weeks} Week(s), {days} Day(s), {hours} Hour(s) and {minutes} Minutes"

    embedV = discord.Embed(title=f"{member.guild.member_count} Members",
                           description=f"Member for {memTime}",
                           color=0xff0000)

    await sendLog(embedV, data)

async def cmdLogger(member, activator, func, reason):

    funcD = func

    if funcD == "Ban":
        funcD = "Bann"
        print("Hello!")

        print(func + funcD)

    embLog = discord.Embed(title=f"{func}", description=f"User {member} was {funcD.lower()}ed by {activator} for:\n{reason}", color=0xfd6a02)

    await sendLog(embed=embLog, data='')


@bot.event
async def on_ready():
    print("Bot Online!")


bot.run(token)
