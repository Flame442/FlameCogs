import random


class BattleshipAI():
	"""
	AI opponent for Battleship.
	
	Params:
	Optional[name] = str, The name for this AI.
	"""
	def __init__(self, name=None):
		if name is None:
			name = '[AI]'
		self.display_name = name
		self.mention = self.display_name
		self.id = None
	
	async def send(self, *args, **kwargs):
		"""Absorbs attempts to DM what would normally be a human player."""
		pass
	
	def place(self, board, length):
		"""Decides where to place ships."""
		options = self._get_possible_ships(board, length)
		if not options:
			raise RuntimeError('There does not appear to be any valid location to place a ship.')
		return random.choice(options)
		
	def shoot(self, board, ship_status):
		"""Picks an optimal place to shoot."""
		options = []
		min_len = [2, 3, 3, 4, 5][ship_status[::-1].index(None)]
		max_len = [5, 4, 3, 3, 2][ship_status.index(None)]
		#Replace all of the dead ship positions with misses to avoid attempting to finish the ship
		for ship_num, cords in enumerate(ship_status):
			if not cords:
				continue
			ship_len = [5, 4, 3, 3, 2][ship_num]
			idx = cords[0] + (cords[1] * 10)
			d = cords[2]
			if d == 'r':
				for n in range(ship_len):
					if board[idx + n] != 2:
						raise RuntimeError('Inconsistency in board and ship_status.')
					board[idx + n] = 1
			else:
				for n in range(ship_len):
					if board[idx + (n * 10)] != 2:
						raise RuntimeError('Inconsistency in board and ship_status.')
					board[idx + (n * 10)] = 1
		#Get all of the possible ship positions with the remaining spaces
		possible_ships = self._get_possible_ships(board, min_len)
		#If there are any hits left, attempt to find the rest of the ship
		if 2 in board:
			#Try to move in a straight line with other hits
			best = 0
			for length in range(min_len, max_len + 1):
				if length == 2: #2 length ships will not produce a line
					continue
				ships = self._get_possible_ships(board, length)
				for cords in ships:
					idx = self._cord_to_index(cords)
					if cords[2] == 'r':
						index = lambda i: idx + i
					else:
						index = lambda i: idx + (i * 10)
					hits_in_ship = 0
					for n in range(length):
						if board[index(n)] == 2:
							hits_in_ship += 1
					if hits_in_ship > 1 and hits_in_ship != length:
						if best == hits_in_ship:
							options.append((idx, cords[2], length))
						elif best < hits_in_ship:
							best = hits_in_ship
							options = [(idx, cords[2], length)]
				if options:
					break
			if options:
				maybe_ship = random.choice(options)
				options = []
				if maybe_ship[1] == 'r':
					index = lambda i: maybe_ship[0] + i
				else:
					index = lambda i: maybe_ship[0] + (i * 10)
				for n in range(maybe_ship[2]):
					if board[index(n)] == 0:
						options.append(self._index_to_cord(index(n)))
			#If no lines exist (or existing lines do not allow for extension), attempt a random spot next to a hit.
			else:
				hit_indexes = []
				for idx, n in enumerate(board):
					if n == 2:
						hit_indexes.append(idx)
				for idx in hit_indexes:
					if idx + 1 <= 99 and board[idx + 1] == 0:
						options.append(self._index_to_cord(idx + 1))
					if idx - 1 >= 0 and board[idx - 1] == 0:
						options.append(self._index_to_cord(idx - 1))
					if idx + 10 <= 99 and board[idx + 10] == 0:
						options.append(self._index_to_cord(idx + 10))
					if idx - 10 >= 0 and board[idx - 10] == 0:
						options.append(self._index_to_cord(idx - 10))		
		#Otherwise, attack the best possible spot
		else:
			best = len(possible_ships)
			for idx in range(100):
				if board[idx] != 0:
					continue
				test_board = board[:] #copy the board
				test_board[idx] = 1
				num_remaining = len(self._get_possible_ships(test_board, min_len))
				if best == num_remaining:
					options.append(self._index_to_cord(idx))
				elif best > num_remaining:
					best = num_remaining
					options = [self._index_to_cord(idx)]
		if not options:
			raise RuntimeError('There does not appear to be any valid location to shoot.')
		return random.choice(options)
		
	@staticmethod
	def _index_to_cord(idx):
		"""Converts a board index to its string representation."""
		lets = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J']
		return lets[idx % 10] + str(idx // 10)
		
	@staticmethod
	def _cord_to_index(cord):
		"""Converts a string cord to its board index."""
		letnum = {'a': 0, 'b': 1, 'c': 2, 'd': 3, 'e': 4, 'f': 5, 'g': 6, 'h': 7, 'i': 8, 'j': 9}
		x = letnum[cord[0].lower()]
		y = int(cord[1])
		return (y * 10) + x
	
	def _get_possible_ships(self, board, length):
		"""Find all of the possible ship positions remaining for ships of a specific length."""
		locations = []
		for idx in range(100):
			canR = True
			canD = True
			if 10 - length < idx % 10:
				canR = False
			for n in range(length):
				if idx + n > 99 or board[idx + n] in (1, 3):
					canR = False
				if idx + (n * 10) > 99 or board[idx + (n * 10)] in (1, 3):
					canD = False
			cord = self._index_to_cord(idx)
			if canR:
				locations.append(cord + 'r')
			if canD:
				locations.append(cord + 'd')
		return locations
