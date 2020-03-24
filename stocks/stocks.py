import discord
from redbot.core import bank
from redbot.core import commands
from redbot.core import Config
import aiohttp

STOCK_URL = 'https://financialmodelingprep.com/api/v3/stock/real-time-price'


class Stocks(commands.Cog):
	"""Buy and sell stocks with bot currency."""
	def __init__(self, bot):
		self.bot = bot
		self.config = Config.get_conf(self, identifier=145519400223506432)
		self.config.register_user(
			stocks = {}
		)
	
	@commands.group(aliases=['stock', 'stonks', 'stonk'])
	async def stocks(self, ctx):
		"""Group command for stocks."""
		pass
	
	@stocks.command()
	async def buy(self, ctx, name, shares: int):
		"""
		Buy stocks.
		
		Enter the ticker symbol for the stock.
		Conversion rate: $1 = 100 credits
		"""
		plural = 's' if shares != 1 else ''
		currency = await bank.get_currency_name(ctx.guild)
		if shares < 1:
			await ctx.send('You cannot buy less than one share.')
			return
		name = name.upper()
		stock_data = await self._get_stock_data()
		if name not in stock_data:
			await ctx.send(f'I couldn\'t find any data for the stock {name}. Please try another stock.')
			return
		price = stock_data[name]
		try:
			bal = await bank.withdraw_credits(ctx.author, shares * price)
		except ValueError:
			bal = await bank.get_balance(ctx.author)
			await ctx.send(
				f'You cannot afford {shares} share{plural} of {name}. '
				f'It would cost {price * shares} {currency} ({price} {currency} each). '
				f'You only have {bal} {currency}.'
			)
			return
		async with self.config.user(ctx.author).stocks() as user_stocks:
			if name in user_stocks:
				user_stocks[name] += shares
			else:
				user_stocks[name] = shares
		await ctx.send(
			f'You purchased {shares} share{plural} of {name} for {price * shares} {currency} '
			f'({price} {currency} each).\nYou now have {bal} {currency}.'
		)
	
	@stocks.command()
	async def sell(self, ctx, name, shares: int):
		"""
		Sell stocks.
		
		Enter the ticker symbol for the stock.
		Conversion rate: $1 = 100 credits
		"""
		plural = 's' if shares != 1 else ''
		if shares < 1:
			await ctx.send('You cannot sell less than one share.')
			return
		name = name.upper()
		stock_data = await self._get_stock_data()
		if name not in stock_data:
			await ctx.send(f'I couldn\'t find any data for the stock {name}. Please try another stock.')
			return
		price = stock_data[name]
		async with self.config.user(ctx.author).stocks() as user_stocks:
			if name not in user_stocks:
				await ctx.send(f'You do not have any shares of {name}.')
				return
			if shares > user_stocks[name]:
				await ctx.send(
					f'You do not have enough shares of {name}. '
					f'You only have {user_stocks[name]} share{plural}.'
				)
				return
			user_stocks[name] -= shares
			if user_stocks[name] == 0:
				del user_stocks[name]
		bal = await bank.deposit_credits(ctx.author, shares * price)
		currency = await bank.get_currency_name(ctx.guild)
		await ctx.send(
			f'You sold {shares} share{plural} of {name} for {price * shares} {currency} '
			f'({price} {currency} each).\nYou now have {bal} {currency}.'
		)

	@stocks.command()
	async def list(self, ctx):
		"""List your stocks."""
		user_stocks = await self.config.user(ctx.author).stocks()
		if not user_stocks:
			await ctx.send('You do not have any stocks.')
			return
		stock_data = await self._get_stock_data()
		name_len = max(max(len(n) for n in user_stocks), 4) + 1
		count_len = max(max(len(str(stock_data[n])) for n in user_stocks), 5) + 1
		msg = '```\nName'
		msg += ' ' * (name_len - 4)
		msg += '| Count'
		msg += ' ' * (count_len - 5)
		msg += '| Price\n'
		msg += '-' * (9 + name_len + count_len)
		msg += '\n'
		for stock in user_stocks:
			if stock in stock_data:
				price = stock_data[stock]
			else:
				price = 'Unknown'
			msg += f'{stock}'
			msg += ' ' * (name_len - len(stock))
			msg += f'| {user_stocks[stock]}'
			msg +=	' ' * (count_len - len(str(user_stocks[stock])))
			msg += f'| {price}\n'
		msg += '```'
		await ctx.send(msg)
	
	@stocks.command()
	async def price(self, ctx, name):
		"""
		View the price of a stock.
		
		Enter the ticker symbol for the stock.
		Conversion rate: $1 = 100 credits
		"""
		name = name.upper()
		stock_data = await self._get_stock_data()
		if name not in stock_data:
			await ctx.send(f'I couldn\'t find any data for the stock {name}. Please try another stock.')
			return
		price = stock_data[name]
		currency = await bank.get_currency_name(ctx.guild)
		await ctx.send(f'{name}: {price} {currency} per share.')

	@staticmethod
	async def _get_stock_data():
		"""Returns a dict mapping stock symbols to their converted price."""
		async with aiohttp.ClientSession() as session:
			async with session.get(STOCK_URL) as r:
				r = await r.json()
				r = r['stockList']
		stock = {x['symbol']: int(x['price'] * 100) for x in r}
		return stock
