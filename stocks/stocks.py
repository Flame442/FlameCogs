import discord
from redbot.core import bank
from redbot.core import commands
from redbot.core import Config
from redbot.core.utils.chat_formatting import humanize_number
import aiohttp


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
		Conversion rate: $1 = 100 credits.
		"""
		await self._fix_stocks(ctx.author)
		plural = 's' if shares != 1 else ''
		currency = await bank.get_currency_name(ctx.guild)
		if shares < 1:
			await ctx.send('You cannot buy less than one share.')
			return
		name = name.upper()
		try:
			stock_data = await self._get_stock_data([name])
		except ValueError as e:
			return await ctx.send(e)
		if name not in stock_data:
			await ctx.send(f'I couldn\'t find any data for the stock {name}. Please try another stock.')
			return
		price = stock_data[name]['price']
		try:
			bal = await bank.withdraw_credits(ctx.author, shares * price)
		except ValueError:
			bal = await bank.get_balance(ctx.author)
			await ctx.send(
				f'You cannot afford {humanize_number(shares)} share{plural} of {name}. '
				f'It would cost {humanize_number(price * shares)} {currency} ({humanize_number(price)} {currency} each). '
				f'You only have {humanize_number(bal)} {currency}.'
			)
			return
		async with self.config.user(ctx.author).stocks() as user_stocks:
			if name in user_stocks:
				user_stocks[name]['count'] += shares
			else:
				user_stocks[name] = {'count': shares, 'total_count': stock_data[name]['total_count']}
		await ctx.send(
			f'You purchased {humanize_number(shares)} share{plural} of {name} for {price * shares} {currency} '
			f'({humanize_number(price)} {currency} each).\nYou now have {humanize_number(bal)} {currency}.'
		)
	
	@stocks.command()
	async def sell(self, ctx, name, shares: int):
		"""
		Sell stocks.
		
		Enter the ticker symbol for the stock.
		Conversion rate: $1 = 100 credits.
		"""
		await self._fix_stocks(ctx.author)
		plural = 's' if shares != 1 else ''
		if shares < 1:
			await ctx.send('You cannot sell less than one share.')
			return
		name = name.upper()
		try:
			stock_data = await self._get_stock_data([name])
		except ValueError as e:
			return await ctx.send(e)
		if name not in stock_data:
			await ctx.send(f'I couldn\'t find any data for the stock {name}. Please try another stock.')
			return
		price = stock_data[name]['price']
		async with self.config.user(ctx.author).stocks() as user_stocks:
			if name not in user_stocks:
				await ctx.send(f'You do not have any shares of {name}.')
				return
			if shares > user_stocks[name]['count']:
				await ctx.send(
					f'You do not have enough shares of {name}. '
					f'You only have {humanize_number(user_stocks[name])} share{plural}.'
				)
				return
			user_stocks[name]['count'] -= shares
			if user_stocks[name]['count'] == 0:
				del user_stocks[name]
		bal = await bank.deposit_credits(ctx.author, shares * price)
		currency = await bank.get_currency_name(ctx.guild)
		await ctx.send(
			f'You sold {humanize_number(shares)} share{plural} of {name} for {humanize_number(price * shares)} {currency} '
			f'({humanize_number(price)} {currency} each).\nYou now have {humanize_number(bal)} {currency}.'
		)

	@stocks.command()
	async def list(self, ctx):
		"""List your stocks."""
		await self._fix_stocks(ctx.author)
		user_stocks = await self.config.user(ctx.author).stocks()
		if not user_stocks:
			await ctx.send('You do not have any stocks.')
			return
		try:
			stock_data = await self._get_stock_data(user_stocks.keys())
		except ValueError as e:
			return await ctx.send(e)
		name_len = max(max(len(n) for n in user_stocks), 4) + 1
		count_len = max(max(len(str(stock_data[n]['price'])) for n in user_stocks), 5) + 1
		msg = '```\nName'
		msg += ' ' * (name_len - 4)
		msg += '| Count'
		msg += ' ' * (count_len - 5)
		msg += '| Price\n'
		msg += '-' * (9 + name_len + count_len)
		msg += '\n'
		for stock in user_stocks:
			if stock in stock_data:
				price = stock_data[stock]['price']
			else:
				price = 'Unknown'
			msg += f'{stock}'
			msg += ' ' * (name_len - len(stock))
			msg += f'| {humanize_number(user_stocks[stock]["count"])}'
			msg +=	' ' * (count_len - len(str(humanize_number(user_stocks[stock]['count']))))
			msg += f'| {humanize_number(price)}\n'
		msg += '```'
		await ctx.send(msg)
	
	@stocks.command()
	async def price(self, ctx, name):
		"""
		View the price of a stock.
		
		Enter the ticker symbol for the stock.
		Conversion rate: $1 = 100 credits.
		"""
		name = name.upper()
		try:
			stock_data = await self._get_stock_data([name])
		except ValueError as e:
			return await ctx.send(e)
		if name not in stock_data:
			await ctx.send(f'I couldn\'t find any data for the stock {name}. Please try another stock.')
			return
		price = stock_data[name]['price']
		real = str(price)
		real = ('0' * (3 - max(len(real), 0))) + real
		real =  '$' + real[:-2] + '.' + real[-2:]
		currency = await bank.get_currency_name(ctx.guild)
		await ctx.send(f'**{name}:** {humanize_number(price)} {currency} per share ({real}).')

	async def _fix_stocks(self, user):
		"""Fix a user's stock data to account for old data and stock splits."""
		async with self.config.user(user).stocks() as user_stocks:
			try:
				stock_data = await self._get_stock_data(user_stocks.keys())
			except ValueError as e:
				return
			for stock in user_stocks:
				if isinstance(user_stocks[stock], int):
					user_stocks[stock] = {
						'count': user_stocks[stock],
						'total_count': stock_data[stock]['total_count']
					}
				elif stock in stock_data and user_stocks[stock]['total_count'] != stock_data[stock]['total_count']:
					old = user_stocks[stock]['total_count']
					new = stock_data[stock]['total_count']
					if not (old and new):
						user_stocks[stock]['total_count'] = new
						continue
					if old // new != 0:
						user_stocks[stock]['count'] //= old // new
					elif new // old != 0:
						user_stocks[stock]['count'] *= new // old
					user_stocks[stock]['total_count'] = new
	
	async def _get_stock_data(self, stocks: list):
		"""
		Returns a dict mapping stock symbols to a dict of their converted price and the total shares of that stock.
		
		This function is designed to contain all of the API code in order to avoid having to mangle multiple parts
		of the code in the event of an API change.
		"""
		api_url = 'https://sandbox.tradier.com/v1/markets/quotes'
		stocks = ','.join(stocks)
		if not stocks:
			return []
		token = await self.bot.get_shared_api_tokens('stocks')
		token = token.get('key', None)
		if not token:
			raise ValueError(
				'You need to set an API key!\n'
				'Follow this guide for instructions on how to get one:\n'
				'<https://github.com/Flame442/FlameCogs/blob/master/stocks/setup.md>'
			)
		params = {'symbols': stocks}
		headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/json'}
		async with aiohttp.ClientSession() as session:
			async with session.get(api_url, params=params, headers=headers) as r:
				try:
					r = await r.json()
				except aiohttp.client_exceptions.ContentTypeError:
					#This might happen when being rate limited, but IDK for sure...
					raise ValueError('Could not get stock data. The API key entered is most likely not valid.')
		r = r['quotes']
		if 'quote' not in r:
			return []
		r = r['quote']
		if not isinstance(r, list):
			r = [r]
		stock = {
			x['symbol']: {
				'price': int(x['last'] * 100),
				'total_count': None #int(x['marketCap'] / x['last']) if x['marketCap'] else None
			} for x in r if 'last' in x
		}
		return stock

	async def red_delete_data_for_user(self, *, requester, user_id):
		"""Delete stock data for a particular user."""
		await self.config.user_from_id(user_id).clear()
