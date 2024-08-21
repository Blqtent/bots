import discord
from discord.ext import commands
import requests
import json
import time
import os
from dotenv import load_dotenv
import asyncio

BLOCKCYPHER_TOKEN = "c81588d3df09465bb5b9e29b148c0fad";

intents = discord.Intents.all()
intents.message_content = True
bot = commands.Bot(command_prefix='/', intents=intents)

SUPPORTED_CRYPTOS = ['BTC', 'LTC', 'ETH']
EXCHANGE_CHANNEL_ID = None
BOT_WALLETS = {}

TERMS_OF_SERVICE = """
Service Fee: 8%
Example: If you are exchanging 1 LTC (63 dollars at time of writing)
you only pay 5 dollars service fee

1. All funds are legally exchanged
2. The exchange rate is determined at the time of transaction.
3. The user is responsible for entering the correct recipient address.
4. Transactions cannot be reversed once completed.
5. The service is provided 'as is' without any warranties.
6. We reserve the right to refuse service to anyone.
7. By using this service, you agree to these terms.
"""

def load_json(filename):
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            print(f"Loaded")
            return json.load(f)
    return {}

def create_wallet(crypto):
    url = f'https://api.blockcypher.com/v1/{crypto.lower()}/main/addrs?token={BLOCKCYPHER_TOKEN}'
    response = requests.post(url)
    if response.status_code == 201:
        return response.json()
    else:
        return None

def check_balance(address, crypto):
    url = f'https://api.blockcypher.com/v1/{crypto.lower()}/main/addrs/{address}/balance?token={BLOCKCYPHER_TOKEN}'
    response = requests.get(url)
    if response.status_code == 200:
        balance = response.json()
        return balance['balance']
    else:
        return None

def get_exchange_rate(from_crypto, to_crypto):
    url = f'https://api.coinbase.com/v2/prices/{from_crypto}-{to_crypto}/spot'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return float(data['data']['amount'])
    else:
        return None

def send_transaction(private_key, recipient_address, coin, amount) :
    tx = blockcypher.simple_spend(from_privkey=private_key,to_address=recipient_address,to_satoshis=amount,api_key=TOKEN,coin_symbol=coin)
    return tx

@bot.event
async def on_ready():
    await bot.tree.sync()
    BOT_WALLETS = load_json("E:\\0-Skid Inc\\exchange\\bot_wallets.json")
    print(f'Logged in as {bot.user.name}')

@bot.tree.command(name="setup",description="Setup the exchange bot")
@commands.has_role('Manager')
async def setup(ctx, channel: discord.TextChannel):
    global EXCHANGE_CHANNEL_ID, BOT_WALLETS
    EXCHANGE_CHANNEL_ID = channel.id

    for crypto in SUPPORTED_CRYPTOS:
        wallet = create_wallet(crypto)
        if wallet:
            BOT_WALLETS[crypto] = wallet
        else:
            await ctx.send(f"Failed to create {crypto} wallet.")
            return

    with open('bot_wallets.json', 'w') as f:
        json.dump(BOT_WALLETS, f)

    embed = discord.Embed(title="Crypto Exchange", description="Welcome to our crypto exchange service. Please read our Terms of Service below:")
    embed.add_field(name="Terms of Service", value=TERMS_OF_SERVICE, inline=False)
    embed.add_field(name="Start Exchange", value="Press the button below to start an exchange.", inline=False)
    
    class ExchangeButton(discord.ui.Button):
        def __init__(self):
            super().__init__(label="Start Exchange", style=discord.ButtonStyle.primary, custom_id="start_exchange")
        
        async def callback(self, interaction: discord.Interaction):
            overwrites = {
                interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }
            channel = await interaction.guild.create_text_channel(f'exchange-{interaction.user.name}', overwrites=overwrites)
            
            await channel.send(f"Welcome {interaction.user.mention}! Your exchange process starts here. Remember, there's an 8% service fee.", view=ExchangeView(channel))
            await interaction.response.send_message(f"I've created a private channel for your exchange: {channel.mention}", ephemeral=True)

    view = discord.ui.View()
    view.add_item(ExchangeButton())

    await channel.send(embed=embed, view=view)
    await ctx.response.send_message("Setup complete. Exchange menu sent to the specified channel.")

@bot.tree.command(name="balance",description="Shows the balance")
async def balance(ctx):
    """Check the bot's balance for all su//pported cryptocurrencies."""
    embed = discord.Embed(title="Bot Balance", color=discord.Color.blue())
    
    for crypto in SUPPORTED_CRYPTOS:
        try:
            address = BOT_WALLETS[crypto]['address']
            balance = check_balance(address, crypto)
            if balance is not None:
                # Convert balance from smallest unit (e.g., satoshis) to whole units
                if crypto == 'BTC':
                    balance = balance / 1e8  # 1 BTC = 100,000,000 satoshis
                elif crypto == 'LTC':
                    balance = balance / 1e8  # 1 LTC = 100,000,000 litoshis
                elif crypto == 'ETH':
                    balance = balance / 1e18  # 1 ETH = 1,000,000,000,000,000,000 wei
                embed.add_field(name=f"{crypto} Balance", value=f"{balance:.8f} {crypto}", inline=False)
            else:
                embed.add_field(name=f"{crypto} Balance", value="Unable to fetch balance", inline=False)
        except KeyError:
            embed.add_field(name=f"{crypto} Balance", value="Wallet not set up", inline=False)
        except Exception as e:
            embed.add_field(name=f"{crypto} Balance", value=f"Error: {str(e)}", inline=False)

    await ctx.response.send_message(embed=embed)

def check_balance(address, crypto):
    url = f'https://api.blockcypher.com/v1/{crypto.lower()}/main/addrs/{address}/balance'
    response = requests.get(url)
    if response.status_code == 200:
        balance = response.json()
        return balance['balance']  # Return the raw balance
    else:
        return None

class ExchangeView(discord.ui.View):
    def __init__(self, channel):
        super().__init__()
        self.channel = channel
        self.from_crypto = None
        self.to_crypto = None
        self.to_address = None
        self.amount = None

    @discord.ui.select(placeholder="Select crypto to exchange from", options=[discord.SelectOption(label=crypto) for crypto in SUPPORTED_CRYPTOS])
    async def select_from_crypto(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.from_crypto = select.values[0]
        self.children[0].disabled = True
        self.children[1].disabled = False
        await interaction.response.edit_message(content=f"You selected {self.from_crypto} as the crypto to exchange from. Now, please select the crypto you want to exchange to.", view=self)

    @discord.ui.select(placeholder="Select crypto to exchange to", options=[discord.SelectOption(label=crypto) for crypto in SUPPORTED_CRYPTOS], disabled=True)
    async def select_to_crypto(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.to_crypto = select.values[0]
        self.children[1].disabled = True
        self.children[2].disabled = False  # Enable the "Enter Address" button
        await interaction.response.edit_message(content=f"You selected {self.to_crypto} as the crypto to exchange to. Please click 'Enter Address' to provide your {self.to_crypto} address.", view=self)

    @discord.ui.button(label="Enter Address", style=discord.ButtonStyle.primary, disabled=True)
    async def enter_address(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AddressModal(self))

    @discord.ui.button(label="Enter Amount", style=discord.ButtonStyle.primary, disabled=True)
    async def enter_amount(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AmountModal(self))

    @discord.ui.button(label="Cancel Exchange", style=discord.ButtonStyle.danger)
    async def cancel_exchange(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Exchange cancelled. This channel will be deleted in 3 seconds.")
        await asyncio.sleep(3)
        await self.channel.delete()

class AddressModal(discord.ui.Modal):
    def __init__(self, parent_view):
        super().__init__(title="Enter Your Address")
        self.parent_view = parent_view
        self.address = discord.ui.TextInput(label="Address", placeholder="Enter your crypto address here")
        self.add_item(self.address)

    async def on_submit(self, interaction: discord.Interaction):
        self.parent_view.to_address = self.address.value
        self.parent_view.children[2].disabled = True
        self.parent_view.children[3].disabled = False  # Enable the "Enter Amount" button
        await interaction.response.edit_message(content=f"Address received. Now, please click 'Enter Amount' to specify the amount of {self.parent_view.from_crypto} you wish to exchange.", view=self.parent_view)

class AmountModal(discord.ui.Modal):
    def __init__(self, parent_view):
        super().__init__(title="Enter Amount")
        self.parent_view = parent_view
        self.amount = discord.ui.TextInput(label="Amount", placeholder=f"Enter amount in {self.parent_view.from_crypto}")
        self.add_item(self.amount)

    async def on_submit(self, interaction: discord.Interaction):
        self.parent_view.amount = float(self.amount.value)
        self.parent_view.children[3].disabled = True
        await interaction.response.edit_message(content="Amount received. Generating temporary wallet...", view=self.parent_view)
        await self.start_exchange(interaction)

    async def start_exchange(self, interaction):
        temp_wallet = create_wallet(self.parent_view.from_crypto)
        if not temp_wallet:
            await interaction.followup.send("Failed to create temporary wallet. Please try again later.")
            return

        service_fee = self.parent_view.amount * 0.08
        total_amount = self.parent_view.amount + service_fee

        await interaction.followup.send(f"Please send {total_amount} {self.parent_view.from_crypto} to this address: {temp_wallet['address']}\n"
                                        f"This includes your exchange amount of {self.parent_view.amount} {self.parent_view.from_crypto} "
                                        f"plus the 8% service fee of {service_fee} {self.parent_view.from_crypto}.")

        for _ in range(10):
            await asyncio.sleep(60)
            balance = check_balance(temp_wallet['address'], self.parent_view.from_crypto)
            if balance >= total_amount:
                break
        else:
            await interaction.followup.send("Time limit exceeded. Transaction cancelled.")
            return

        tx = send_transaction(temp_wallet['private'], BOT_WALLETS[self.parent_view.from_crypto], int(to_amount * 1e18 if self.parent_view.from_crypto == "ETH" else 1e8), self.parent_view.from_crypto)

        exchange_rate = get_exchange_rate(self.parent_view.from_crypto, self.parent_view.to_crypto)
        if not exchange_rate:
            await interaction.followup.send("Failed to get exchange rate. Please try again later.")
            return

        to_amount = self.parent_view.amount * exchange_rate

        tx = send_transaction(BOT_WALLETS[self.parent_view.to_crypto]['private'], self.parent_view.to_address, int(to_amount * 1e18 if self.parent_view.to_crypto == "ETH" else 1e8), self.parent_view.to_crypto)
        if not tx:
            await interaction.followup.send("Failed to send transaction. Please contact support.")
            return

        receipt = f"Exchange complete!\nFrom: {self.parent_view.amount} {self.parent_view.from_crypto}\nTo: {to_amount} {self.parent_view.to_crypto}\nAddress: {self.parent_view.to_address}\nTransaction ID: {tx['tx']['hash']}\nService Fee: {service_fee} {self.parent_view.from_crypto}"
        await interaction.user.send(receipt)
        owner = await bot.fetch_user(bot.owner_id)
        await owner.send(f"Merchant receipt:\n{receipt}")

        await interaction.followup.send("Exchange completed successfully. Check your DMs for the receipt. This channel will be deleted in 1 minute.")
        await asyncio.sleep(60)
        await self.parent_view.channel.delete()

bot.run("")

