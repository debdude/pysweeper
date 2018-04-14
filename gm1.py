import sys, termios, tty
import term
import random 
from collections import deque

cx, cy = 0, 0
ox, oy = 0, 0
world = None

OK = 1000
BOOM = 999
WIN = 1001

syms = ['·', '1', '2', '3', '4', '5', '6', '7', '8', # #of mines around
        "#", '¤' , "?", # unknown, flag, QM
        '*', '*', '^', '*']  # actually mine, mine reveal, candidate

UNKNOWN = 9 # default tile
FLAG = 10 #flagged bomb
QM = 11 #question mark
MINE = 12

CANDIDATE = 14

class World():
    def __init__(self, sx, sy, nmines = 0):
        assert sy + sy < 500, 'too big'
        self.sx = sx
        self.sy = sy
        self.nmines = 0
        # self.world = [[x*y%4 for y in range(sy)] for x in range(sx)]
        self.map = [[UNKNOWN for y in range(sy)] for x in range(sx)]
        self.mines = [[0 for y in range(sy)] for x in range(sx)]
        self.place_mines(nmines)
        self.q = deque()

        # self.bombs = []

    def draw(self):
        term.clear()
        term.pos(1, 1)
        for y in range(self.sy):
            print(''.join([syms[ self.map[x][y] ] 
                for x in range(self.sx)]))


    def mines_marked(self):
        c = 0 
        for x in range(self.sx):
            for y in range(self.sy):
                c += 1 if self.map[x][y] == FLAG else 0
        return c


    def reveal(self):
        term.clear()
        term.pos(1, 1)

        for y in range(self.sy):
            print(''.join([syms[ self.map[x][y] + self.mines[x][y]*3   ] 
                for x in range(self.sx)]))
        # self.draw()


    def ismine(self, x, y):
        return self.mines[x][y]

    def putmine(self, x, y):
        self.mines[x][y] = 1 


    def toggle(self, x, y):
        state = self.map[x][y] 
        if state == UNKNOWN:
            self.map[x][y] = FLAG  
        elif state == FLAG:
            self.map[x][y] = QM 
        elif state == QM:
            self.map[x][y] = UNKNOWN 
        return OK


    def place_mines(self, num):
        assert num <= self.sx*self.sy, 'too many mines!'
        for _ in range(num):
            x = random.choice(range(self.sx))
            y = random.choice(range(self.sy))
            while self.mines[x][y]: #not empty already, re-pick
                x = random.choice(range(self.sx))
                y = random.choice(range(self.sy))
            self.putmine(x, y)
            self.nmines += 1

    def get_count(self, x, y):
        return len([_ for xx, yy in self.get_neighbors_u(x, y) 
            if self.mines[xx][yy]] )

    def open(self, x, y):  #try to open a cell
        if self.mines[x][y]:
            return BOOM

        if self.map[x][y] < UNKNOWN: #already marked
            return OK   

        # nmines = self.get_count(x, y) 
        # self.map[x][y] = nmines

        # if nmines == 0:
        #     self.q.append([x, y])

        # while len(self.q):
        #     x, y = self.q.pop()
        #     nmines = self.get_count(x, y) 
        #     self.map[x][y] = nmines
        #     if nmines == 0:
        #         for xx, yy in self.get_neighbors_uq(x, y):                
        #             self.q.append([xx, yy])
        qs = set()

        # if nmines == 0:
        qs.add(x*1000 + y)

        while len(qs):
            xy = qs.pop()
            x, y = xy//1000, xy % 1000
            nmines = self.get_count(x, y) 
            self.map[x][y] = nmines
            if nmines == 0:
                for xx, yy in self.get_neighbors_u(x, y):                
                    qs.add(xx*1000+yy)

        return WIN if self.iswin() else OK






    def get_neighbors(self, x, y):
        minx = max(0, x-1)
        miny = max(0, y-1)
        maxx = min(x+2, self.sx)
        maxy = min(y+2, self.sy)
        # print(minx, miny,'->', maxx, maxy)
        nb = [[xx,yy] for xx in range(minx, maxx) 
            for yy in range(miny, maxy) if [xx,yy]!=[x,y] ]
        return nb

    def get_neighbors_u(self, x, y):
        return [[xx,yy] for xx, yy 
            in self.get_neighbors(x,y) if self.map[xx][yy] >= UNKNOWN]

    def get_neighbors_uq(self, x, y):
        return [[xx,yy] for xx, yy 
            in self.get_neighbors(x,y) 
            if (self.map[xx][yy] == UNKNOWN and [xx,yy] not in self.q)]


    def iswin(self):
        closed = [0 for y in range(self.sy) for x in range(self.sx) 
            if self.map[x][y] >= UNKNOWN]
        return True if len(closed)==self.nmines else False






def getch():   # define non-Windows version
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch


def escape():
    print('escape')

def cpos():
    global ox, oy
    term.pos(cy + 1, cx +1)
    term.write(syms[ world.map[cx][cy] ])
    term.pos(cy + 1, cx +1)

    # term.pos(oy+1, ox+1)
    # term.write(syms[ world.map[ox][oy] ])

    # term.pos(cy + 1, cx +1)
    # term.write(syms[ world.map[cx][cy] ], 
    #     term.blue, term.bold)

    # ox, oy = cx, cy

def up():
    global cx, cy
    cy = max(cy-1, 0)
    cpos()
    return OK

def down():
    global cx, cy
    cy = min(cy+1, world.sy -1 )
    cpos()
    return OK

def left():
    global cx, cy
    cx = max(cx-1, 0)
    cpos()
    return OK

def right():
    global cx, cy
    cx = min(cx+1, world.sx - 1)
    cpos()
    return OK

def enter():
    global cx, cy, redraw
    redraw = True
    return world.open(cx, cy) 

def toggle():
    global cx, cy
    world.toggle(cx, cy)
    cpos()
    return OK 




def status(text = ''):
    term.pos(3 + world.sy, 1)
    print('POS:', cx, cy, 
            '  |   MINES: %d / %d   |  '%(world.nmines - world.mines_marked(), 
            world.nmines),  
            text)
    cpos()


def gameloop(x = 80, y=30, mm = 40):
    global cx, cy, redraw
    key = None
    cx, cy = 0, 0

    actions = {
        # '': escape,
        'w': up,
        's': down,
        'a': left,
        'd': right,
        '\r': enter,
        ' ': toggle
    }

    global world
    world = World(x, y, mm)
    world.draw()
    status('start!')
    cpos()

    result = OK
    redraw = False
    key = ''

    while key != '\03' and result == OK:
        key = getch()
        if key in actions:
            result = actions[key]()
        if redraw: 
            world.draw()
            redraw = False
            cpos()
        status('your move')

    if result == BOOM:
        status('BOOM YOU LOSE!')
        print('YOU LOSE')
    elif result == WIN:
        status('YAY YOU WIN')
        print('YOU WIN WELL DONE!')




def main():
    global world
    world = World(80, 30, 20)
    world.draw()
    # gameloop()


def maptest():
    global w
    random.seed(99)
    w = World(25, 10)
    w.place_mines(10)
    w.draw()
    # print('...................')
    w.reveal()
    w.toggle(2,3)
    w.toggle(5,5)
    w.toggle(5,5)
    w.toggle(7,7)
    w.toggle(7,7)
    w.toggle(7,7)
    w.toggle(2,9)
    w.toggle(6,9)
    w.toggle(6,9)
    w.draw()
    w.reveal()
    w.open(1,3)
    w.open(1,4)
    w.open(1,5)
    w.open(1,6)
    w.draw()
    res = w.open(5, 3)    
    print(res == BOOM)
    w.reveal()

if __name__ == "__main__":
    main()