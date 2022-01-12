from .constants import HOUSEPRICE, PRICEBUY, PROPGROUPS, RENTPRICE, RRPRICE, MORTGAGEPRICE, TENMORTGAGEPRICE
from copy import deepcopy
import random


class MonopolyAI():
	"""
	AI opponent for Monopoly.
	
	Params:
	me = int, The player number of this AI
	Optional[name] = str, The name for this AI.
	"""
	def __init__(self, me, name=None):
		if name is None:
			name = '[AI]'
		self.display_name = name
		self.mention = name
		self.me = me
		self.cache = []
	
	def _get_min_safe(self, game, config):
		"""Uses the most expensive space that could be landed on to determine how much to save."""
		high = 0
		
		#TAX
		high = max(high, config['incomeValue'])
		high = max(high, config['luxuryValue'])
		
		#RAILROADS
		store = {}
		for p in (5, 15, 25, 35):
			if game.ownedby[p] not in (-1, self.me):
				if game.ownedby[p] in store:
					store[game.ownedby[p]] += 1
				else:
					store[game.ownedby[p]] = 1
		if store:
			high = max(high, RRPRICE[max(store.values())])
		
		#UTILS
		if game.ownedby[12] == game.ownedby[28] and game.ownedby[12] not in (-1, self.me):
			high = max(high, 120)
		elif game.ownedby[12] not in (-1, self.me) or game.ownedby[28] not in (-1, self.me):
			high = max(high, 48)
		
		#PROPS
		for group in PROPGROUPS.values():
			monopoly = (
				all(game.ownedby[p] == game.ownedby[group[0]] for p in group)
				and game.ownedby[group[0]] not in (-1, self.me)
			)
			for prop in group:
				if game.ownedby[prop] in (-1, self.me):
					continue
				if game.numhouse[prop] == 0 and monopoly:
					high = max(high, 2 * RENTPRICE[prop * 6])
				else:
					high = max(high, RENTPRICE[prop * 6 + game.numhouse[prop]])
		#The function below has a max of 1000 at high=2000
		if high >= 2000:
			return 1000
		return int(high - (.00025 * (high ** 2)))
	
	@staticmethod
	def _subset_sum(options, goal, allow_above):
		"""
		Params:
		options = Dict[int, int], maps a choice to the number of times it can be used.
		goal = int, the number to reach.
		allow_above = bool, whether the closest number should be above or below the goal.
		
		Returns:
		Dict[int, int], maps a choice to the number of times it should be used, the sum of which has a sum closet possible to goal.
		"""
		best = []
		store = [[]]
		existing_sums = []
		while len(store) != 0:
			new_store = []
			for x in store:
				for option in options:
					#do not try to use an option more times than allowed
					if x.count(option) == options[option]:
						continue
					hold = deepcopy(x)
					hold.append(option)
					#an equal-value list already exists, space efficiency
					if sum(hold) in existing_sums:
						continue
					#if this is exactly the goal, exit and return, this is what we want
					if sum(hold) == goal:
						result = {}
						for i in hold:
							result[i] = result.get(i, 0) + 1
						return result
					if allow_above:
						if sum(best) > goal:
							#already too large
							if sum(hold) > sum(best):
								continue
							#above the goal, below the current best
							if sum(hold) > goal:
								best = hold
							#do NOT save to new-store since the next ittr can only be greater (which is worse)
						else:
							#greater is always better
							if sum(hold) > sum(best):
								best = hold
							#only save if the next ittr has the potential to be better
							if sum(hold) < goal:
								new_store.append(hold)
					else:
						#do not surpass the goal
						if sum(hold) > goal:
							continue
						#this is better than the current best, save it incase an exact match does not exist
						if sum(hold) > sum(best):
							best = hold
						new_store.append(hold)
					existing_sums.append(sum(hold))
				store = new_store
		result = {}
		for i in best:
			result[i] = result.get(i, 0) + 1
		return result
	
	def _buy_houses(self, game, safe, config):
		"""Prepare the cache to buy houses."""
		max_spend = game.bal[self.me] - safe
		max_hotels = config['hotelLimit']
		max_houses = config['houseLimit']
		
		#properties with monopolies
		possible_colors = [
			all(game.ownedby[p] == self.me for p in group)
			and not any(game.ismortgaged[p] == 1 for p in group)
			for group in PROPGROUPS.values()
		]
		if not any(possible_colors):
			return False
		house_costs = {}
		to_subset_sum = {}
		n = -1
		pg = list(PROPGROUPS.values())
		for idx, possible in enumerate(possible_colors):
			if not possible:
				continue
			n += 1
			per = HOUSEPRICE[pg[idx][0]]
			count = min(max_spend // per, (len(pg[idx]) * 5) - sum(game.numhouse[p] for p in pg[idx]))
			if per not in house_costs:
				#cannot safely afford a house OR no house spots remain
				if count == 0:
					continue
				house_costs[per] = [[idx, n]]
				to_subset_sum[per] = count
			else:
				if count > to_subset_sum[per]:
					house_costs[per] = [idx]
					to_subset_sum[per] = count
				elif count == to_subset_sum[per]:
					house_costs[per].append(idx)
		subset_sum = self._subset_sum(to_subset_sum, max_spend, False)
		result = []
		# TODO: This new_numhouse var is used to ensure the bought houses/hotels
		#       does not exceed max_houses/max_hotels. It does so by canceling
		#       the AI attempting to buy houses at all if it would buy houses that
		#       exceed those values. It should be changed to instead only generate
		#       housing configurations that are under the house/hotel limits.
		new_numhouse = game.numhouse[:]
		#ittr over each house price that is getting houses
		for hc in subset_sum:
			#pick a random prop group from that price
			idx, n = random.choice(house_costs[hc])
			result.append(n)
			to_change = {}
			#repeat the number of houses this prop group is getting
			for _ in range(subset_sum[hc]):
				current_houses = [game.numhouse[p] for p in pg[idx]]
				for x in to_change:
					current_houses[x] = to_change[x]
				prop_id = current_houses.index(min(current_houses))
				if prop_id in to_change:
					#this *should not* happpen
					if to_change[prop_id] == 5:
						break
					to_change[prop_id] += 1
				else:
					to_change[prop_id] = game.numhouse[pg[idx][prop_id]] + 1
				new_numhouse[pg[idx][prop_id]] = to_change[prop_id]
			for x in to_change:
				result.append(x)
				result.append(to_change[x])
			result.append('c')
		if max_houses != -1 and sum(x for x in new_numhouse if x in (1, 2, 3, 4)) > max_houses:
			return False
		if max_hotels != -1 and sum(1 for x in new_numhouse if x == 5) > max_hotels:
			return False
		#no houses are able to be bought
		if not result:
			return False
		result.append('d')
		self.cache = result
		return 'h'
	
	def _sell_houses(self, game, safe):
		"""Prepare the cache to sell houses."""
		goal = safe - game.bal[self.me]
		#properties with monopolies
		possible_colors = [
			all(game.ownedby[p] == self.me for p in group)
			and not any(game.ismortgaged[p] for p in group)
			for group in PROPGROUPS.values()
		]
		if not any(possible_colors):
			return False
		house_costs = {}
		to_subset_sum = {}
		n = -1
		pg = list(PROPGROUPS.values())
		for idx, possible in enumerate(possible_colors):
			if not possible:
				continue
			n += 1
			per = HOUSEPRICE[pg[idx][0]] // 2
			count = sum(game.numhouse[p] for p in pg[idx])
			if per not in house_costs:
				#no houses in this group
				if count == 0:
					continue
				house_costs[per] = [[idx, n]]
				to_subset_sum[per] = count
			else:
				if count > to_subset_sum[per]:
					house_costs[per] = [idx]
					to_subset_sum[per] = count
				elif count == to_subset_sum[per]:
					house_costs[per].append(idx)
		subset_sum = self._subset_sum(to_subset_sum, goal, True)
		result = []
		#ittr over each house price that is getting houses
		for hc in subset_sum:
			#pick a random prop group from that price
			idx, n = random.choice(house_costs[hc])
			result.append(n)
			to_change = {}
			#repeat the number of houses this prop group is getting
			for _ in range(subset_sum[hc]):
				current_houses = [game.numhouse[p] for p in pg[idx]]
				for x in to_change:
					current_houses[x] = to_change[x]
				prop_id = current_houses.index(max(current_houses))
				if prop_id in to_change:
					#this *should not* happpen
					if to_change[prop_id] == 0:
						break
					to_change[prop_id] -= 1
				else:
					to_change[prop_id] = game.numhouse[pg[idx][prop_id]] - 1
			for x in to_change:
				result.append(x)
				result.append(to_change[x])
			result.append('c')
		#no houses are able to be sold
		if not result:
			return False
		result.append('d')
		self.cache = result
		return 'h'

	def _unmortgage(self, game, safe):
		"""Prepare the cache to unmortgage properties"""
		max_spend = game.bal[self.me] - safe
		#properties able to be mortgaged
		mortgageable = [
			a for a in range(40) if game.ownedby[a] == self.me and game.numhouse[a] <= 0
		]
		if not mortgageable:
			return False
		mortgage_value = {}
		to_subset_sum = {}
		for idx, prop in enumerate(mortgageable):
			#only already mortgaged props
			if game.ismortgaged[prop] != 1:
				continue
			per = TENMORTGAGEPRICE[prop]
			if per not in mortgage_value:
				mortgage_value[per] = [idx]
				to_subset_sum[per] = 1
			else:
				mortgage_value[per].append(idx)
				to_subset_sum[per] += 1
		subset_sum = self._subset_sum(to_subset_sum, max_spend, False)
		result = []
		#ittr over each price
		for price in subset_sum:
			#pick a random sample of properties from that price
			sample = random.sample(mortgage_value[price], subset_sum[price])
			for idx in sample:
				result.append(idx)
		#no props are able to be unmortgaged
		if not result:
			return False
		result.append('d')
		self.cache = result
		return 'm'

	def _mortgage(self, game, safe):
		"""Prepare the cache to mortgage properties"""
		goal = safe - game.bal[self.me]
		#properties able to be mortgaged
		mortgageable = [
			a for a in range(40) if game.ownedby[a] == self.me and game.numhouse[a] <= 0
		]
		if not mortgageable:
			return False
		mortgage_value = {}
		to_subset_sum = {}
		for idx, prop in enumerate(mortgageable):
			#only unmortgaged props
			if game.ismortgaged[prop] != 0:
				continue
			per = MORTGAGEPRICE[prop]
			if per not in mortgage_value:
				mortgage_value[per] = [idx]
				to_subset_sum[per] = 1
			else:
				mortgage_value[per].append(idx)
				to_subset_sum[per] += 1
		subset_sum = self._subset_sum(to_subset_sum, goal, True)
		result = []
		#ittr over each price
		for price in subset_sum:
			#pick a random sample of properties from that price
			sample = random.sample(mortgage_value[price], subset_sum[price])
			for idx in sample:
				result.append(idx)
		#no props are able to be unmortgaged
		if not result:
			return False
		result.append('d')
		self.cache = result
		return 'm'

	@staticmethod
	def _calc_prop_value(game, ownedby, player):
		"""Calculate the value of a player's properties for trading."""
		value = 0
		for prop in range(40):
			if ownedby[prop] == player:
				value += PRICEBUY[prop]
				if game.ismortgaged[prop]:
					value -= TENMORTGAGEPRICE[prop]
		for group in PROPGROUPS.values():
			if all(ownedby[p] == player for p in group):
				value += 1000
		return value
		
	def turn(self, game, config, choices):
		"""Take an action for a normal turn.""" 
		#if able to roll, roll
		if 'r' in choices:
			return 'r'
		safe = self._get_min_safe(game, config)
		#if the current balance is higher than safe, try to use money
		if game.bal[self.me] > safe:
			maybe_unmortgage = self._unmortgage(game, safe)
			if maybe_unmortgage:
				return maybe_unmortgage
			maybe_buy_houses = self._buy_houses(game, safe, config)
			if maybe_buy_houses:
				return maybe_buy_houses	
		#if the current balance is lower than 0, try to get money
		if game.bal[self.me] < 0:
			maybe_sell_houses = self._sell_houses(game, 0)
			if maybe_sell_houses:
				return maybe_sell_houses
			maybe_mortgage = self._mortgage(game, 0)
			if maybe_mortgage:
				return maybe_mortgage
		#otherwise, done/give up
		if 'd' in choices:
			return 'd'
		if 'g' in choices:
			return 'g'
		raise RuntimeError('One of "r", "d", or "g" should exist as a choice.')
	
	def jail_turn(self, game, config, choices):
		"""Take an action for a turn while in jail."""
		if 'r' in choices:
			return 'r'
		if 'g' in choices:
			return 'g'
		raise RuntimeError('One of "r" or "g" should exist as a choice.')
	
	def buy_prop(self, game, config, prop_id):
		"""Decide whether or not to buy a specific property."""
		if game.bal[self.me] - PRICEBUY[prop_id] < self._get_min_safe(game, config):
			return 'n'
		return 'y'
	
	#TODO: Incorperate this as part of the auction process
	def bid(self, game, config, prop_id):
		if game.bal[self.me] < self._get_min_safe(game, config):
			return None
		raise NotImplementedError
	
	def incoming_trade(self, game, them_id, incoming, outgoing):
		"""Decide whether to accept or deny an incoming trade."""
		value = 0
		#begin by basing the value on the money change
		value += incoming[0]
		value -= outgoing[0]
		#then factor in goojf cards at $50 per
		value += incoming[1] * 50
		value -= outgoing[1] * 50
		#and finally properties
		ownedby = game.ownedby.copy()
		me_delta = -1 * self._calc_prop_value(game, ownedby, self.me)
		them_delta = -1 * self._calc_prop_value(game, ownedby, them_id)
		for prop in incoming[2]:
			ownedby[prop] = self.me
		for prop in outgoing[2]:
			ownedby[prop] = them_id
		me_delta += self._calc_prop_value(game, ownedby, self.me)
		them_delta += self._calc_prop_value(game, ownedby, them_id)
		if me_delta > them_delta:
			value += me_delta
		else:
			value -= them_delta
		if value > -50:
			return 'y'
		return 'n'
	
	def grab_from_cache(self):
		return self.cache.pop(0)
	
	def to_save(self):
		return {'me': self.me, 'display_name': self.display_name}
	
	@classmethod
	def from_save(cls, save):
		return cls(save['me'], save['display_name'])
