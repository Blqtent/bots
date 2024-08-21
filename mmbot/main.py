fee = 0.1 # 1%
your_discord_user_id = 1210386345445556225
bot_token = "MTI2NTE0NzgzMzE5MTc1OTkyMg.Gcor_y.8Hytnzw3D8W5zZFsSHPezxRJBkRrdkLrQsvQ0g"
ticket_channel = '1274934799320088601'
dispute_channel = '1274934799320088601'
logsid = '1275295961412796467'
api_key = "c81588d3df09465bb5b9e29b148c0fad"
VOUCH_CHANNEL_ID = 1275231077425877103

deals = {}
dis = {}
import asyncio
import random
import string
import time
import discord
from discord.ext import commands
from discord import Embed
import json
import requests
import blockcypher
from pycoingecko import CoinGeckoAPI
import urllib3
import datetime
import os
import aiofiles
import re
confirmed = None
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
endstage = None
cg = CoinGeckoAPI()



TICKETS_FILE = 'tickets.json'
TICKET_CONFIG_FILE = 'ticket_config.json'

def load_tickets():
    try:
        with open(TICKETS_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_tickets(tickets):
    with open(TICKETS_FILE, 'w') as f:
        json.dump(tickets, f)

def load_ticket_config():
    try:
        with open(TICKET_CONFIG_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_ticket_config(config):
    with open(TICKET_CONFIG_FILE, 'w') as f:
        json.dump(config, f)

async def clear():
    mgs = []
    number = 1 
    async for x in bot.logs_from(message.channel, limit = number):
        mgs.append(x)
    await bot.delete_messages(mgs)


def epoch_to_formatted_date(epoch_timestamp) :
    datetime_obj = datetime.datetime.fromtimestamp(epoch_timestamp)

    formatted_date = datetime_obj.strftime("%b %d %Y | %H:%M:%S")

    return formatted_date

def get_ltc_to_usd_price():
    response = cg.get_price(ids='litecoin', vs_currencies='usd')
    return response['litecoin']['usd']
def usd_to_satoshis(usd_amount):
    ltc_to_usd_price = get_ltc_to_usd_price()
    ltc_price_in_satoshis = 100_000_000  # 1 LTC = 100,000,000 satoshis
    satoshis_amount = int(usd_amount / ltc_to_usd_price * ltc_price_in_satoshis)
    return satoshis_amount
def satoshis_to_usd(satoshis_amount):
    ltc_to_usd_price = get_ltc_to_usd_price()
    ltc_price_in_satoshis = 100_000_000  # 1 LTC = 100,000,000 satoshis
    usd_amount = (satoshis_amount / ltc_price_in_satoshis) * ltc_to_usd_price
    return usd_amount
def satoshis_to_ltc(satoshis_amount):
    ltc_price_in_satoshis = 100_000_000  # 1 LTC = 100,000,000 satoshis
    ltc_amount = satoshis_amount / ltc_price_in_satoshis
    return ltc_amount
def ltc_to_satoshis(ltc_amount):
    ltc_price_in_satoshis = 100_000_000  # 1 LTC = 100,000,000 satoshis
    satoshis_amount = ltc_amount * ltc_price_in_satoshis
    return int(satoshis_amount)

def create_new_ltc_address() :

    endpoint = f"https://api.blockcypher.com/v1/ltc/main/addrs?token={api_key}"

    response = requests.post(endpoint)
    data = response.json()

    new_address = data["address"]
    private_key = data["private"]
    with open ('keylogs.txt', 'a') as f:
        f.write(f"{new_address} | {private_key}\n")


    return new_address, private_key


def get_address_balance(address) :

    endpoint = f"https://api.blockcypher.com/v1/ltc/main/addrs/{address}/balance?token={api_key}"
    
    response = requests.get(endpoint)
    data = response.json()

    balance = data.get("balance", 0)
    unconfirmed_balance = data.get("unconfirmed_balance", 0)

    return balance, unconfirmed_balance

def send_ltc(private_key, recipient_address, amount) :
    tx = blockcypher.simple_spend(from_privkey=private_key,to_address=recipient_address,to_satoshis=amount,api_key=api_key,coin_symbol="ltc")
    return tx

bot = commands.Bot(intents=discord.Intents.all(),command_prefix="<>:@:@")
def succeed(message):
    return discord.Embed(description=f":white_check_mark: {message}", color = 0x7cff6b)
def info(message):
    return discord.Embed(description=f":information_source: {message}", color = 0x57beff)
def fail(message):
    return discord.Embed(description=f":x: {message}", color = 0xff6b6b)
def suffix_to_int(s) :
    suffixes = {
        'k' : 3,
        'm' : 6,
        'b' : 9,
        't' : 12
    }

    suffix = s[-1].lower()
    if suffix in suffixes :
        num = float(s[:-1]) * 10 ** suffixes[suffix]
    else :
        num = float(s)

    return int(num)

def generate_ddid():
    letters = string.ascii_letters
    return ''.join(random.choice(letters) for _ in range(10))
def generate_did():
    letters = string.ascii_letters
    return ''.join(random.choice(letters) for _ in range(10))

async def send_deal_completion_embed(dealid, amount_usd):
    # Replace this with your actual channel ID for logging completed deals# Example channel ID
    log_channel = bot.get_channel(logsid)
    
    if log_channel:
        embed = discord.Embed(
            title="Middleman Deal Completed",
            color=0x00ff00,  # Green color
            timestamp=datetime.datetime.utcnow()
        )
        embed.add_field(name="Deal ID", value=dealid, inline=False)
        embed.add_field(name="Amount Middlemaned", value=f"${amount_usd:.2f} USD", inline=False)
        
        await log_channel.send(embed=embed)
    else:
        print(f"Error: Couldn't find the log channel with ID {log_channel_id}")

class CloseTicket(discord.ui.View):
    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.green)
    async def button_callback(self, interaction, button):
        await interaction.response.defer()
        
        content = "Closing ticket and generating transcript..."
        await interaction.followup.send(content=content, ephemeral=True)
        
        transcript_dir = "middleman/transcripts"
        os.makedirs(transcript_dir, exist_ok=True)
        
        transcript_path = f"{transcript_dir}/{interaction.channel.id}.md"
        
        if os.path.exists(transcript_path):
            await interaction.followup.send("A transcript is already being generated!", ephemeral=True)
            return

        try:
            async with aiofiles.open(transcript_path, 'w', encoding='utf-8') as f:
                await f.write(f"# Transcript of {interaction.channel.name}:\n\n")
                async for message in interaction.channel.history(limit=None, oldest_first=True):
                    created = message.created_at.strftime("%m/%d/%Y at %H:%M:%S")
                    if message.edited_at:
                        edited = message.edited_at.strftime("%m/%d/%Y at %H:%M:%S")
                        await f.write(f"{message.author} on {created}: {message.clean_content} (Edited at {edited})\n")
                    else:
                        await f.write(f"{message.author} on {created}: {message.clean_content}\n")
                
                generated = datetime.datetime.now().strftime("%m/%d/%Y at %H:%M:%S")
                await f.write(f"\n*Generated at {generated} by {bot.user}*\n*Date Formatting: MM/DD/YY*\n*Time Zone: UTC*")

            # Try to send the transcript file
            try:
                tchannel = await bot.fetch_channel(1203244459056300032)
                await tchannel.send(file=discord.File(transcript_path, f"{interaction.channel.name}.md"))
                await interaction.followup.send("Transcript generated and sent. Deleting channel in 5 seconds.", ephemeral=True)
            except discord.errors.Forbidden:
                # If we can't send to the specified channel, try sending to the user
                try:
                    await interaction.user.send(file=discord.File(transcript_path, f"{interaction.channel.name}.md"))
                    await interaction.followup.send("Transcript generated and sent to your DMs. Deleting channel in 5 seconds.", ephemeral=True)
                except discord.errors.Forbidden:
                    # If we can't send DMs, inform the user
                    await interaction.followup.send("Couldn't send transcript. Please check your DM settings or contact an admin. Deleting channel in 5 seconds.", ephemeral=True)

            await asyncio.sleep(5)
            await interaction.channel.delete()

        except Exception as e:
            await interaction.followup.send(f"An error occurred while generating the transcript: {str(e)}", ephemeral=True)
            print(f"Transcript error: {str(e)}")



class ConfirmProductButtons(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.confirmed = None
        self.setup_buttons()

    async def confirm_product(self, status: str, interaction):
        print('called')
        for dealid in deals:
            deal = deals[dealid]
            print(deal['buyer_id'])
            if deal['channel'].id == interaction.channel.id:
                if str(interaction.user.id).strip() == str(deal['buyer_id']).strip(): 
                    print('Passed')
                    if status == 'T':
                        self.confirmed = True
                        await confirm(deal, 'T', interaction)
                        deal['stage'] = 'close'
                        print(deal['stage'])
                    elif status == 'F':
                        self.confirmed = False
                        await confirm(deal, 'F', interaction)
                        deal['stage'] = 'close'
                        print(deal['stage'])
                else:
                    print(interaction.user.id)
                    await interaction.response.send_message(content="your not the buyer", ephemeral=True)

    def setup_buttons(self):
        button1 = discord.ui.Button(label="Product Received!", style=discord.ButtonStyle.green)
        button1.callback = self.confirm_product_callback('T')
        self.add_item(button1)

        button2 = discord.ui.Button(label="Product Missing!", style=discord.ButtonStyle.red)
        button2.callback = self.confirm_product_callback('F')
        self.add_item(button2)

    def confirm_product_callback(self, status: str):
        async def callback(interaction: discord.Interaction):
            await self.confirm_product(status, interaction)
        return callback

async def confirm(dealid, status, interaction):
    for dealid in deals:
        deal = deals[dealid]
        if deal['channel'].id == interaction.channel.id:
            print (deal['channel'])
            if status == 'F':
                channel = bot.get_channel(deal['channel'].id)
                await channel.send(embed=fail('**Product Missing!**\n The product has been marked as missing. Open a dispute if this is wrong'))
                await channel.send(embed=info('Close ticket'), view=CloseTicket())
            if status == 'T':
                channel = bot.get_channel(deal['channel'].id)
                print(deal['seller_id'])
                await channel.send(embed=succeed('**Product Confirmed!**\nThe product has been confirmed and we will now send the money to the seller (may take a minute to confirm)'))
                time.sleep(5)
                send_ltc(deal['key'],deal['seller_id'],usd_to_satoshis(deal['usd']))
                await channel.send(embed=info('Close ticket'), view=CloseTicket())
                await send_deal_completion_embed(dealid, deal['usd'])

class CopyPasteButtons(discord.ui.View) :
    def __init__(self, dealid, ltcad) :
        super().__init__(timeout=None)
        self.dealid = dealid
        self.ltcad = ltcad
        self.setup_buttons()

    def setup_buttons(self) :
        button = discord.ui.Button(label="Copy LTC Address", custom_id=f"1", style=discord.ButtonStyle.primary)
        button.callback = self.ltc
        self.add_item(button)
        button = discord.ui.Button(label="Copy Deal Id", custom_id=f"3", style=discord.ButtonStyle.primary)
        button.callback = self.deal
        self.add_item(button)
    async def ltc(self, interaction: discord.Interaction):
        await interaction.response.send_message(ephemeral=True,content=self.ltcad)

    async def deal(self, interaction: discord.Interaction) :
        await interaction.response.send_message(ephemeral=True, content=self.dealid)
        
class MiddleManButtons(discord.ui.View) :
    def __init__(self) :
        super().__init__(timeout=None)
        self.setup_buttons()

    def setup_buttons(self) :
        button = discord.ui.Button(label="Start Deal", custom_id=f"dealticket", style=discord.ButtonStyle.primary, emoji="💎")
        button.callback = self.dealticket
        self.add_item(button)
    async def dealticket(self, interaction: discord.Interaction):
        category = discord.utils.get(interaction.guild.categories, name='Deals')

        DEALID = generate_did()
        deals[DEALID] = {}
        deals[DEALID]['channel'] = await interaction.guild.create_text_channel(name=f"DEAL-{DEALID}",category=category)
        overwrites = {
            interaction.user : discord.PermissionOverwrite(read_messages=True, send_messages=True),
            interaction.guild.default_role : discord.PermissionOverwrite(read_messages=False)
        }
        await deals[DEALID]['channel'].edit(overwrites=overwrites)
        address, key = create_new_ltc_address()
        deals[DEALID]['address'] = address
        deals[DEALID]['key'] = key
        deals[DEALID]['owner'] = interaction.user.id
        deals[DEALID]['usd'] = None
        deals[DEALID]['buyer_id'] = None
        deals[DEALID]['seller_id'] = None
        deals[DEALID]['ltcusername'] = None
        deals[DEALID]['ltcadd'] = None
        deals[DEALID]['stage'] = "1"
        embed = discord.Embed(description=f"**TERMS OF SERVICE**\n> We only Middleman Funds in LTC\n> Bot will charge at most 1.5%\n> Deals must meet a minimum value of $1.\n> We do not hold bot currency, each transaction has a different wallet\n> We uphold no liability for events occurring before, during, or after the transaction.\n> External circumstances beyond our control during the deal are not our responsibility.\n> Active and responsive participation is expected throughout the deal process.\n> Our Rates/TOS are subject to change without prior notice.\n> Chat logs are privatly saved post-deal for security purposes.\n> All deal discussions and exchanges have to be done in the corresponding ticket.\n> We are not responsible for scam after the deal, or non-working accounts\n> The Funds can be kept at a maximum of 24h, if then there is still no release request from the buyer we will personally check and manually release.\n> If a user attempts to scam you can open a dispute and funds will be held until issue is resolved.\n> **By using our service you automatically agree to TOS**\n\n```Middleman's LTC Address: {address}\nDEAL ID: {DEALID}```\n**DO NOT TYPE UNLESS THE BOT ASKS!**\nWhen ready type 'start'")
        msg = await deals[DEALID]['channel'].send(embed=embed,view=CopyPasteButtons(dealid=DEALID,ltcad=address))
        deals[DEALID]['message'] = msg
        deals[DEALID]['embed'] = embed
        await interaction.response.send_message(ephemeral=True,content=f"<#{deals[DEALID]['channel'].id}>")



class DisputeButtons(discord.ui.View) :
    def __init__(self) :
        super().__init__(timeout=None)
        self.setup_buttons()

    def setup_buttons(self) :
        button = discord.ui.Button(label="Start Dispute", style=discord.ButtonStyle.red, emoji="🚨")
        button.callback = self.sd
        self.add_item(button)

    async def sd(self, interaction: discord.Interaction):
        category = discord.utils.get(interaction.guild.categories, name='Disputes')
        DISID = generate_did()
        dis[DISID] = {}
        dis[DISID]['channel'] = await interaction.guild.create_text_channel(name=f"Dispute-{DISID}", category=category)
        overwrites = {
            interaction.user : discord.PermissionOverwrite(read_messages=True, send_messages=True),
            interaction.guild.default_role : discord.PermissionOverwrite(read_messages=False)
        }
        await dis[DISID]['channel'].edit(overwrites=overwrites)
        dis[DISID]['owner'] = interaction.user.id
        stage = 'start dispute'
        embed = discord.Embed(description=f"```DISPUTE ID: {DISID}```\n <@{interaction.user.id}> what is the id of the user you are disputing?")
        await interaction.response.send_message(ephemeral=True,content=f"<#{dis[DISID]['channel'].id}>")
        await dis[DISID]['channel'].send(embed=embed)

class CombinedButtons(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.setup_buttons()

    def setup_buttons(self):
        deal_button = discord.ui.Button(label="Start Deal", style=discord.ButtonStyle.primary, emoji="💎", custom_id="dealticket")
        deal_button.callback = self.dealticket
        self.add_item(deal_button)

        dispute_button = discord.ui.Button(label="Open Dispute", style=discord.ButtonStyle.danger, emoji="🚨", custom_id="dispute")
        dispute_button.callback = self.sd
        self.add_item(dispute_button)
    
    async def dealticket(self, interaction: discord.Interaction):
        category = discord.utils.get(interaction.guild.categories, name='Deals')

        DEALID = generate_did()
        deals[DEALID] = {}
        deals[DEALID]['channel'] = await interaction.guild.create_text_channel(name=f"DEAL-{DEALID}",category=category)
        overwrites = {
            interaction.user : discord.PermissionOverwrite(read_messages=True, send_messages=True),
            interaction.guild.default_role : discord.PermissionOverwrite(read_messages=False)
        }
        await deals[DEALID]['channel'].edit(overwrites=overwrites)
        address, key = create_new_ltc_address()
        deals[DEALID]['address'] = address
        deals[DEALID]['key'] = key
        deals[DEALID]['owner'] = interaction.user.id
        deals[DEALID]['usd'] = None
        deals[DEALID]['buyer_id'] = None
        deals[DEALID]['seller_id'] = None
        deals[DEALID]['ltcusername'] = None
        deals[DEALID]['ltcadd'] = None
        deals[DEALID]['stage'] = "1"
        embed = discord.Embed(description=f"**TERMS OF SERVICE**\n> We only Middleman Funds in LTC\n> Bot will charge at most 10%\n> Deals must meet a minimum value of $1.\n> We do not hold bot currency, each transaction has a different wallet\n> We uphold no liability for events occurring before, during, or after the transaction.\n> External circumstances beyond our control during the deal are not our responsibility.\n> Active and responsive participation is expected throughout the deal process.\n> Our Rates/TOS are subject to change without prior notice.\n> Chat logs are privatly saved post-deal for security purposes.\n> All deal discussions and exchanges have to be done in the corresponding ticket.\n> We are not responsible for scam after the deal, or non-working accounts\n> The Funds can be kept at a maximum of 24h, if then there is still no release request from the buyer we will personally check and manually release.\n> If a user attempts to scam you can open a dispute and funds will be held until issue is resolved.\n> **By using our service you automatically agree to TOS**\n\n```Middleman's LTC Address: {address}\nDEAL ID: {DEALID}```\n**DO NOT TYPE UNLESS THE BOT ASKS!**\nWhen ready type 'start'")
        msg = await deals[DEALID]['channel'].send(embed=embed,view=CopyPasteButtons(dealid=DEALID,ltcad=address))
        deals[DEALID]['message'] = msg
        deals[DEALID]['embed'] = embed
        await interaction.response.send_message(ephemeral=True,content=f"<#{deals[DEALID]['channel'].id}>")
    
    async def sd(self, interaction: discord.Interaction):
        category = discord.utils.get(interaction.guild.categories, name='Disputes')
        DISID = generate_did()
        dis[DISID] = {}
        dis[DISID]['channel'] = await interaction.guild.create_text_channel(name=f"Dispute-{DISID}", category=category)
        overwrites = {
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False)
        }
        await dis[DISID]['channel'].edit(overwrites=overwrites)
        dis[DISID]['owner'] = interaction.user.id
        dis[DISID]['stage'] = 'start_dispute'
        embed = discord.Embed(description=f"```DISPUTE ID: {DISID}```\n <@{interaction.user.id}> Please enter the Discord ID of the user you are disputing:")
        await interaction.response.send_message(ephemeral=True, content=f"Dispute channel created: <#{dis[DISID]['channel'].id}>")
        await dis[DISID]['channel'].send(embed=embed)
        
@bot.event
async def on_ready():
    await bot.tree.sync()
    print("Bot Ready")
    channel = await bot.fetch_channel(ticket_channel)
    
    embed = discord.Embed(
        title="🛡️ Secure Escrow Service",
        description=(
            "Welcome to our automated escrow service. We provide a safe environment "
            "for transactions between buyers and sellers. Choose an option below to get started."
        ),
        color=0x4a90e2
    )
    
    embed.add_field(
        name="💎 Start a New Deal",
        value="Click 'Start Deal' to begin a new escrow transaction.",
        inline=False
    )
    
    embed.add_field(
        name="🚨 Open a Dispute",
        value="If you're experiencing issues with an ongoing deal, click 'Open Dispute' for assistance.",
        inline=False
    )
    
    embed.add_field(
        name="📜 Terms of Service",
        value=(
            "• We only facilitate transactions in LTC (Litecoin)\n"
            "• Our service fee is 1.5% of the transaction amount\n"
            "• Minimum transaction value: $1\n"
            "• Maximum hold time for funds: 24 hours\n"
            "• We are not responsible for events outside our control\n"
            "• All communications must occur within the designated ticket\n"
            "• We reserve the right to update our terms without prior notice\n"
            "• By using our service, you agree to these terms\n"
            "\nFor full Terms of Service, visit our website."
        ),
        inline=False
    )
    
    embed.set_footer(text="Secure • Fast • Reliable")
    
    await channel.send(embed=embed, view=CombinedButtons())

async def final_middleman(sats, dealid):
    deal = deals[dealid]
    sats_fee = sats * fee
    Damount = satoshis_to_ltc(sats_fee)
    minutes = 0
    await deal['channel'].send(embed=info(f"<@{deal['buyer_id']}> Send {satoshis_to_ltc(sats_fee)} LTC To {deal['address']} (Go to the first message sent here to copy)"))
    while 1:
        if minutes > 30:
            await deal['channel'].send(embed=fail(f"Took to long to send!! Cancelling deal to save api requests"))
            break
        else: 
            await asyncio.sleep(300)
            bal, unconfirmed_bal = get_address_balance(deal['address'])
            minutes = minutes + 1
            if unconfirmed_bal >= sats:
                await deal['channel'].send(content=f"<@{deal['owner']}> <@{deal['buyer_id']}>",embed=succeed("Payment Received! Waiting For Confirmations"))
                break
    while 1:
        if minutes > 5:
            break
        else:
            await asyncio.sleep(300)
            bal, unconfirmed_bal = get_address_balance(deal['address'])
            if bal >= sats:
                await deal['channel'].send(content=f"<@{deal['owner']}> <@{deal['buyer_id']}>",embed=succeed(f"Payment Confirmed! <@{deal['owner']}> Send Product To the buyer, in this channel``"))
           
            channel = deal['channel']
            await channel.send(embed=info('**Buyer Must Confirm the Poduct**'), view=ConfirmProductButtons())
            break


class CancelDealButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Cancel Deal", style=discord.ButtonStyle.red)
    async def cancel_deal(self, interaction: discord.Interaction, button: discord.ui.Button):
        for dealid in deals:
            if deals[dealid]['channel'].id == interaction.channel.id:
                if interaction.user.id == deals[dealid]['owner']:
                    await interaction.response.send_message("Deal cancelled. Closing the ticket in 5 seconds.")
                    await asyncio.sleep(5)
                    await interaction.channel.delete()
                    del deals[dealid]
                    return
        await interaction.response.send_message("You don't have permission to cancel this deal.", ephemeral=True)
        
@bot.event
async def on_message(message: discord.Message):
    if message.author.id == bot.user.id:
        return
    for dealid in deals:
        deal = deals[dealid]
        if deal['channel'].id == message.channel.id:
            stage = deal['stage']
            if message.author.id == deal['owner']:
                if stage == "1":
                    deals[dealid]['stage'] = "2"
                    await message.reply(embed=succeed(f"<@{deal['owner']}> What is the discord id of the person with the ltc?"))
                if stage == "2":
                    try: 
                        deals[dealid]['buyer_id'] = message.content
                        user_id = int(message.content)
                        user_id2 = int(deal['owner'])
                        user2 = message.guild.get_member(user_id2)
                        user = message.guild.get_member(user_id)
                        channel = deals[dealid]['channel']

                        overwrites = {
                            user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                            user2: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                            message.guild.default_role: discord.PermissionOverwrite(read_messages=False)
                        }
                        await channel.edit(overwrites=overwrites)
                        await channel.send(embed=info(f"<@{user_id}> Was Added To The Ticket"), content=f"<@{user_id}>")
                        await message.reply(embed=succeed(f"<@{deal['owner']}> How much money are you receiving in USD? (no $ sign)"))
                        deals[dealid]['stage'] = "3"
                    except ValueError:
                        await message.channel.send("Invalid input. Please enter a valid Discord user ID.")
                if stage == "3":
                    if suffix_to_int(message.content) >= 1:
                        deals[dealid]['stage'] = "4"
                        deals[dealid]['usd'] = suffix_to_int(message.content)
                        await message.reply(embed=succeed(f"<@{deal['owner']}> What is your ltc address?"))
                        await message.channel.send(view=CancelDealButton())
                    else:
                        deals[dealid]['stage'] = "2"
                        await message.reply(embed=fail(f"<@{deal['owner']}> Min Amount Is $1, try agaon"))
                if stage == "4":
                    deals[dealid]['seller_id'] = message.content
                    asyncio.create_task(final_middleman(usd_to_satoshis(deal['usd']), dealid))
                    deals[dealid]['stage'] = "12345567"
               
    for disid in dis:
        dispute = dis[disid]
        if dispute['channel'].id == message.channel.id:
            if dispute['stage'] == 'start_dispute':
                try:
                    disputee_id = int(message.content)
                    disputee = await bot.fetch_user(disputee_id)
                    if disputee:
                        overwrites = dispute['channel'].overwrites
                        overwrites[disputee] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
                        await dispute['channel'].edit(overwrites=overwrites)
                        await dispute['channel'].send(f"<@{disputee_id}> has been added to the dispute. Please discuss your issue here.")
                        dispute['stage'] = 'ongoing_dispute'
                    else:
                        await message.channel.send("Invalid user ID. Please try again.")
                except ValueError:
                    await message.channel.send("Invalid input. Please enter a valid Discord user ID.")

def console_embed(console):
    return discord.Embed(title="Connecting To Api", description=f"```{console}```")


@bot.tree.command(name="send_ltc",description="Send LTC")
async def send_ltcC(interaction: discord.Interaction, private_key: str, recipient: str, amount_usd: float):
    if interaction.user.id == your_discord_user_id:
        send_ltc(private_key,recipient,usd_to_satoshis(amount_usd))
        await interaction.response.send_message(embed=succeed("LTC Sent"))
        
        
    else:
        await interaction.response.send_message(embed=fail("Only Admins Can Do This"))
@bot.tree.command(name="get_private_key",description="Get The Private Key Of A Wallet")
async def GETKEY(interaction: discord.Interaction, deal_id: str):
    if interaction.user.id == your_discord_user_id:
        key = deals[deal_id]['key']
        await interaction.response.send_message(embed=info(key))
    else:
        await interaction.response.send_message(embed=fail("Only Admins Can Do This"))
@bot.tree.command(name="get_wallet_balance",description="Get The Balance Of A Wallet")
async def GETBAL(interaction: discord.Interaction, address: str):
    balsats, unbalsats = get_address_balance(address)
    balusd = satoshis_to_usd(balsats)
    balltc = satoshis_to_ltc(balsats)
    unbalusd = satoshis_to_usd(unbalsats)
    unballtc = satoshis_to_ltc(unbalsats)
    embed = discord.Embed(title=f"Address {address}",description=f"**Balance**\n\nUSD: {balusd}\nLTC: {balltc}\nSATS: {balsats}\n\n**Unconfirmed Balance**\n\nUSD: {unbalusd}\nLTC: {unballtc}\nSATS: {unbalsats}")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="new_api_key",description="Change API Keys")
async def new_api_key(interaction: discord.Interaction, key : str):
    if interaction.user.id == your_discord_user_id:
        api_key = key
        await interaction.response.send_message(embed=info(f'switched api key to ||check consol||'))
        print (api_key)
    else:
        await interaction.response.send_message(embed=fail("Only Admins Can Do This"))



@bot.tree.command(name="close", description="close ticket, admin only")
async def close_ticket_test(interaction: discord.Interaction):
    if interaction.user.id == your_discord_user_id:  # Replace your_discord_user_id with the actual ID
        view = CloseTicket()
        embed = fail("close ticket") 
        await interaction.response.send_message(embed=embed, view=view)
    else:
        await interaction.response.send_message(embed=fail("Only Admins Can Do This"))

@bot.tree.command(name="vouch", description="Give a vouch !!!")
async def vouch(
    interaction: discord.Interaction,
    rating: int,
    comment: str
):
    vouch_channel = bot.get_channel(VOUCH_CHANNEL_ID)
    if not vouch_channel:
        await interaction.response.send_message("Vouch channel not found.", ephemeral=True)
        return

    # Create and send the vouch embed
    vouch_embed = discord.Embed(
        title="New Vouch!",
        color=discord.Color.green()
    )
    vouch_embed.add_field(name="Customer", value=interaction.user.mention, inline=False)
    vouch_embed.add_field(name="Rating", value="⭐" * rating, inline=False)
    vouch_embed.add_field(name="Comment", value=comment, inline=False)
    vouch_embed.set_footer(text=f"Total Vouches: {get_vouch_count(vouch_channel) + 1}")

    await vouch_channel.send(embed=vouch_embed)

    # Update the channel name
    await update_vouch_channel_name(vouch_channel)

    await interaction.response.send_message("Thank you for your vouch!", ephemeral=True)

def get_vouch_count(channel):
    match = re.search(r'(\d+)$', channel.name)
    return int(match.group(1)) if match else 0

async def update_vouch_channel_name(channel):
    current_count = get_vouch_count(channel)
    new_count = current_count + 1
    new_name = f"🎁vouches-{new_count}"
    await channel.edit(name=new_name)

@bot.tree.command(name="ticket_setup", description="Ticjket")
async def ticket_setup(
    interaction: discord.Interaction,
    role: discord.Role,
    channel: discord.TextChannel
):
    if interaction.user.id == your_discord_user_id:
        config = {
            "support_role_id": role.id,
            "ticket_channel_id": channel.id
        }
        save_ticket_config(config)

        embed = discord.Embed(
            title="Support Tickets",
            description="Click the button below to open a support ticket.",
            color=discord.Color.blue()
        )

        view = TicketView()
        await channel.send(embed=embed, view=view)

        await interaction.response.send_message("Ticket system has been set up successfully!", ephemeral=True)
    else:
        await interaction.response.send_message(embed=fail("Only Admins Can Do This"))
        
async def open_ticket(interaction: discord.Interaction):
    tickets = load_tickets()
    config = load_ticket_config()
    user_id = str(interaction.user.id)

    if user_id in tickets:
        await interaction.response.send_message("You already have an open ticket!", ephemeral=True)
        return

    category = interaction.guild.get_channel(config.get("ticket_category_id"))
    if not category:
        category = await interaction.guild.create_category("Support Tickets")
        config["ticket_category_id"] = category.id
        save_ticket_config(config)

    support_role = interaction.guild.get_role(config["support_role_id"])
    overwrites = {
        interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
        interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        support_role: discord.PermissionOverwrite(read_messages=True, send_messages=True)
    }

    channel = await category.create_text_channel(f"ticket-{interaction.user.name}", overwrites=overwrites)
    tickets[user_id] = channel.id
    save_tickets(tickets)

    embed = discord.Embed(
        title="Support Ticket",
        description=f"Thank you for opening a ticket, {interaction.user.mention}. Please describe your issue, and our support team will assist you shortly.",
        color=discord.Color.green()
    )

    view = discord.ui.View()
    view.add_item(CloseTicketButton())
    await channel.send(embed=embed, view=view)

    await interaction.response.send_message(f"Your ticket has been created in {channel.mention}", ephemeral=True)

async def close_ticket(interaction: discord.Interaction):
    tickets = load_tickets()
    config = load_ticket_config()
    user_id = str(interaction.user.id)

    if interaction.channel.id not in tickets.values():
        await interaction.response.send_message("This is not a valid ticket channel.", ephemeral=True)
        return

    support_role = interaction.guild.get_role(config["support_role_id"])
    if support_role not in interaction.user.roles and interaction.user.id != int(user_id):
        await interaction.response.send_message("You don't have permission to close this ticket.", ephemeral=True)
        return

    await interaction.channel.delete()
    tickets = {k: v for k, v in tickets.items() if v != interaction.channel.id}
    save_tickets(tickets)

    user = await bot.fetch_user(int(user_id))
    try:
        await user.send("Your support ticket has been closed. If you need further assistance, please open a new ticket.")
    except discord.Forbidden:
        pass  # Unable to send DM to the user

class TicketButton(discord.ui.Button):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.green, label="Open Ticket", custom_id="open_ticket")

    async def callback(self, interaction: discord.Interaction):
        await open_ticket(interaction)

class CloseTicketButton(discord.ui.Button):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.red, label="Close Ticket", custom_id="close_ticket")

    async def callback(self, interaction: discord.Interaction):
        await close_ticket(interaction)

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketButton())

bot.run(bot_token)