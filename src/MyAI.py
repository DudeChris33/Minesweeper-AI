# ==============================CS-171==================================
# FILE:			MyAI.py
#
# AUTHOR: 		Chris Cyr, Daniel Geyfman
#
# DESCRIPTION:	This file contains the MyAI class. You will implement your
#				agent in this file. You will write the 'getAction' function,
#				the constructor, and any additional helper functions.
#
# NOTES: 		- MyAI inherits from the abstract AI class in AI.py.
# ==============================CS-171==================================

from AI import AI
from Action import Action
import random
import time
from collections import defaultdict

OKBLUE = '\033[94m'
OKCYAN = '\033[96m'
OKGREEN = '\033[92m'
WARNING = '\033[93m'
FAIL = '\033[91m'
ENDC = '\033[0m'

class MyAI( AI ):
	def __init__(self, rowDimension, colDimension, totalMines, startX, startY):
		self.rowDimension = colDimension
		self.colDimension = rowDimension
		self.xMax = self.rowDimension-1
		self.yMax = self.colDimension-1
		self.totalMines = totalMines
		self.minesLeft = totalMines
		self.totalCells = self.rowDimension*self.colDimension

		self.lastX = startX
		self.lastY = startY

		self.safe = []
		self.visited = set()
		self.hints = {}
		self.realHints = {}
		self.flagged = set()

		self.greatReset = False

		self.startTime = time.time()
		self.timeLimit = 300
		
		# with open("stats.txt", "r") as f:
		# 	contents = f.readlines()
		# if not contents:
		# 	with open("stats.txt", "w") as f:
		# 		f.write("0\n")
		# 		f.write("0\n")
		# with open("stats.txt", "r") as f:
		# 	contents = f.readlines()
		# 	self.index = int(contents[1].rstrip())+1
		# 	contents[1] = f"{self.index}\n"
		# with open("stats.txt", "w") as f:
		# 	f.writelines(contents)
		# with open("stats.txt", "a") as f:
		# 	output = f"{self.index} failed\n"
		# 	f.write(output)

		# self.flagFlagged = set()


	def getAction(self, number: int):# -> "Action Object":
		if time.time() - self.startTime > self.timeLimit:
			print(f"{FAIL}TIMEOUT{ENDC}")
			# with open("stats.txt", "r") as f:
			# 	contents = f.readlines()
			# 	contents[0] = f"{int(contents[0].rstrip()) + 1}\n"
			# 	contents.pop(-1)
			# with open("stats.txt", "w") as f:
			# 	f.writelines(contents)
			return Action(AI.Action.LEAVE)

		if number != -1:
			lastMove = (self.lastX, self.lastY)
			if lastMove not in self.visited:
				self.visited.add(lastMove)
			if lastMove not in self.hints:
				self.hints[lastMove] = number
			self.updateMoves(self.lastX, self.lastY)
			for n in self.getNeighbors(self.lastX, self.lastY):
				if n in self.hints:
					self.updateMoves(*n)
		# # # print(f"self.flagged {len(self.flagged)}: {self.flagged}")
		# # print(f"self.safe {len(self.safe)}: {self.safe}")

		# if self.flagged:
		# 	for (fx, fy) in self.flagged:
		# 		if (fx, fy) not in self.flagFlagged:
		# 			self.flagFlagged.add((fx, fy))
		# 			self.lastX, self.lastY = fx, fy
		# 			return Action(AI.Action.FLAG, fx, fy)

		if self.safe and len(self.visited) + self.totalMines < self.totalCells:
			x, y = self.safe.pop(0)
			neighbors = self.getNeighbors(x, y)
			numUnvisitedNeighbors = len(self.getUnvisitedNeighbors(neighbors))
			while self.safe and (x, y) in self.visited and numUnvisitedNeighbors == 0:
				x, y = self.safe.pop(0)
				neighbors = self.getNeighbors(x, y)
				numUnvisitedNeighbors = len(self.getUnvisitedNeighbors(neighbors))
			if (x, y) in self.visited and numUnvisitedNeighbors > 0:
				self.lastX, self.lastY = x, y
				return self.getAction(self.hints[(x, y)])
			elif (x, y) not in self.visited:
				self.greatReset = True
				self.lastX, self.lastY = x, y
				return Action(AI.Action.UNCOVER, self.lastX, self.lastY)

		# print(f"{OKGREEN}FINDING PATTERNS{ENDC}")
		if self.findPatterns():
			return self.getAction(-1)

		# print(f"{OKCYAN}GREAT RESET{ENDC}")
		if self.greatReset:
			self.greatResetter()
			return self.getAction(-1)

		if len(self.visited) + self.totalMines < self.totalCells:
			self.makeRealHintsTable()
			# print(f"{OKBLUE}ENTROPY{ENDC}")
			if self.entropySolver():
				return self.getAction(-1)
			# print(f"{WARNING}CSP SOLVER{ENDC}")
			if self.cspSolver():
				return self.getAction(-1)
			# print(f"{FAIL}SELECTING RANDOMLY{ENDC}")
			if self.randomPicker():
				return self.getAction(-1)

		# print(f"{OKGREEN}INTENTIONALLY LEAVING{ENDC}")
		# with open("stats.txt", "r") as f:
		# 	contents = f.readlines()
		# 	contents[0] = f"{int(contents[0].rstrip()) + 1}\n"
		# 	contents.pop(-1)
		# with open("stats.txt", "w") as f:
		# 	f.writelines(contents)
		return Action(AI.Action.LEAVE)

	def updateMoves(self, x: int, y: int):
		neighbors = self.getNeighbors(x, y)
		unvisitedNeighbors = self.getUnvisitedNeighbors(neighbors)
		flaggedCount = self.countFlagged(neighbors)

		if unvisitedNeighbors:
			if self.hints[(x, y)] == 0:
				for n in unvisitedNeighbors:
					if n not in self.safe:
						self.safe.append(n)

			elif self.hints[(x, y)] == flaggedCount:
				for n in unvisitedNeighbors:
					if n not in self.safe:
						self.safe.append(n)

			elif self.hints[(x, y)] == len(unvisitedNeighbors) + flaggedCount:
				for b in unvisitedNeighbors:
					self.placeFlag(b)
					for c in self.getNeighbors(*b):
						if c in self.visited and c not in self.safe:
							self.safe.append(c)

	def getNeighbors(self, x: int, y: int) -> list:
		neighbors = []
		for dx, dy in [(-1, 1), (0, 1), (1, 1), (-1, 0), (1, 0), (-1, -1), (0, -1), (1, -1)]:
			if 0 <= x+dx < self.rowDimension and 0 <= y+dy < self.colDimension:
				neighbors.append((x + dx, y + dy))
		return neighbors

	def getUnvisitedNeighbors(self, neighbors: list) -> list:
		return [n for n in neighbors if self.unvisited(n)]
	
	def unvisited(self, a: tuple) -> bool:
		return a not in self.visited and a not in self.flagged

	def countFlagged(self, neighbors: list) -> int:
		return sum(1 for n in neighbors if n in self.flagged)

	def makeRealHintsTable(self):
		self.realHints.clear()
		for a in self.hints.keys():
			if self.hints[a] == 0:
				self.realHints[a] = 0
			else:
				neighbors = self.getNeighbors(*a)
				self.realHints[a] = self.hints[a] - self.countFlagged(neighbors)
	
	def updateRealHintsTable(self, a: tuple):
		neighborsA = self.getNeighbors(*a)
		if a in self.hints:
			if self.hints[a] == 0:
				self.realHints[a] = 0
			else:
				self.realHints[a] = self.hints[a] - self.countFlagged(neighborsA)
		for b in neighborsA:
			if b in self.hints:
				if self.hints[b] == 0:
					self.realHints[b] = 0
				else:
					neighborsB = self.getNeighbors(*b)
					self.realHints[b] = self.hints[b] - self.countFlagged(neighborsB)

	def placeFlag(self, a: tuple):
		if a not in self.flagged:
			self.flagged.add(a)
			self.minesLeft -= 1
		if a in self.safe:
			self.safe.remove(a)
		neighbors = self.getNeighbors(*a)
		for b in neighbors:
			if b in self.visited and b not in self.safe:
				self.safe.append(b)
		self.updateRealHintsTable(a)

	def findPatterns(self) -> bool:
		self.makeRealHintsTable()
		found = False
		if self.pattern_1_2_1():
			found = True
		if self.pattern_1_2_2_1():
			found = True
		if self.hole_1():
			found = True
		if self.hole_3():
			found = True
		# if not found:
		# 	if self.pattern_1_3_1_c():
		# 		found = True
		# 	if self.pattern_2_2_2_c():
		# 		found = True
		return found

	def pattern_1_2_1(self) -> bool:
		def pattern_1_2_1_h(box: list) -> bool:
			if all(self.unvisited(b) and b not in self.safe for b in box):
				# # print(f"1-2-1 found {box[0]} mine")
				self.placeFlag(box[0])
				# # print(f"1-2-1 found {box[2]} mine")
				self.placeFlag(box[2])
				return True

		found = False
		for (x, y) in self.realHints.keys():
			realHintM = self.realHints[(x, y)]
			l, d, u, r = (x-1, y), (x, y-1), (x, y+1), (x+1, y)
			if realHintM == 2 and sum(1 for h in [l, d, u, r] if h in self.realHints and self.realHints[h] == 1) == 2:
				realHintL = self.realHints[l] if l in self.realHints else -1
				realHintD = self.realHints[d] if d in self.realHints else -1
				realHintU = self.realHints[u] if u in self.realHints else -1
				realHintR = self.realHints[r] if r in self.realHints else -1
				ld, lu, rd, ru = (x-1, y-1), (x-1, y+1), (x+1, y-1), (x+1, y+1)
				if realHintL == 1 and realHintR == 1:	# left/right to search up/down
					if y < self.yMax and (y == 0 or all(a in self.visited or a in self.flagged for a in [ld, d, rd])):	# check up
						temp = pattern_1_2_1_h([lu, u, ru])
						if not found: found = temp
					if y > 0 and (y == self.yMax or all(a in self.visited or a in self.flagged for a in [lu, u, ru])):	# check down
						temp = pattern_1_2_1_h([ld, d, rd])
						if not found: found = temp
				if realHintD == 1 and realHintU == 1:
					if x < self.xMax and (x == 0 or all(a in self.visited or a in self.flagged for a in [ld, l, lu])):	# check right
						temp = pattern_1_2_1_h([rd, r, ru])
						if not found: found = temp
					if x > 0 and (x == self.xMax or all(a in self.visited or a in self.flagged for a in [rd, r, ru])):	# check left
						temp = pattern_1_2_1_h([ld, l, lu])
						if not found: found = temp
		return found

	def pattern_1_2_2_1(self) -> bool:
		def pattern_1_2_2_1_h(box: list) -> bool:
			if all(self.unvisited(b) and b not in self.safe for b in box):
				# # print(f"1-2-2-1 found {box[1]} mine")
				self.placeFlag(box[1])
				# # print(f"1-2-2-1 found {box[2]} mine")
				self.placeFlag(box[2])
				return True

		found = False
		for (x, y) in self.realHints.keys():
			realHintM = self.realHints[(x, y)]
			l, d, u, r = (x-1, y), (x, y-1), (x, y+1), (x+1, y)
			ll, dd, uu, rr = (x-2, y), (x, y-2), (x, y+2), (x+2, y)
			if realHintM == 2:
				realHintL = self.realHints[l] if l in self.realHints else -1
				realHintD = self.realHints[d] if d in self.realHints else -1
				realHintU = self.realHints[u] if u in self.realHints else -1
				realHintUU = self.realHints[uu] if uu in self.realHints else -1
				realHintR = self.realHints[r] if r in self.realHints else -1
				realHintRR = self.realHints[rr] if rr in self.realHints else -1
				ld, lu, rd, ru = (x-1, y-1), (x-1, y+1), (x+1, y-1), (x+1, y+1)
				llu, lld, ldd, luu = (x-2, y+1), (x-2, y-1), (x-1, y-2), (x-1, y+2)
				rdd, ruu, rru, rrd = (x+1, y-2), (x+1, y+2), (x+2, y+1), (x+2, y-1)
				if realHintL == 1 and realHintR == 2 and realHintRR == 1:	# left/right to search up/down
					if y < self.yMax and (y == 0 or all(a in self.visited or a in self.flagged for a in [ld, d, rd, rrd])):	# check up:	# check up
						temp = pattern_1_2_2_1_h([lu, u, ru, rru])
						if not found: found = temp
					if y > 0 and (y == self.yMax or all(a in self.visited or a in self.flagged for a in [lu, u, ru, rru])):			# check down
						temp = pattern_1_2_2_1_h([ld, d, rd, rrd])
						if not found: found = temp
				if realHintD == 1 and realHintU == 2 and realHintUU == 1:	# up/down to search left/right
					if x < self.xMax and (x == 0 or all(a in self.visited or a in self.flagged for a in [ld, l, lu, luu])):	# check right
						temp = pattern_1_2_2_1_h([rd, r, ru, ruu])
						if not found: found = temp
					if x > 0 and (x == self.xMax or all(a in self.visited or a in self.flagged for a in [rd, r, ru, ruu])):			# check left
						temp = pattern_1_2_2_1_h([ld, l, lu, luu])
						if not found: found = temp
		return found

	def hole_1(self) -> bool:
		found = False
		for a in self.realHints.keys():
			realHintA = self.realHints[a]
			if realHintA > 0:
				neighborsA = self.getNeighbors(*a)
				for b in neighborsA:
					if b in self.realHints:
						realHintA = self.realHints[a]
						realHintB = self.realHints[b]
						if realHintB > 0:
							neighborsB = self.getNeighbors(*b)
							unvisitedNeighborsA = set(self.getUnvisitedNeighbors(neighborsA))
							unvisitedNeighborsB = set(self.getUnvisitedNeighbors(neighborsB))
							unvisitedNeighborsBmA = unvisitedNeighborsB - unvisitedNeighborsA
							if unvisitedNeighborsBmA and unvisitedNeighborsA <= unvisitedNeighborsB:
								if realHintB == realHintA:
									for c in unvisitedNeighborsBmA:
										if c not in self.safe:
											# # print(f"hole 1 found {c} safe")
											self.safe.append(c)
											found = True
								elif realHintB == realHintA + len(unvisitedNeighborsBmA):
									for c in unvisitedNeighborsBmA:
										# # print(f"hole 1 found {c} mine")
										self.placeFlag(c)
										found = True
									unvisitedNeighborsAmB = unvisitedNeighborsA - unvisitedNeighborsB
									for c in unvisitedNeighborsAmB:
										if c not in self.safe:
											# # print(f"hole 1 found {c} safe")
											self.safe.append(c)
											found = True
		return found

	def hole_3(self) -> bool:
		found = False
		for a in self.realHints.keys():
			realHintA = self.realHints[a]
			if realHintA > 0:
				neighborsA = self.getNeighbors(*a)
				unvisitedNeighborsA = set(self.getUnvisitedNeighbors(neighborsA))
				for (bx, by) in unvisitedNeighborsA:
					neighborsB = self.getNeighbors(bx, by)
					for c in neighborsB:
						if c in self.realHints:
							realHintA = self.realHints[a]
							realHintC = self.realHints[c]
							if realHintC > 0:
								neighborsC = self.getNeighbors(*c)
								unvisitedNeighborsC = set(self.getUnvisitedNeighbors(neighborsC))
								unvisitedNeighborsCmA = unvisitedNeighborsC - unvisitedNeighborsA
								if unvisitedNeighborsCmA and unvisitedNeighborsA <= unvisitedNeighborsC:
									if realHintC == realHintA:
										for d in unvisitedNeighborsCmA:
											if d not in self.safe:
												# # print(f"hole 3 found {d} safe")
												self.safe.append(d)
												found = True
									elif realHintC == realHintA + len(unvisitedNeighborsCmA):
										# unvisitedNeighborsAmC = unvisitedNeighborsA - unvisitedNeighborsC
										for c in unvisitedNeighborsCmA:
											# # print(f"hole 3 found {c} mine")
											self.placeFlag(c)
											found = True
										# for c in unvisitedNeighborsAmC:
										# 	if c not in self.safe:
										# 		# # print(f"hole 3 found {c} safe")
										# 		self.safe.append(c)
										# 		found = True
		return found

	# todo triangle 3, 4, 5

	# def pattern_1_3_1_c(self) -> bool:
	# 	def pattern_1_3_1_c_h(box: list, anchor: tuple, corner: tuple, hooks: list) -> bool:
	# 		if all(self.unvisited(a) for a in box) and (anchor in self.visited or anchor in self.flagged):
	# 			# # print(f"pattern 1-3-1-c found {corner} mine")
	# 			self.placeFlag(corner)
	# 			for n in hooks:
	# 				if n not in self.safe:
	# 					# # print(f"pattern 1-3-1-c found {n} safe")
	# 					self.safe.append(n)
	# 			return True

	# 	found = False
	# 	for (x, y) in self.realHints.keys():
	# 		if 0 < x < self.xMax and 0 < y < self.yMax:
	# 			realHintM = self.realHints[(x, y)]
	# 			l, d, u, r = (x-1, y), (x, y-1), (x, y+1), (x+1, y)
	# 			if realHintM == 3 and sum(1 for h in [l, d, u, r] if h in self.realHints and self.realHints[h] == 1) == 2:
	# 				realHintL = self.realHints[l] if l in self.realHints else -1
	# 				realHintD = self.realHints[d] if d in self.realHints else -1
	# 				realHintU = self.realHints[u] if u in self.realHints else -1
	# 				realHintR = self.realHints[r] if r in self.realHints else -1
	# 				ld, lu, rd, ru = (x-1, y-1), (x-1, y+1), (x+1, y-1), (x+1, y+1)
	# 				llu, lld, ldd, luu = (x-2, y+1), (x-2, y-1), (x-1, y-2), (x-1, y+2)
	# 				rdd, ruu, rru, rrd = (x+1, y-2), (x+1, y+2), (x+2, y+1), (x+2, y-1)
	# 				if realHintL == 1 and realHintD == 1 and realHintU == -1 and realHintR == -1 and x > 1 and y > 1:	# LD to look RU
	# 					temp = pattern_1_3_1_c_h([lu, u, ru, r, rd], ld, ru, [llu, rdd])
	# 					if not found: found = temp
	# 				elif realHintL == 1 and realHintD == -1 and realHintU == 1 and realHintR == -1 and x > 1 and y < self.yMax-1:	# LU to look RD
	# 					temp = pattern_1_3_1_c_h([ld, d, rd, r, ru], lu, rd, [lld, ruu])
	# 					if not found: found = temp
	# 				elif realHintL == -1 and realHintD == 1 and realHintU == -1 and realHintR == 1 and x < self.xMax-1 and y > 1:	# RD to look LU
	# 					temp = pattern_1_3_1_c_h([ld, l, lu, u, ru], rd, lu, [ldd, rru])
	# 					if not found: found = temp
	# 				elif realHintL == -1 and realHintD == -1 and realHintU == 1 and realHintR == 1 and x < self.xMax-1 and y < self.yMax-1:	# RU to look LD
	# 					temp = pattern_1_3_1_c_h([lu, l, ld, d, rd], ru, ld, [luu, rrd])
	# 					if not found: found = temp
	# 	return found

	# def pattern_2_2_2_c(self) -> bool:
		# def pattern_2_2_2_c_h(box: list, anchor: tuple, corner: tuple, hooks: list) -> bool:
		# 	if all(self.unvisited(a) for a in box) and (anchor in self.visited or anchor in self.flagged):
		# 		if corner not in self.safe:
		# 			# # print(f"pattern 2-2-2-c found {corner} safe")
		# 			self.safe.append(corner)
		# 		for n in hooks:
		# 			# # print(f"pattern 2-2-2-c found {n} mine")
		# 			self.placeFlag(n)
		# 		return True

		# found = False
		# for (x, y) in self.realHints.keys():
		# 	if 0 < x < self.xMax and 0 < y < self.yMax:
		# 		realHintM = self.realHints[(x, y)]
		# 		l, d, u, r = (x-1, y), (x, y-1), (x, y+1), (x+1, y)
		# 		if realHintM == 2 and sum(1 for h in [l, d, u, r] if h in self.realHints and self.realHints[h] == 2) == 2:
		# 			realHintL = self.realHints[l] if l in self.realHints else -1
		# 			realHintD = self.realHints[d] if d in self.realHints else -1
		# 			realHintU = self.realHints[u] if u in self.realHints else -1
		# 			realHintR = self.realHints[r] if r in self.realHints else -1
		# 			ld, lu, rd, ru = (x-1, y-1), (x-1, y+1), (x+1, y-1), (x+1, y+1)
		# 			llu, lld, ldd, luu = (x-2, y+1), (x-2, y-1), (x-1, y-2), (x-1, y+2)
		# 			rdd, ruu, rru, rrd = (x+1, y-2), (x+1, y+2), (x+2, y+1), (x+2, y-1)
		# 			if realHintL == 2 and realHintD == 2 and realHintU == -1 and realHintR == -1 and x > 1 and y > 1:	# LD to look RU
		# 				temp = pattern_2_2_2_c_h([lu, u, ru, r, rd], ld, ru, [llu, rdd])
		# 				if not found: found = temp
		# 			elif realHintL == 2 and realHintD == -1 and realHintU == 2 and realHintR == -1 and x > 1 and y < self.yMax-1:	# LU to look RD
		# 				temp = pattern_2_2_2_c_h([ld, d, rd, r, ru], lu, rd, [lld, ruu])
		# 				if not found: found = temp
		# 			elif realHintL == -1 and realHintD == 2 and realHintU == -1 and realHintR == 2 and x < self.xMax-1 and y > 1:	# RD to look LU
		# 				temp = pattern_2_2_2_c_h([ld, l, lu, u, ru], rd, lu, [ldd, rru])
		# 				if not found: found = temp
		# 			elif realHintL == -1 and realHintD == -1 and realHintU == 2 and realHintR == 2 and x < self.xMax-1 and y < self.yMax-1:	# RU to look LD
		# 				temp = pattern_2_2_2_c_h([lu, l, ld, d, rd], ru, ld, [luu, rrd])
		# 				if not found: found = temp
		# return found

	def greatResetter(self):
		self.greatReset = False
		for (x, y) in self.hints.keys():
			neighbors = self.getNeighbors(x, y)
			numUnvisitedNeighbors = len(self.getUnvisitedNeighbors(neighbors))
			if self.hints[(x, y)] > 0 and numUnvisitedNeighbors > 0:
				self.updateMoves(x, y)
	
	def entropySolver(self) -> bool:
		"""
		STAGE 1: Constraints
		"""
		unvisitedCoordsIndex = {}
		unvisitedIndexCoords = {}
		index = 0
		for x in range(self.rowDimension):
			for y in range(self.colDimension):
				if self.unvisited((x, y)):# and any(n in self.visited and self.realHints[n] > 0 for n in self.getNeighbors(x, y)):
					unvisitedCoordsIndex[(x, y)] = index
					unvisitedIndexCoords[index] = (x, y)
					index += 1
		n = index
		constraints = []
		for x in range(self.rowDimension):
			for y in range(self.colDimension):
				if (x, y) in self.realHints:
					c_j = self.realHints[(x, y)]
					omega_j = [unvisitedCoordsIndex[n] for n in self.getNeighbors(x, y) if n in unvisitedCoordsIndex]
					if c_j and omega_j:
						constraints.append((c_j, omega_j))

		"""
		STAGE 2: Entropy
		"""
		p = [1.0] * n	# prob mine
		q = [1.0] * n	# prob no mine

		iter = 0
		itercap = 1000
		while iter < itercap:
			iter += 1

			prev_p = p[:]
			prev_q = q[:]

			for c_j, omega_j in constraints:
				sum_p = sum(p[i] for i in omega_j)
				if sum_p > 0 and sum_p != c_j:
					factor_p = c_j / sum_p
					for i in omega_j:
						p[i] *= factor_p

				sum_q = sum(q[i] for i in omega_j)
				complement_cj = len(omega_j) - c_j
				if sum_q > 0 and sum_q != complement_cj:
					factor_q = complement_cj / sum_q
					for i in omega_j:
						q[i] *= factor_q
				elif sum_q == 0:
					if complement_cj == 0:
						for i in omega_j:
							q[i] = 0	# No mines are possible here
					else:
						for i in omega_j:
							q[i] = 1.0 / len(omega_j)	# Distribute probabilities equally

			# Renormalize probabilities to ensure p + q = 1
			for i in range(n):
				normalization_factor = p[i] + q[i]
				if normalization_factor == 0:
					normalization_factor = 1
				p[i] /= normalization_factor
				q[i] /= normalization_factor

			# Check for convergence
			if all(abs(p[i] - prev_p[i]) < 1e-4 for i in range(n)) and all(abs(q[i] - prev_q[i]) < 1e-4 for i in range(n)):
				break
		if iter >= itercap:
			print(f"{WARNING}Too many iterations{ENDC}")
			return False

		# # print(f"p: {[i for i in p if i < 0.5]}")
		# # print(f"q: {[i for i in q if i < 0.5]}")

		"""
		STAGE 3: Find best
		"""
		index = 0
		bestCost = 0.4
		bestCells = []
		for i in range(len(p)):
			if p[i] < bestCost and i in unvisitedIndexCoords:
				bestCost = p[i]
				bestCells.clear()
				bestCells.append(unvisitedIndexCoords[i])
			elif p[i] == bestCost and i in unvisitedIndexCoords:
				bestCells.append(unvisitedIndexCoords[i])

		worstCost = 0.1
		worstCells = []
		for i in range(len(q)):
			if q[i] < worstCost and i in unvisitedIndexCoords:
				worstCost = q[i]
				worstCells.clear()
				worstCells.append(unvisitedIndexCoords[i])
			elif q[i] == worstCost and i in unvisitedIndexCoords:
				worstCells.append(unvisitedIndexCoords[i])
		
		"""
		STAGE 4: Visit
		"""
		# # print(f"bestCells: {bestCells}, {bestCost}")
		# # print(f"worstCells: {worstCells}, {worstCost}")
		if bestCells and bestCost <= worstCost:
			(x, y) = random.choice(bestCells)
			# bestCells.sort()
			# (x, y) = bestCells.pop(0)
		
			# # print(f"(x, y): ({x}, {y})")
			self.safe.append((x, y))
			neighbors = self.getNeighbors(x, y)
			for (nx, ny) in neighbors:
				if (nx, ny) in self.visited and (nx, ny) not in self.safe:
					self.safe.append((nx, ny))
				neighborNeighbors = self.getNeighbors(nx, ny)
				for (nnx, nny) in neighborNeighbors:
					if (nnx, nny) in self.visited and (nnx, nny) not in self.safe:
						self.safe.append((nnx, nny))
			return True
		elif worstCells:
			(x, y) = random.choice(worstCells)
			# worstCells.sort()
			# (x, y) = worstCells.pop(0)
		
			# # print(f"(x, y): ({x}, {y})")
			self.placeFlag((x, y))
			neighbors = self.getNeighbors(x, y)
			for (nx, ny) in neighbors:
				if (nx, ny) in self.visited and (nx, ny) not in self.safe:
					self.safe.append((nx, ny))
				neighborNeighbors = self.getNeighbors(nx, ny)
				for (nnx, nny) in neighborNeighbors:
					if (nnx, nny) in self.visited and (nnx, nny) not in self.safe:
						self.safe.append((nnx, nny))
			return True
		else:
			return False
	
	# def getInfoGain(self, x: int, y: int) -> int:
	# 	count = 0
	# 	box = [
	# 		(-2,  2), (-1,  2), ( 0,  2), ( 1,  2), ( 2,  2),
	# 		(-2,  1), (-1,  1), ( 0,  1), ( 1,  1), ( 2,  1),
	# 		(-2,  0), (-1,  0),           ( 1,  0), ( 2,  0),
	# 		(-2, -1), (-1, -1), ( 0, -1), ( 1, -1), ( 2, -1),
	# 		(-2, -2), (-1, -2), ( 0, -2), ( 1, -2), ( 2, -2),
	# 	]
	# 	for (dx, dy) in box:
	# 		if (x+dx, y+dy) in self.visited:
	# 			count += 1
	# 	return count
	
	def cspSolver(self) -> bool:
		cellsLeft = self.totalCells - len(self.visited) - len(self.flagged)
		bestCost = (0.5 + self.minesLeft / cellsLeft) / 2
		bestCells = []
		for x in range(self.rowDimension):
			for y in range(self.colDimension):
				if self.unvisited((x, y)):
					neighbors = self.getNeighbors(x, y)
					if any(n in self.visited for n in neighbors):
						cost = 0
						visitedNeighbors = [n for n in neighbors if n in self.visited]
						for n in visitedNeighbors:
							if n in self.realHints and self.realHints[n] > 0:
								neighborNeighbors = self.getNeighbors(*n)
								numUnvisitedNeighborNeighbors = len(self.getUnvisitedNeighbors(neighborNeighbors))
								neighborRealHint = self.realHints[n]
								cost += (neighborRealHint / numUnvisitedNeighborNeighbors)
						numVisitedNeighbors = len(visitedNeighbors)
						cost += (self.minesLeft / cellsLeft)
						cost /= (numVisitedNeighbors + 1)
						cost -= (numVisitedNeighbors / 1000)
						
						if cost > 0:
							if cost == bestCost:
								bestCells.append((x, y))
							elif cost < bestCost:
								bestCost = cost
								bestCells.clear()
								bestCells.append((x, y))

		if bestCells:
			# # print(f"bestCells: {bestCells}, {bestCost}")
			(x, y) = random.choice(bestCells)
			# bestCells.sort()
			# (x, y) = bestCells.pop(0)
			
			# # print(f"(x, y): ({x}, {y})")
			self.safe.append((x, y))
			neighbors = self.getNeighbors(x, y)
			for (nx, ny) in neighbors:
				if (nx, ny) in self.visited and (nx, ny) not in self.safe:
					self.safe.append((nx, ny))
				neighborNeighbors = self.getNeighbors(nx, ny)
				for (nnx, nny) in neighborNeighbors:
					if (nnx, nny) in self.visited and (nnx, nny) not in self.safe:
						self.safe.append((nnx, nny))
			return True
		else:
			return False
	
	def randomPicker(self) -> bool:
		bestCells = []
		for x in range(self.rowDimension):
			for y in range(self.colDimension):
				if self.unvisited((x, y)) and not any(n in self.visited for n in self.getNeighbors(x, y)):
					bestCells.append((x, y))
		if bestCells:
			(x, y) = random.choice(bestCells)
			# bestCells.sort()
			# (x, y) = bestCells.pop(0)
			
			# # print(f"(x, y): ({x}, {y})")
			self.safe.append((x, y))
			neighbors = self.getNeighbors(x, y)
			for (nx, ny) in neighbors:
				if (nx, ny) in self.visited and (nx, ny) not in self.safe:
					self.safe.append((nx, ny))
				neighborNeighbors = self.getNeighbors(nx, ny)
				for (nnx, nny) in neighborNeighbors:
					if (nnx, nny) in self.visited and (nnx, nny) not in self.safe:
						self.safe.append((nnx, nny))
			return True
		else:
			return False