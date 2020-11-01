import glob
import math
import os
import random
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

print("DemonBot v.01 Online!")

bot = commands.Bot(
    command_prefix=['o!', 'demon!'],
    intents=intents,
    case_insensitive=True
)


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

    '''Evaluates Input. Restricted to OblivionCreator only.'''
    
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


@bot.command(name='kick', aliases=['yeet'])
async def _kick(ctx, user=''):

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

    await ctx.guild.kick(user=user)
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

    tup = args
    banReason = ' '.join(tup)

    try:
        member = await bot.fetch_user(user)
    except:
        await ctx.send("That is not a valid Discord user!")
        return

    await ctx.guild.ban(user=member, reason=banReason)
    await ctx.send(f"User {member} has been banned for {banReason}.")


@bot.command(name='mute')
async def _mute(ctx, user):
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


@bot.command(name='announce', aliases=['a'])
async def _announce(ctx, channel: discord.TextChannel, title, *args):

    '''Sends an announcement to the specified channel.
    USAGE:
    o!announce/a "<TITLE>" <ANNOUNCEMENT CONTENT>

    For Example
    o!announce #general "Generic Announcement" This is a generic announcement!

    The announcement may not contain any quotes (" or ') or it will error out.

    '''

    await ctx.message.delete()



    if not ctx.message.author.guild_permissions.manage_messages:
        await ctx.send("You do not have permission to perform this action!")
        return

    anStr = ' '.join(args)

    mentionList = []

    print(mentionList)

    print(channel, title, *args)
    emA = discord.Embed(title=title,
                        description=anStr, color=0xff0000)

    await channel.send(embed=emA)

    pass

@_announce.error
async def _announce_error(ctx, args):
    await ctx.send("Unable to send announcement! Please check your formatting is correct. For more help, please do o!help announce")

bot.run(token)
