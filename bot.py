import discord
from discord import app_commands
from discord.ext import commands
import random
import os
import json
import requests
import humanfriendly
from discord import member
from datetime import timedelta
from discord import utils, Interaction
from discord.ui import Select, View
import asyncio

TOKEN = 'EXPUNGED'

INVITE = 'REDACTED'

bot = commands.Bot(command_prefix='?', intents=discord.Intents.default().all())

GUILD_ID = 1045457143865823295

@bot.event
async def on_ready():
    print('Bot is ready!')
    try:
        synced = await bot.tree.sync()
        print(f'Synced {len(synced)} command(s)!')
    except Exception as e:
        print(e)

@bot.command()
async def sync(ctx):
    await bot.tree.sync()
    print('Synced!')
    await ctx.send('Synced!')
    return

class ticket_launcher(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)
    
    @discord.ui.button(label='Create a ticket.', style=discord.ButtonStyle.blurple, custom_id='ticket_button')
    async def ticket(self, interaction: discord.Interaction, button: discord.ui.button):
        ticket = utils.get(interaction.guild.text_channels, name=f'ticket-{interaction.user.name}-{interaction.user.discriminator}')
        if ticket is not None: await interaction.response.send_message(f'YOu already have a ticket {ticket.mention}!', ephemeral=True)
        else:
            overwrites = {
                interaction.guild.default_role: discord.PermissionOverwrite(view_channel = False),
                interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True, embed_links=True),
                interaction.guild.me: discord.PermissionOverwrite(view_channel = True, send_messages = True, read_message_history=True)
            }
            channel = await interaction.guild.create_text_channel(name=f'ticket-{interaction.user.name}-{interaction.user.discriminator}', overwrites=overwrites, reason=f'Ticket for {interaction.user}')
            await channel.send(f'{interaction.user.mention} has created a ticket!', view=main())
            await interaction.response.send_message('Created the ticket.', ephemeral=True)

class main(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)
    
    @discord.ui.button(label='Close Ticket', style=discord.ButtonStyle.red, custom_id='close')
    async def close(self, interaction: discord.Interaction, button):
        embed = discord.Embed(title='Are you sure you want to close this ticket?', color=discord.Colour.blurple())
        await interaction.response.send_message(embed=embed, ephemeral=True, view=confirm())

class confirm(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)

    @discord.ui.button(label='Close Ticket', style=discord.ButtonStyle.red, custom_id='close')
    async def confirm_button(self, interaction: discord.Interaction, button):
        try: await interaction.channel.delete()
        except: await interaction.response.send_message('Channel deletion failed! Make sure I have "administrator" or "manage_channels" permissions!', ephemeral=True)

@bot.tree.command(name='test')
async def test(interaction: discord.Interaction):
    await interaction.response.send_message(f'Hey {interaction.user.mention}!', ephemeral=True)

@bot.tree.command(name='say')
@app_commands.describe(arg = 'What should the bot say?')
async def say(interaction: discord.Interaction, arg: str):
    await interaction.response.send_message(f'{arg}', ephemeral=True)

@bot.tree.command(name="guessthenumber", description="Guess the number",)
async def guessthenumber(interaction: discord.Interaction,):
    await interaction.response.send_message("Please guess a number from **1-100**, you have **5** guesses.")
    guesses = 0
    num = random.randint(1, 100)
    while True:
        msg = await bot.wait_for('message',check=lambda m:m.author == interaction.user and m.channel == interaction.channel and m.content.isdigit())
        num_ = int(msg.content)
        print(num)
        if guesses>5:
            await msg.reply(":x: No more attempts left")
            break
        
        guesses+=1
        
        if num!=num_:
            await msg.reply(f"Incorrect! The number that I chose is {'higher :chart_with_upwards_trend: ' if num_<num else 'lower :chart_with_downwards_trend: '}")
        else:
            await msg.reply(f"Correct! The number that I chose was {num} ✅")
            break



@bot.tree.command(name='mute', description='Mutes a user')
@app_commands.describe(member='Select a user to mute.', reason='Set the reason to why the mute happened.', duration='Set the duration of a mute.')
async def _mute(interaction: discord.Interaction, member: discord.Member, duration: str, reason: str,):
    if interaction.user.guild_permissions.mute_members == True:
        originaltime = duration
        time = int(humanfriendly.parse_timespan(duration))
        await member.timeout(discord.utils.utcnow()+timedelta(seconds = time))
        embed = discord.Embed(
            title=f"{member} Muted",
            description=f"{member} Was Muted By {interaction.user}",
            color=discord.Color.green()
        )
        embed.add_field(name="Reason", value=f"{reason}", inline=True)
        await interaction.response.send_message(f"{member.mention}", embed=embed)
    else:
        embed1 = discord.Embed(
            description="You Dont Have Permissions To Execute This Command",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed1, ephemeral=True)
        channel = utils.get(interaction.guild.channels, name='logs')
        await channel.send(f'User `{interaction.user}` warned `{member}` for `{reason}`.')

@bot.event
async def on_application_command_error(interaction: discord.Interaction, error):
    error = getattr(error, "original", error)
    if str(error) == "403 Forbidden (error code: 50013): Missing Permissions" or str(error) == "403 Forbidden (error code: 50001): Missing Access":
        embed = discord.Embed(
            description = f"Unable to execute command, since i dont have permissions to do it.",
            colour = 0xF04A47
        )
        await interaction.send(embed=embed, ephemeral = True)

@bot.tree.command(name='ban', description='Ban a user from the guild.')
@app_commands.describe(member='Select a member to ban from the guild.', reason='Select a reason to why you banned the member')
async def _ban(interaction: discord.Interaction, member: discord.Member, reason: str,):
    if interaction.user.guild_permissions.ban_members == False:
        await interaction.response.send_message('Sorry, you do not have permissions to use this command.')
    if reason==None:
        await interaction.response.send_message('Please select a reason to ban the member.')
    else:
        if interaction.user.guild_permissions.ban_members==True:
            await member.ban()
            await interaction.response.send_message(f'{member} has been banned successfully for {reason}.')
        else:
            embed = discord.Embed(
                description="You Dont Have Permissions to Execute This Command!",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed)
            channel = utils.get(interaction.guild.channels, name='logs')
            await channel.send(f'User `{interaction.user}` warned `{member}` for `{reason}`.')

@bot.tree.command(name='kick', description='Kick a user from the guild.')
@app_commands.describe(member='Select a member to kick from the guild.', reason='Select a reason to why you kicked the member.')
async def _kick(interaction: discord.Interaction, member: discord.Member, reason: str):
    if interaction.user.guild_permissions.kick_members==False:
        embed = discord.Embed(description='You do not have permissions to use this command, please refrain from using commands that you are not allowed to use.',
        color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed)
    if reason==None:
        await interaction.response.send_message('You need to specify a reason!', ephemeral=True)
    else:
        await member.kick()
        await interaction.response.send_message('Kicked {} for {} successfully.'.format(member, reason))
        channel = utils.get(interaction.guild.channels, name='logs')
        await channel.send(f'User `{interaction.user}` warned `{member}` for `{reason}`.')

@bot.tree.command(name='clear', description='Purges the selected amount.')
async def _clear(interaction: discord.Interaction, amount: int):
    if interaction.user.guild_permissions.manage_messages==False:
        await interaction.response.send_message('You do not have permissions to use this **epic** command.', ephemeral=True)
    else:
        await interaction.channel.purge(limit=amount)
        await interaction.response.send_message('Cleared {} messages succesfully.'.format(amount), ephemeral=True)

@bot.tree.command(name='ticket', description='Launches the ticket system.')
async def ticketing(interaction: discord.Interaction):
    if interaction.user.guild_permissions.embed_links:
        embed = discord.Embed(title='Support Ticket', color=discord.Color.blue())
        await interaction.channel.send(embed=embed, view=ticket_launcher())
        await interaction.response.send_message('System launched!', ephemeral=True)
    else:
        interaction.response.send_message('You are not allowed to launch the ticket system.', ephemeral=True)

@bot.tree.command(name='close', description='Closes the current ticket')
async def close(interaction: discord.Interaction):
    if 'ticket-' in interaction.channel.name:
        embed = discord.Embed(title='Are you sure you want to close this ticket?', color=discord.Color.blurple())
        await interaction.response.send_message(embed=embed, view=confirm(), ephemeral=True)
    else: await interaction.response.send_message('This is not a ticket!', ephemeral=True)

@bot.command()
async def verify5e65T(ctx):
    verifyrole = discord.utils.get(ctx.guild.roles, name='Verified')
    unverifyrole = discord.utils.get(ctx.guild.roles, name='Unverified')
    await ctx.author.add_roles(verifyrole)
    await ctx.channel.purge(limit = 1)
    await ctx.author.send("You are now verified.")
    await ctx.author.remove_roles(unverifyrole)

@bot.event
async def on_member_join(member):
    role = discord.utils.get(member.guild.roles, name='Unverified')
    await member.add_roles(role)
    if role==None:
        print('Ignoring...')

@bot.tree.command(name='launchmenus', description='Launch the menu system')
async def _launchmenus(interaction: discord.Interaction):
    select = Select(options=[
        discord.SelectOption(label='Python', emoji='<:python:1046813438145466378>', value='0'),
        discord.SelectOption(label='C++', emoji='<:csharp:1046813393497100431>', value='1'),
        discord.SelectOption(label='C#', emoji='<:cplusplus:1046813421124984973>', value='2')
    ])
    view = View()
    view.add_item(select)
    
    async def callback(interaction: discord.Interaction):
        pythonrole = utils.get(interaction.guild.roles, name='Python')
        cplusplus = utils.get(interaction.guild.roles, name='C++')
        csharp = utils.get(interaction.guild.roles, name='C#')
        if select.values[0] == '0':
            await interaction.user.add_roles(pythonrole)
            await interaction.response.send_message('Added the Python role to you.', ephemeral=True)
        if select.values[0] == '1':
            await interaction.user.add_roles(cplusplus)
            await interaction.response.send_message('Added the C++ role to you.', ephemeral=True)
        if select.values[0] == '2':
            await interaction.user.add_roles(csharp)
            await interaction.response.send_message('Added the C# role to you.', ephemeral=True)

    select.callback = callback

    embed = discord.Embed(description='What is **YOUR** coding language?', color=discord.Color.dark_magenta())
    await interaction.response.send_message(embed=embed, view=view)

@bot.tree.command(name='warn',description='Warn a user')
@app_commands.describe(member='Select a member you want to warn.', reason='Why do you want to warn the member?')
async def _warn(interaction: discord.Interaction, member: discord.Member, reason: str):
    if interaction.user.guild_permissions.kick_members==False:
        await interaction.response.send_message('You do not have any permissions so just STOP!', ephemeral=True)
    embed = discord.Embed(title='Warned {} for {}'.format(member, reason), color=discord.Color.random())
    await interaction.response.send_message(embed=embed, ephemeral=True)
    channel = utils.get(interaction.guild.channels, name='logs')
    await channel.send(f'User `{interaction.user}` warned `{member}` for `{reason}`.')

@bot.tree.command(name='clearlogs', description='Clear the mod logs.')
async def _clearlogs(interaction: discord.Interaction):
    if interaction.user.guild_permissions.administrator==False:
        await interaction.response.send_message('You require {} permissions to execute this command.'.format(interaction.user.guild_permissions.administrator), ephemeral=True)
    else:
        channel = utils.get(interaction.guild.channels, name='logs')
        await channel.purge(limit=999)
        await interaction.response.send_message('Cleared the logs.', ephemeral=True)

@bot.tree.command(name='announce', description='Announce something.')
@app_commands.describe(announcement='Announce something here.')
async def _announce(interaction: discord.Interaction, announcement: str):
    if interaction.user.guild_permissions.administrator==False:
        await interaction.response.send_message('You cannot use this bla bla bla...', ephemeral=True)
    else:
        channel = utils.get(interaction.guild.channels, name='announcements')
        await channel.send(announcement)
        await interaction.response.send_message('Sent the announcement.', ephemeral=True)

@bot.tree.command(name='setup', description='If you are too lazy, use this command. This will set up an server automatically.')
async def _setup(interaction: discord.Interaction):
    if interaction.user.guild_permissions.administrator==False:
        await interaction.response.send_message('You cannot use this command as you are missing the admin permissions so yeaa.', ephemeral=True)
    else:
        await interaction.response.send_message('Setting up...')
        await interaction.guild.create_role(name='Staff Team', color=discord.Color.random())
        await interaction.guild.create_role(name='Verified', color=discord.Color.blue())
        await interaction.guild.create_role(name='Unverified', color=discord.Color.dark_blue())
        await interaction.guild.create_role(name='Poll Permissions', color=discord.Color.red())
        staffrole = utils.get(interaction.guild.roles, name='Staff Team')
        verifiedRole = utils.get(interaction.guild.roles, name='Verified')
        unverifiedRole = utils.get(interaction.guild.roles, name='Unverified')
        pollperms = utils.get(interaction.guild.roles, name='Poll Permissions')
        staffoverwrites = {
            staffrole: discord.PermissionOverwrite(read_messages=True, send_messages=True, embed_links=True, attach_files=True),
            unverifiedRole: discord.PermissionOverwrite(read_messages=False),
            verifiedRole: discord.PermissionOverwrite(read_messages=False),
            pollperms: discord.PermissionOverwrite(read_messages=False)
        }
        verifyChannel = {
            staffrole: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            unverifiedRole: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            verifiedRole: discord.PermissionOverwrite(read_messages=False),
            pollperms: discord.PermissionOverwrite(read_messages=True)
        }
        general = {
            unverifiedRole: discord.PermissionOverwrite(read_messages=False),
            verifiedRole: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        important = {
            staffrole: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            verifiedRole: discord.PermissionOverwrite(read_messages=True, send_messages=False),
            unverifiedRole: discord.PermissionOverwrite(read_messages=True, send_messages=False)
        }
        specialchannel = {
            staffrole: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            verifiedRole: discord.PermissionOverwrite(read_messages=True, send_messages=False),
            unverifiedRole: discord.PermissionOverwrite(read_messages=True, send_messages=False)
        }
        memes = {
            verifiedRole: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True, embed_links=True),
            unverifiedRole: discord.PermissionOverwrite(read_messages=False)
        }
        owner = {
            verifiedRole: discord.PermissionOverwrite(read_messages=False),
            unverifiedRole: discord.PermissionOverwrite(read_messages=False),
            staffrole: discord.PermissionOverwrite(read_messages=False)
        }
        await interaction.guild.create_category(name='Important')
        await interaction.guild.create_category(name='General')
        await interaction.guild.create_category(name='Verification Process')
        await interaction.guild.create_category(name='Support')
        await interaction.guild.create_category(name='Staff')
        importantcategory = utils.get(interaction.guild.categories, name='Important')
        generalcategory = utils.get(interaction.guild.categories, name='General')
        verificationprocess = utils.get(interaction.guild.categories, name='Verification Process')
        supportcategory = utils.get(interaction.guild.categories, name='Support')
        staffcategorys = utils.get(interaction.guild.categories, name='Staff')
        await interaction.guild.create_text_channel(name='announcements', overwrites=important, category=importantcategory)
        await interaction.guild.create_text_channel(name='rules', overwrites=important, category=importantcategory)
        await interaction.guild.create_text_channel(name='suggestions', overwrites=specialchannel, category=importantcategory)
        await interaction.guild.create_text_channel(name='polls', overwrites=specialchannel, category=importantcategory)
        await interaction.guild.create_text_channel(name='staff-chat', overwrites=staffoverwrites, category=staffcategorys)
        await interaction.guild.create_text_channel(name='tickets', overwrites=specialchannel, category=supportcategory)
        await interaction.guild.create_text_channel(name='verify', overwrites=verifyChannel, category=verificationprocess)
        await interaction.guild.create_text_channel(name='general', overwrites=general, category=generalcategory)
        await interaction.guild.create_text_channel(name='bot-commands', overwrites=general, category=generalcategory)
        await interaction.guild.create_text_channel(name='memes', overwrites=memes, category=generalcategory)
        await interaction.guild.create_text_channel(name='media', overwrites=memes, category=generalcategory)
        await interaction.guild.create_text_channel(name='logs', overwrites=owner, category=staffcategorys)
        ruleschannel = utils.get(interaction.guild.channels, name='rules')
        await ruleschannel.send('''
    1. You are allowed to swear to a certain point, just use your brain.
    2. Follow all discord TOS and guidelines! https://discord.com/terms https://discord.com/guidelines
    3. Do not dare someone to do suicide or any close to that, that will result in an INSTANT ban.
    4. Do not brieb any of our admins.
    5. If you feel good enough to take a challenge upon yourself, then figure out where the source code is. If you find the source code you will be rewarded an special role of your choice.
    6. If you feel the bot is suitable for your server, then please execute ?invite in #bot-commands.
    7. You are required to be over 13 years old or older to be on this discord server.
    8. The bot coder, and some of our admins will always be available for python help, but not always during school. Only during weekend.
    9. If you need help please open an ticket with ?ticket.
    10. Have fun!''')
        announcementschannel = utils.get(interaction.guild.channels, name='announcements')
        await announcementschannel.send('Post any announcement here using /announce.')
        await interaction.response.send_message('Delete the standard categories that are created when creating a server now.')

@bot.tree.command(name='slowmode', description='Set the slowmode of a channel.')
@app_commands.describe(time='Select how much the slowmode should be.')
async def _slowmode(interaction: discord.Interaction, time: int):
    if interaction.user.guild_permissions.manage_channels==False:
        await interaction.response.send_message('You do not have the required permissions to use this command.', ephemeral=True)
    else:
        if time==0:
            await interaction.response.send_message('Reset the slowmode time back to 0 automatically.', ephemeral=True)
            await interaction.channel.edit(slowmode_delay=0)
            loggingchannel = utils.get(interaction.guild.channels, name='logs')
            await loggingchannel.send('User {} set the slowmode time to {} in {}'.format(interaction.user, time, interaction.channel))
        else:
            await interaction.channel.edit(slowmode_delay=time)
            await interaction.response.send_message('Set the slowmode to {} in {}.'.format(time, interaction.channel), ephemeral=True)
            loggingchannel = utils.get(interaction.guild.channels, name='logs')
            await loggingchannel.send('User {} set the slowmode time to {} in {}'.format(interaction.user, time, interaction.channel))

@bot.tree.command(name='reminder', description='Sets a reminder for you.')
@app_commands.describe(reminder='What do you wanna be reminded off?', time='When should you be reminded?')
async def _reminder(interaction: discord.Interaction, reminder: str, time: str):
    def convert(time):
        pos = ['s', 'm', 'h', 'd']

        time_dict = {'s': 1, 'm': 60, 'h': 3600, 'd': 3600*24}

        unit = time[-1]

        if unit not in pos:
            return -1
        try:
            val = int(time[:-1])
        except:
            return -2
        
        return val * time_dict[unit]
    
    converted_time = convert(time)

    if converted_time == -1:
        await interaction.response.send_message('You did not answer the time.', ephemeral=True)
        return
    
    if converted_time == -2:
        await interaction.response.send_message('The time must be a number!', ephemeral=True)
        return
    
    await interaction.response.send_message('Started reminder for **{}** and I will remind you in **{}**.'.format(reminder, time))

    await asyncio.sleep(converted_time)
    await interaction.followup.send('{} reminded you for **{}**.'.format(interaction.user.mention, reminder))

bot.run(TOKEN)
