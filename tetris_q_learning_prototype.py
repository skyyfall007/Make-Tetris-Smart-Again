#!/usr/bin/env python2
#-*- coding: utf-8 -*-

# NOTE FOR WINDOWS USERS:
# You can download a "exefied" version of this game at:
# http://hi-im.laria.me/progs/tetris_py_exefied.zip
# If a DLL is missing or something like this, write an E-Mail (me@laria.me)
# or leave a comment on this gist.

# Very simple tetris implementation
# 
# Control keys:
#       Down - Drop stone faster
# Left/Right - Move stone
#         Up - Rotate Stone clockwise
#     Escape - Quit game
#          P - Pause game
#     Return - Instant drop
#
# Have fun!

# Copyright (c) 2010 "Laria Carolin Chabowski"<me@laria.me>
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

from random import randrange as rand
import random
import math
import pygame, sys
import csv


#possible functions:
#get_board_state()
#move_to(x)
#update_q
#evaluate_actions

# The configuration
cell_size =	18
cols =		3
rows =		3
maxfps = 	30


colors = [
(0,   0,   0  ),
(255, 85,  85),
(100, 200, 115),
(120, 108, 245),
(255, 140, 50 ),
(50,  120, 52 ),
(146, 202, 73 ),
(150, 161, 218 ),
(35,  35,  35) # Helper color for background grid
]

#available actions for q-learning
actions = ['LEFT','RIGHT','RETURN']

# Define the shapes of the single parts
tetris_shapes = [
##	[[1, 1, 1],
##	 [0, 1, 0]],
##	
##	[[0, 2, 2],
##	 [2, 2, 0]],
##	
##	[[3, 3, 0],
##	 [0, 3, 3]],
##	
##	[[4, 0, 0],
##	 [4, 4, 4]],
##	
##	[[0, 0, 5],
##	 [5, 5, 5]],
##	
##	[[6, 6, 6, 6]],
	
	[[1]]
]

def rotate_clockwise(shape):
	return [ [ shape[y][x]
			for y in range(len(shape)) ]
		for x in range(len(shape[0]) - 1, -1, -1) ]

def check_collision(board, shape, offset):
	off_x, off_y = offset
	for cy, row in enumerate(shape):
		for cx, cell in enumerate(row):
			try:
				if cell and board[ cy + off_y ][ cx + off_x ]:
					return True
			except IndexError:
				return True
	return False

def remove_row(board, row):
	del board[row]
	return [[0 for i in range(cols)]] + board
	
def join_matrixes(mat1, mat2, mat2_off):
	off_x, off_y = mat2_off
	for cy, row in enumerate(mat2):
		for cx, val in enumerate(row):
			mat1[cy+off_y-1	][cx+off_x] += val
	return mat1

def new_board():
	board = [ [ 0 for x in range(cols) ]
			for y in range(rows) ]
	board += [[ 1 for x in range(cols)]]
	return board
#ML functions
#def get_action():
 #      return random.choice(actions)


class TetrisApp(object):
	def __init__(self):
		pygame.init()
		pygame.key.set_repeat(250,25)
		self.width = cell_size*(cols+6)
		self.height = cell_size*rows
		self.rlim = cell_size*cols
		self.bground_grid = [[ 8 if x%2==y%2 else 0 for x in range(cols)] for y in range(rows)]
		
		self.default_font =  pygame.font.Font(
			pygame.font.get_default_font(), 12)
		
		self.screen = pygame.display.set_mode((self.width, self.height))
		pygame.event.set_blocked(pygame.MOUSEMOTION) # We do not need
		                                             # mouse movement
		                                             # events, so we
		                                             # block them.
		self.next_stone = tetris_shapes[rand(len(tetris_shapes))]
		self.available_actions = []
		self.actions = []
		self.a_index = 0
		
		#Q-learning variables
		self.gamma = 0.8
		self.q_table = {}
		self.n_episodes = 10
		self.init_state = ""
		self.c_state = ""
		self.p_state = ""
		self.c_action = None 
		self.at_goal = False
		self.action_list = []
		self.reward = 0
		self.h_row_y = 0
		self.init_game()
		
	
	def new_stone(self):
		self.stone = self.next_stone[:]
		self.next_stone = tetris_shapes[rand(len(tetris_shapes))]
		self.stone_x = int(cols / 2 - len(self.stone[0])/2)
		self.stone_y = 0
		
		if check_collision(self.board,
		                   self.stone,
		                   (self.stone_x, self.stone_y)):
			self.gameover = True
			self.reward-=50
		#self.get_actions_available()
		#self.update_table()
	
	def init_game(self):
		self.board = new_board()
		self.new_stone()
		self.level = 1
		self.score = 0
		self.lines = 0
		self.running = True
		pygame.time.set_timer(pygame.USEREVENT+1, 1000)
	
	def disp_msg(self, msg, topleft):
		x,y = topleft
		for line in msg.splitlines():
			self.screen.blit(
				self.default_font.render(
					line,
					False,
					(255,255,255),
					(0,0,0)),
				(x,y))
			y+=14

	
	def center_msg(self, msg):
		for i, line in enumerate(msg.splitlines()):
			msg_image =  self.default_font.render(line, False,
				(255,255,255), (0,0,0))
		
			msgim_center_x, msgim_center_y = msg_image.get_size()
			msgim_center_x //= 2
			msgim_center_y //= 2
		
			self.screen.blit(msg_image, (
			  self.width // 2-msgim_center_x,
			  self.height // 2-msgim_center_y+i*22))
	
	def draw_matrix(self, matrix, offset):
		off_x, off_y  = offset
		for y, row in enumerate(matrix):
			for x, val in enumerate(row):
				if val:
					pygame.draw.rect(
						self.screen,
						colors[val],
						pygame.Rect(
							(off_x+x) *
							  cell_size,
							(off_y+y) *
							  cell_size, 
							cell_size,
							cell_size),0)
	
	def add_cl_lines(self, n):
		linescores = [0, 40, 100, 300, 1200]
		self.lines += n
		self.score += linescores[n] * self.level
		if self.lines >= self.level*6:
			self.level += 1
			newdelay = 1000-50*(self.level-1)
			newdelay = 100 if newdelay < 100 else newdelay
			pygame.time.set_timer(pygame.USEREVENT+1, newdelay)
	
	def move(self, delta_x):
		if not self.gameover and not self.paused:
			new_x = self.stone_x + delta_x
			if new_x < 0:
				new_x = 0
			if new_x > cols - len(self.stone[0]):
				new_x = cols - len(self.stone[0])
			if not check_collision(self.board,
			                       self.stone,
			                       (new_x, self.stone_y)):
				self.stone_x = new_x
	def quit(self):
		self.center_msg("Exiting...")
		pygame.display.update()
		sys.exit()
	
	def drop(self, manual):
		if not self.gameover and not self.paused:
			self.score += 1 if manual else 0
			self.stone_y += 1
			if check_collision(self.board,self.stone,(self.stone_x, self.stone_y)):
				self.board = join_matrixes(self.board,self.stone,(self.stone_x, self.stone_y))
				if self.h_row_y>self.stone_y:
					self.reward-=5
					self.h_row_y = self.stone_y
				else:
					self.reward+=5
				self.new_stone()
				cleared_rows = 0
				while True:
					for i, row in enumerate(self.board[:-1]):
						if 0 not in row:
							self.board = remove_row(
							  self.board, i)
							cleared_rows += 1
							#print("WINWIN")
							self.reward+=10
							self.h_row_y-=1
							break
					else:
						break
				self.add_cl_lines(cleared_rows)
				return True
		return False
	
	def insta_drop(self):
		if not self.gameover and not self.paused:
			while(not self.drop(True)):
				pass
	
	def rotate_stone(self):
		if not self.gameover and not self.paused:
			new_stone = rotate_clockwise(self.stone)
			if not check_collision(self.board,
			                       new_stone,
			                       (self.stone_x, self.stone_y)):
				self.stone = new_stone
	
	def toggle_pause(self):
		self.paused = not self.paused
	
	def start_game(self):
		if self.gameover:
			self.init_game()
			self.gameover = False
	
	def run(self):
		key_actions = {
			'ESCAPE':	self.quit,
			'LEFT':		lambda:self.move(-1),
			'RIGHT':	lambda:self.move(+1),
			'DOWN':		lambda:self.drop(True),
			'UP':		self.rotate_stone,
			'p':		self.toggle_pause,
			'SPACE':	self.start_game,
			'RETURN':	self.insta_drop
		}
		
		self.gameover = False
		self.paused = False
		
		dont_burn_my_cpu = pygame.time.Clock()
		while self.running:
			self.screen.fill((0,0,0))
			if self.gameover:
				self.get_actions_available()
				self.update_table()
				#print('LOST')
				self.center_msg("""Game Over!\nYour score: %d
Press space to continue""" % self.score)
				key_actions['SPACE']()
			else:
				
				if self.paused:
					self.center_msg("Paused")
				else:
					pygame.draw.line(self.screen,
						(255,255,255),
						(self.rlim+1, 0),
						(self.rlim+1, self.height-1))
					self.disp_msg("Next:", (
						self.rlim+cell_size,
						2))
					self.disp_msg("Score: %d\n\nLevel: %d\
\nLines: %d" % (self.score, self.level, self.lines),
						(self.rlim+cell_size, cell_size*5))
					self.draw_matrix(self.bground_grid, (0,0))
					self.draw_matrix(self.board, (0,0))
					self.draw_matrix(self.stone,
						(self.stone_x, self.stone_y))
					self.draw_matrix(self.next_stone,
						(cols+1,2))
			pygame.display.update()

                        #performs a random actions
			#self.ti-=1
			#if self.ti<=0:
			if self.a_index==len(self.actions):
				self.get_actions_available()
				self.update_table()
				#key_actions[get_action()]()
				self.choose_action()
				self.a_index = 0
				#print(self.actions)
			else:
                                #previous state is set before the final action
				self.p_state = str(self.board)+str(self.stone)
				key_actions[self.actions[self.a_index]]()
				#print(self.a_index])
				self.a_index+=1
				
				#print(actions)
				#self.ti=5
                                
			
			
			#print(self.available_actions)
			
			for event in pygame.event.get():
				if event.type == pygame.USEREVENT+1:
					self.drop(False)
				elif event.type == pygame.QUIT:
					self.running = False
					self.save_q_table()
					self.quit()
				#elif event.type == pygame.KEYDOWN:
				#	for key in key_actions:
				#		if event.key == eval("pygame.K_"
				#		+key):
				#			key_actions[key]()
					
			dont_burn_my_cpu.tick(maxfps)
     #get available actions
	#fills list of available actions with a tuple: (orientation,x_offset)
        #check collision based off offsets from pieces positions on board. offsets based on number of cols
        #ex: for i in range(#offsets): offset =(i+1)-x_pos # if !check_col(board,shape,offset): 
        #def move_to(x_pos,board):
	def get_actions_available(self):
		self.available_actions = []
		for i in range(cols):
			offset = (i)-self.stone_x
			test_shape = self.stone
			#check orientation with position of x
			for i2 in range(4):
				if not check_collision(self.board, test_shape, (self.stone_x+offset,self.stone_y)):
					self.available_actions.append((i2,offset+self.stone_x))
				test_shape = rotate_clockwise(test_shape)
				
	#using the list of available actions
	#the system composes the actions in an orderlist starting with rotation and then position 
	def choose_action(self):
		self.actions = []
		if len(self.available_actions)>0:
			rotation, position = random.choice(self.available_actions)
			#print(rotation, ' ', offset)
			#for i in range(rotation):
			#	self.actions.append('UP')
			#print(offset)
			dir = 0
			self.c_action = (rotation,position)
			while position !=self.stone_x:
				if position<self.stone_x:
					dir = 1
					self.actions.append('LEFT')
				elif position >self.stone_x:
					dir = -1
					self.actions.append('RIGHT')
				position+=dir
			self.actions.append('RETURN')
			
			#print(self.actions)
	def update_table(self):
		if self.c_action !=None:
			self.c_state = str(self.board)+str(self.stone)
			p_state = None
			max_reward = 0
			q0 = 0
			for a in self.available_actions:
				f_state = (str(self.board)+str(self.stone),a)
				if  f_state in self.q_table:
					r = self.q_table[f_state]
					if max_reward <r:
						max_reward = r
			
			if (self.p_state,self.c_action) in self.q_table:
				q0 = self.q_table[(self.p_state,self.c_action)]
			else:
				q0 = 0

			self.q_table[(self.p_state,self.c_action)] =q0+ 0.1*(self.reward+self.gamma*max_reward - q0)
			self.reward = 0
			
	def save_q_table(self):
		with open('q_table_values.csv', 'w', newline='') as f:
			writer = csv.writer(f,delimiter=",")
			writer.writerow(['board state']+['rotation']+['x_pos']+['reward'])
			for key,value in self.q_table.items():
				state, action = key
				rotation, x_pos = action
				writer.writerow([str(state),str(rotation),str(x_pos),str(value)])
				#print(key, " ", value)
			#print(len(self.q_table))
			
			
			
if __name__ == '__main__':
	App = TetrisApp()
	App.run()

