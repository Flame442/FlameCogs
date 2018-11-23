import discord
from redbot.core import commands
from random import randint
from redbot.core.data_manager import bundled_data_path

class Hangman(commands.Cog):
	"""Play hangman with the bot"""
	def __init__(self, bot):
		self.bot = bot
		self.man = ['\
    ___    \n\
   |   |   \n\
   |   O   \n\
   |       \n\
   |       \n\
   |       \n\
   |       \n\
  ','\
    ___    \n\
   |   |   \n\
   |   O   \n\
   |   |   \n\
   |   |   \n\
   |       \n\
   |       \n\
  ','\
    ___    \n\
   |   |   \n\
   |   O   \n\
   |  \|   \n\
   |   |   \n\
   |       \n\
   |       \n\
  ','\
    ___    \n\
   |   |   \n\
   |   O   \n\
   |  \|/  \n\
   |   |   \n\
   |       \n\
   |       \n\
   ','\
    ___    \n\
   |   |   \n\
   |   O   \n\
   |  \|/  \n\
   |   |   \n\
   |  /    \n\
   |       \n\
   ','\
    ___    \n\
   |   |   \n\
   |   O   \n\
   |  \|/  \n\
   |   |   \n\
   |  / \  \n\
   |       \n\
   ','\
    ___    \n\
   |   |   \n\
   |   X   \n\
   |  \|/  \n\
   |   |   \n\
   |  / \  \n\
   |       \n\
   ']

	@commands.command()
	async def hangman(self, ctx):
		"""Play hangman with the bot"""
		fp = bundled_data_path(self) / 'words.txt'
		x = open(fp) #default wordlist
		wordlist = []
		for line in x:
			wordlist.append(line.strip().lower())
		word = wordlist[randint(0,len(wordlist))] #pick and format random word
		guessed = ''
		fails = 0
		end = 0
		starter = ctx.message
		err = 0
		boardmsg = None
		while end == 0:
			p = ''
			for l in word:
				if l not in 'abcdefghijklmnopqrstuvwxyz': #auto print non letter characters
					p += l+' '
				elif l in guessed: #print already guessed characters
					p += l+' '
				else:
					p += '_ ' 
			p += '    ('
			for l in guessed:
				if l not in word:
					p += l
			p += ')'
			p = '```'+self.man[fails]+'\n'+p+'```'
			if err == 1:
				p += 'You already guessed that letter.\n'
			elif err == 2:
				p += 'Pick a letter.\n'
			check = lambda m: m.channel == starter.channel and m.author == starter.author
			if boardmsg == None:
				boardmsg = await ctx.send(p+'Guess:')
			else:
				await boardmsg.edit(content=str(p+'Guess:'))
			try:
				umsg = await self.bot.wait_for('message', check=check, timeout=60)
			except:
				return await ctx.send('Canceling selection. You took too long.\nThe word was '+word+'.')
			t = umsg.content[0].lower()
			await umsg.delete()
			if t in guessed:
				err = 1
			elif t not in 'abcdefghijklmnopqrstuvwxyz':
				err = 2
			else:
				err = 0
				if t not in word:
					fails += 1
					if fails == 6: #too many fails
						await boardmsg.edit(content=str('```'+self.man[6]+'```Game Over\nThe word was '+word+'.'))
						end = 1
				guessed += t
				if word.strip(guessed) == word.strip('abcdefghijklmnopqrstuvwxyz'): #guessed entire word
					await boardmsg.edit(content=str('```'+self.man[fails]+'```You win!\nThe word was '+word+'.'))
					end = 1
