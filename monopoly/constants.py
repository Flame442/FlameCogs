TILENAME = [
	'Go', 'Mediterranean Avenue',
	'Community Chest', 'Baltic Avenue',
	'Income Tax', 'Reading Railroad',
	'Oriental Avenue', 'Chance',
	'Vermont Avenue', 'Connecticut Avenue',
	'Jail', 'St. Charles Place',
	'Electric Company', 'States Avenue',
	'Virginia Avenue', 'Pennsylvania Railroad',
	'St. James Place', 'Community Chest',
	'Tennessee Avenue', 'New York Avenue',
	'Free Parking', 'Kentucky Avenue',
	'Chance', 'Indiana Avenue',
	'Illinois Avenue', 'B&O Railroad',
	'Atlantic Avenue', 'Ventnor Avenue',
	'Water Works', 'Marvin Gardens',
	'Go To Jail', 'Pacific Avenue',
	'North Carolina Avenue', 'Community Chest',
	'Pennsylvania Avenue', 'Short Line',
	'Chance', 'Park Place',
	'Luxury Tax', 'Boardwalk'
]
PRICEBUY = [
	-1, 60, -1, 60, -1,
	200, 100, -1, 100, 120,
	-1, 140, 150, 140, 160,
	200, 180, -1, 180, 200,
	-1, 220, -1, 220, 240,
	200, 260, 260, 150, 280,
	-1, 300, 300, -1, 320,
	200, -1, 350, -1, 400
]
RENTPRICE = [
	-1, -1, -1, -1, -1, -1,
	2, 10, 30, 90, 160, 250,
	-1, -1, -1, -1, -1, -1,
	4, 20, 60, 180, 360, 450,
	-1, -1, -1, -1, -1, -1,
	-1, -1, -1, -1, -1, -1,
	6, 30, 90, 270, 400, 550,
	-1, -1, -1, -1, -1, -1,
	6, 30, 90, 270, 400, 550,
	8, 40, 100, 300, 450, 600,
	-1, -1, -1, -1, -1, -1,
	10, 50, 150, 450, 625, 750,
	-1, -1, -1, -1, -1, -1,
	10, 50, 150, 450, 625, 750,
	12, 60, 180, 500, 700, 900,
	-1, -1, -1, -1, -1, -1,
	14, 70, 200, 550, 750, 950,
	-1, -1, -1, -1, -1, -1,
	14, 70, 200, 550, 750, 950,
	16, 80, 220, 600, 800, 1000,
	-1, -1, -1, -1, -1, -1,
	18, 90, 250, 700, 875, 1050,
	-1, -1, -1, -1, -1, -1,
	10, 90, 250, 700, 875, 1050,
	20, 100, 300, 750, 925, 1100,
	-1, -1, -1, -1, -1, -1,
	22, 110, 330, 800, 975, 1150,
	22, 110, 330, 800, 975, 1150,
	-1, -1, -1, -1, -1, -1,
	24, 120, 360, 850, 1025, 1200,
	-1, -1, -1, -1, -1, -1,
	26, 130, 390, 900, 1100, 1275,
	26, 130, 390, 900, 1100, 1275,
	-1, -1, -1, -1, -1, -1,
	28, 150, 450, 1000, 1200, 1400,
	-1, -1, -1, -1, -1, -1,
	-1, -1, -1, -1, -1, -1,
	35, 175, 500, 1100, 1300, 1500,
	-1, -1, -1, -1, -1, -1,
	50, 200, 600, 1400, 1700, 2000
]
RRPRICE = [0, 25, 50, 100, 200]
CCNAME = [
	'Advance to Go (Collect $200)',
	'Bank error in your favor\nCollect $200',
	'Doctor\'s fee\nPay $50',
	'From sale of stock you get $50',
	'Get Out of Jail Free',
	'Go to Jail\nGo directly to jail\nDo not pass Go\nDo not collect $200',
	'Grand Opera Night\nCollect $50 from every player for opening night seats',
	'Holiday Fund matures\nReceive $100',
	'Income tax refund\nCollect $20',
	'It is your birthday\nCollect $10',
	'Life insurance matures\nCollect $100',
	'Pay hospital fees of $100',
	'Pay school fees of $150',
	'Receive $25 consultancy fee',
	'You are assessed for street repairs\n$40 per house\n$115 per hotel',
	'You have won second prize in a beauty contest\nCollect $10',
	'You inherit $100'
]
CHANCENAME = [
	'Advance to Go (Collect $200)',
	'Advance to Illinois Ave\nIf you pass Go, collect $200.',
	'Advance to St. Charles Place\nIf you pass Go, collect $200',
	(
		'Advance token to nearest Utility. If unowned, you may buy it from the Bank. '
		'If owned, throw dice and pay owner a total ten times the amount thrown.'
	), (
		'Advance token to the nearest Railroad and pay owner twice the rental to which '
		'he/she is otherwise entitled. If Railroad is unowned, you may buy it from the Bank.'
	),
	'Bank pays you dividend of $50',
	'Get Out of Jail Free',
	'Go Back 3 Spaces',
	'Go to Jail\nGo directly to Jail\nDo not pass Go\nDo not collect $200',
	'Make general repairs on all your property\nFor each house pay $25\nFor each hotel $100',
	'Pay poor tax of $15',
	'Take a trip to Reading Railroad\nIf you pass Go, collect $200',
	'Take a walk on the Boardwalk\nAdvance token to Boardwalk',
	'You have been elected Chairman of the Board\nPay each player $50',
	'Your building and loan matures\nCollect $150',
	'You have won a crossword competition\nCollect $100'
]
MORTGAGEPRICE = [
	-1, 30, -1, 30, -1,
	100, 50, -1, 50, 60,
	-1, 70, 75, 70, 80,
	100, 90, -1, 90, 100,
	-1, 110, -1, 110, 120,
	100, 130, 130, 75, 140,
	-1, 150, 150, -1, 160,
	100, -1, 175, -1, 200
]
TENMORTGAGEPRICE = [
	-1, 33, -1, 33, -1,
	110, 55, -1, 55, 66,
	-1, 77, 83, 77, 88,
	110, 99, -1, 99, 110,
	-1, 121, -1, 121, 132,
	110, 143, 143, 83, 154,
	-1, 165, 165, -1, 176,
	110, -1, 188, -1, 220
]
HOUSEPRICE = [
	-1, 50, -1, 50, -1, 
	-1, 50, -1, 50, 50,
	-1, 100, -1, 100, 100,
	-1, 100, -1, 100, 100,
	-1, 150, -1, 150, 150,
	-1, 150, 150, -1, 150,
	-1, 200, 200, -1, 200,
	-1, -1, 200, -1, 200
]
PROPGROUPS = {
	'Brown': [1, 3], 'Light Blue': [6, 8, 9],
	'Pink': [11, 13, 14], 'Orange': [16, 18, 19],
	'Red': [21, 23, 24], 'Yellow': [26, 27, 29],
	'Green': [31, 32, 34], 'Dark Blue': [37, 39]
}
PROPCOLORS = {
	1: 'Brown', 3: 'Brown',
	6: 'Light Blue', 8: 'Light Blue', 9: 'Light Blue',
	11: 'Pink', 13: 'Pink', 14: 'Pink',
	16: 'Orange', 18: 'Orange', 19: 'Orange',
	21: 'Red', 23: 'Red', 24: 'Red',
	26: 'Yellow', 27: 'Yellow', 29: 'Yellow',
	31: 'Green', 32: 'Green', 34: 'Green',
	37: 'Dark Blue', 39: 'Dark Blue',
	5: 'Railroad', 15: 'Railroad', 25: 'Railroad', 35: 'Railroad', 
	12: 'Utility', 28: 'Utility'
}
