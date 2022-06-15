import discord
from redbot.core.data_manager import bundled_data_path
from redbot.core.data_manager import cog_data_path
from redbot.core import commands
from redbot.core import Config
from redbot.core import checks
from random import randint
import asyncio, os


class Hangman(commands.Cog):
	"""Play hangman with the bot."""
	def __init__(self, bot):
		self.bot = bot
		self.config = Config.get_conf(self, identifier=7345167902)
		self.config.register_guild(
			fp = str(bundled_data_path(self) / 'words.txt'),
			doEdit = True
		)
		self.man = [
			(
				'    ___    \n'
				'   |   |   \n'
				'   |   O   \n'
				'   |       \n'
				'   |       \n'
				'   |       \n'
				'   |       \n'
			), (
				'    ___    \n'
				'   |   |   \n'
				'   |   O   \n'
				'   |   |   \n'
				'   |   |   \n'
				'   |       \n'
				'   |       \n'
			), (
				'    ___    \n'
				'   |   |   \n'
				'   |   O   \n'
				'   |  \\|  \n'
				'   |   |   \n'
				'   |       \n'
				'   |       \n'
			), (
				'    ___    \n'
				'   |   |   \n'
				'   |   O   \n'
				'   |  \\|/ \n'
				'   |   |   \n'
				'   |       \n'
				'   |       \n'
			), (
				'    ___    \n'
				'   |   |   \n'
				'   |   O   \n'
				'   |  \\|/ \n'
				'   |   |   \n'
				'   |  /    \n'
				'   |       \n'
			), (
				'    ___    \n'
				'   |   |   \n'
				'   |   O   \n'
				'   |  \\|/ \n'
				'   |   |   \n'
				'   |  / \\ \n'
				'   |       \n'
			), (
				'    ___    \n'
				'   |   |   \n'
				'   |   X   \n'
				'   |  \\|/ \n'
				'   |   |   \n'
				'   |  / \\ \n'
				'   |       \n'
			)
		]

	@staticmethod
	def _get_message(word, guessed):
		"""Returns a string of the guessing text."""
		p = ''
		for l in word:
			if l not in 'abcdefghijklmnopqrstuvwxyz': #auto print non letter characters
				p += l + ' '
			elif l in guessed: #print already guessed characters
				p += l + ' '
			else:
				p += '_ ' 
		p += '    ('
		for l in guessed:
			if l not in word:
				p += l #add the incorrect guessed letters
		p += ')'
		return p

	@commands.command()
	async def hangman(self, ctx):
		"""Play hangman with the bot."""
		if ctx.guild is None: #default vars in pms
			fp = str(bundled_data_path(self) / 'words.txt')
			doEdit = False #cant delete messages in pms
		else: #server specific vars
			fp = await self.config.guild(ctx.guild).fp()
			doEdit = await self.config.guild(ctx.guild).doEdit()
		try:
			f = open(fp)
		except FileNotFoundError:
			await ctx.send('Your wordlist was not found, using the default wordlist.')
			f = open(str(bundled_data_path(self) / 'words.txt'))
		wordlist = [line.strip().lower() for line in f]
		word = wordlist[randint(0,len(wordlist)-1)] #pick and format random word
		guessed = ''
		fails = 0
		game = True
		err = 0
		boardmsg = None
		check = lambda m: (
			m.channel == ctx.message.channel 
			and m.author == ctx.message.author 
			and len(m.content) == 1 
			and m.content.lower() in 'abcdefghijklmnopqrstuvwxyz'
		)
		while game:
			p = self._get_message(word, guessed)
			p = f'```{self.man[fails]}\n{p}```'
			if err == 1:
				p += 'You already guessed that letter.\n'
			if boardmsg is None or not doEdit:
				boardmsg = await ctx.send(p+'Guess:')
			else:
				await boardmsg.edit(content=str(p+'Guess:'))
			try:
				umsg = await self.bot.wait_for('message', check=check, timeout=60)
			except asyncio.TimeoutError:
				return await ctx.send(
					f'Canceling selection. You took too long.\nThe word was {word}.'
				)
			t = umsg.content.lower()
			if doEdit:
				await asyncio.sleep(.2)
				try:
					await umsg.delete()
				except (discord.errors.Forbidden, discord.errors.NotFound):
					pass
			if t in guessed:
				err = 1
				continue
			err = 0
			guessed += t
			if t not in word:
				fails += 1
				if fails == 6: #too many fails
					p = self._get_message(word, guessed)
					p = f'```{self.man[fails]}\n{p}```Game Over\nThe word was {word}.'
					if doEdit:
						await boardmsg.edit(content=p)
					else:
						await ctx.send(p)
					game = False
					continue
			#guessed entire word
			if not (set('abcdefghijklmnopqrstuvwxyz') & set(word)) - set(guessed):
				p = self._get_message(word, guessed)
				p = f'```{self.man[fails]}\n{p}```You win!\nThe word was {word}.'
				if doEdit:
					await boardmsg.edit(content=p)
				else:
					await ctx.send(p)
				game = False
	
	@commands.guild_only()
	@checks.guildowner()
	@commands.group()
	async def hangmanset(self, ctx):
		"""Config options for hangman."""
		pass
	
	@hangmanset.group(invoke_without_command=True)
	async def wordlist(self, ctx, value: str):
		"""
		Change the wordlist used.
		
		Extra wordlists can be put in the data folder.
		Wordlists are a .txt file with every new line being a new word.
		This value is server specific.
		"""
		wordlists = [p.resolve() for p in cog_data_path(self).glob("*.txt")]
		try:
			fp = next(p for p in wordlists if p.stem == value)
			await self.config.guild(ctx.guild).fp.set(str(fp))
			await ctx.send(f'The wordlist is now set to `{value}`.')
		except StopIteration:
			await ctx.send(f'Wordlist `{value}` not found.')
	
	@wordlist.command()
	async def default(self, ctx):
		"""Set the wordlist to the default list."""
		fp = str(bundled_data_path(self) / 'words.txt')
		await self.config.guild(ctx.guild).fp.set(fp)
		await ctx.send('The wordlist is now set to the default list.')

	@wordlist.command()
	async def list(self, ctx):
		"""List available wordlists."""
		wordlists = [p.resolve().stem for p in cog_data_path(self).glob("*.txt")]
		if wordlists == []:
			return await ctx.send('You do not have any wordlists.')
		msg = '\n'.join(wordlists).strip()
		await ctx.send(f'Available wordlists:```\n{msg}```')

	@wordlist.command()
	async def current(self, ctx):
		"""Show the current wordlist."""
		v = await self.config.guild(ctx.guild).fp()
		if str(v) == str(bundled_data_path(self) / 'words.txt'):
			await ctx.send('The wordlist is set to the default list.')
		else:
			await ctx.send(f'The wordlist is set to `{str(v)[str(v).find("Hangman")+8:-4]}`.')
	
	@hangmanset.command()
	async def edit(self, ctx, value: bool=None):
		"""
		Set if hangman messages should be one edited message or many individual messages.
		
		Defaults to True.
		This value is server specific.
		"""
		if value is None:
			v = await self.config.guild(ctx.guild).doEdit()
			if v:
				await ctx.send('Games are currently being played on a single, edited message.')
			else:
				await ctx.send('Games are currently being played on multiple messages.')
		else:
			await self.config.guild(ctx.guild).doEdit.set(value)
			if value:
				await ctx.send('Games will now be played on a single, edited message.')
			else:
				await ctx.send('Games will now be played on multiple messages.')

	async def red_delete_data_for_user(self, **kwargs):
		"""Nothing to delete."""
		return
