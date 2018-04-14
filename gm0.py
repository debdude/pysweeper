import sys, termios, tty
import term
import random 

UNKNOWN = 0
CLEAR = 1
FLAG = 2
QM = 3
MINE = 4
MINEBLOWN = 5
MINEFLAG = 6
MINEQM = 7

OK = 0
BOOM = 1

w = None
x, y = 0, 0
maxx, maxy = 20, 10

#unknown, empty, flag, question
syms = ["#", '·', 'B' , "?", '*', '*', '+', '*'] 
syms_rev = ['·', '·', '-' , '·', '*', '*', '+', '#'] 

class World():
    def __init__(self, sx, sy):
        self.sx = sx
        self.sy = sy
        self.mines = 0
        # self.world = [[x*y%4 for y in range(sy)] for x in range(sx)]
        self.world = [[UNKNOWN for y in range(sy)] for x in range(sx)]
        # self.bombs = []

    def draw(self):
        # term.clear()
        # term.pos(1, 1)
        print('MINES LEFT: %d / %d'%(self.mines - self.mines_marked(), self.mines))
        for y in range(self.sy):
            print(''.join([syms[ self.world[x][y] % 4 ] 
                for x in range(self.sx)]))

    def mines_marked(self):
        c = 0 
        for x in range(self.sx):
            for y in range(self.sy):
                c += 1 if self.world[x][y] % 4 == FLAG else 0
        return c

    def reveal(self):
        # term.clear()
        # term.pos(1, 1)
        for y in range(self.sy):
            print(''.join([syms_rev[ self.world[x][y]] 
                for x in range(self.sx)]))

    def ismine(self, x, y):
        return 

    def putmine(self, x, y):
        self.world[x][y] += MINE if self.world[x][y] < MINE else 0


    def toggle(self, x, y):
        state = self.world[x][y] % 4
        if state == UNKNOWN:
            self.world[x][y] = FLAG + (self.world[x][y]//4)*4 #preserve unseen mine
        elif state == FLAG:
            self.world[x][y] = QM + (self.world[x][y]//4)*4
        elif state == QM:
            self.world[x][y] = UNKNOWN + (self.world[x][y]//4)*4


    def place_mines(self, num):
        if num > self.sx*self.sy:
            raise('FUU')
        for _ in range(num):
            x = random.choice(range(self.sx))
            y = random.choice(range(self.sy))
            while self.world[x][y] > 4: #not empty already, re-pick
                x = random.choice(range(self.sx))
                y = random.choice(range(self.sy))
            self.putmine(x, y)
            self.mines += 1

    def open(self, x, y):
        if self.world[x][y] > 3:
            return BOOM
        self.world[x][y] = CLEAR
        return OK

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

def arrow():
    global x, y
    print('arrow')

def up():
    global x, y
    print('up')

def down():
    global x, y
    print('down')

def left():
    global x, y
    print('left')

def right():
    global x, y
    print('right')


def gameloop():
    global x, y
    key = None
    x, y = 0, 0

    actions = {
        '': escape,
        'w': up,
        's': down,
        'a': left,
        'd': right
    }

    draw_world()

    while key != '\03':
        if key in actions:
            result = actions[key]()

        draw_world()
        key = getch()


def main():
    global world
    world = World(25, 10)
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