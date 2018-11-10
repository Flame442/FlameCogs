import discord, re
from redbot.core import commands

class WordStats(commands.Cog):
	"""Tracks commonly written words"""
	def __init__(self, bot):
		self.bot = bot
		
	@commands.guild_only()
	@commands.command()
	async def wordstats(self, message, user: discord.Member=None):
		"""Prints the most commonly written words"""
		wordlist = [] #list of all words
		worddic = {} #count of each word
		if user == None:
			mention = 'the server'
		else:
			mention = user.mention
		'''Make wordlist'''
		with open('all.txt') as f:
			for line in f:
				lineid, words = line.split('|') 
				words = words.split(' ')
				if user == None or int(lineid.strip()) == user.id:
					for word in words:
						word = word.strip()
						if word:
							wordlist.append(word)
		'''Count/sort wordlist'''
		num = len(wordlist)
		for word in wordlist:
			try:
				worddic[word] += 1
			except:
				worddic[word] = 1
		order = list(reversed(sorted(worddic,key= lambda w: worddic[w])))
		'''Print result & write to file'''
		result = ''
		smallresult = ''
		n = 0
		for word in order:
			if n < 30:
				smallresult +=str(worddic[word])+' '+str(word)+'\n'
				n += 1
			result += str(worddic[word])+' '+str(word)+'\n'
		await message.send('Out of '+str(num)+' words, the 30 most common words that '+mention+' has said are:\n```'+smallresult.rstrip()+'```')
		with open('result.txt', 'w') as f:
			f.write(result)

	async def run(self, t):
		"""Passively records all message contents"""
		if t.author.id != self.bot.user.id:
			message = t.content.lower()
			with open('all.txt','a') as f:
				f.write(str(t.author.id)+' | '+str(re.sub(r'[^a-zA-Z ]','',message))+'\n')
