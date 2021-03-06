import signal
import sys, termios, tty
import term
import time
import random 
# from collections import deque

cx, cy = 0, 0
ox, oy = 0, 0
world = None

OFFY = 1

OK = 1000
BOOM = 999
WIN = 1001
BREAK = 1002

UNKNOWN = 9 # default tile
FLAG = 10 #flagged mine
QM = 11 #question mark
BLOWN = 12

tiles = [
    ('·', term.white, term.dim), 
    ('1', term.dim, term.green), 
    ('2', term.yellow, term.dim), 
    ('3', term.dim, term.cyan), 
    ('4', term.bold, term.green), 
    ('5', term.bold, term.blue), 
    ('6', term.cyan), 
    ('7', term.bold, term.magenta), 
    ('8', term.red, term.bold), # #of mines around
    ('o', term.white) , # UNKNOWN
    ('¤', term.red, term.bold) , # marked mine
    ("?", term.blue, term.bold),  # qmark        
    ('¤', term.bgred), #blown mine 
    ('¤', term.bold, term.red), # reveal unknown
    ('¤', term.green, term.bold), #reveal marked
    ('¤', term.red, term.bold), #reveal qm mine
    ('¤', term.bgred, term.bold)  #reveal blown
]  



class World():
    def __init__(self, sx, sy, nmines = 0):
        assert sy + sy < 500, 'too big'
        self.sx = sx
        self.sy = sy
        self.nmines = 0
        self.map = [[UNKNOWN for y in range(sy)] for x in range(sx)]
        self.mines = [[0 for y in range(sy)] for x in range(sx)]
        self.place_mines(nmines)

    def draw(self):
        # term.clear()
        for y in range(self.sy):
            term.pos(y+OFFY+1, 1)
            for x in range(self.sx):
                term.write(*tiles[ self.map[x][y] ]) 

    def mines_marked(self):
        c = 0 
        for x in range(self.sx):
            for y in range(self.sy):
                c += 1 if self.map[x][y] == FLAG else 0
        return c



    def reveal(self):
        # term.clear()
        for y in range(self.sy):
            term.pos(y+OFFY+1, 1)
            for x in range(self.sx):
                term.write(*tiles[self.mines[x][y]*4 + self.map[x][y] ]) 



    def ismine(self, x, y):
        return self.mines[x][y]

    def putmine(self, x, y):
        self.mines[x][y] = 1 


    def toggle(self, x, y):  #lol fsm
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
        return len([0 for xx, yy in self.get_neighbors_u(x, y) 
            if self.mines[xx][yy]] )

    def open(self, x, y):  #try to open a cell
        qs = None

        if self.mines[x][y]:
            self.map[x][y] = BLOWN
            return BOOM

        flagged_ns, unknown_ns = [], []
        #already has number, maybe can open neighbors
        if self.map[x][y] < UNKNOWN and self.map[x][y] > 0: 
            for xx, yy in self.get_neighbors(x, y):
                if self.map[xx][yy] == FLAG:
                    flagged_ns.append((xx, yy))
                elif self.map[xx][yy] == UNKNOWN:
                    unknown_ns.append((xx, yy))            
            #all surrounding mines marked (supposedly)
            #add remaining neighbors to q
            if len(flagged_ns) >= self.map[x][y]: 
                qs = set([xx*1000+yy for xx,yy in unknown_ns])
                # debug(str(qs))
            else:
                #nope, cannot safely open around
                return OK   

        #init if not inited earlier
        #set is actually a unique queue
        qs = qs or set((x*1000 + y, ))  
        
        #term throws up sometimes in concurrent output, disable timer
        signal.alarm(0) 

        while len(qs):            
            xy = qs.pop()
            x, y = xy//1000, xy % 1000
            #can still trigger BOOM if opening from number
            #and flags were misplaced
            if self.mines[x][y]: 
                self.map[x][y] = BLOWN
                return BOOM             
            nmines = self.get_count(x, y) 
            self.map[x][y] = nmines
            if nmines == 0:
                for xx, yy in self.get_neighbors_u(x, y):                       
                    qs.add(xx*1000+yy)

        signal.alarm(1)  #reenable timer
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

    # def get_neighbors_uq(self, x, y):
    #     return [[xx,yy] for xx, yy 
    #         in self.get_neighbors(x,y) 
    #         if (self.map[xx][yy] == UNKNOWN and [xx,yy] not in self.q)]

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

#actions
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

def brk():
    return BREAK

# /actions


#display
def status(text = '', *args):
    term.pos(2 + world.sy + OFFY, 8)
    term.write(term.red + '¤:' + term.white )
    term.write('%d/%d  '%(world.nmines - world.mines_marked(), 
                world.nmines))
    term.write(text, *args)              
    cpos()

def help(text = term.dim + "move: wasd/toggle: SPACE/open: ENTER"):
    term.pos(3 + world.sy + OFFY, 0)
    term.write(text)    

def debug(text):
    term.pos(3 + world.sy + OFFY, 0)
    term.write(text)    


def timeout_handler(sg, frame):
    term.pos(2 + world.sy + OFFY, 1)
    term.write(term.blue + 't:')
    term.write(term.white + '%i '%(time.time() - starttime))
    signal.alarm(1)
    cpos()

def cpos():
    #position cursor properly and redraw that tile
    try:
        term.pos(cy + 1 + OFFY, cx +1)
        term.write(* tiles[ world.map[cx][cy] ])
        term.pos(cy + 1 + OFFY, cx +1)
    except RuntimeError:
        sleep(0.2)
        cpos()  #timing glitch in term, just retry lol

def head():
    term.pos(1,1)
    term.write(term.center(term.green + 
        'PYSWEEPER %ix%i'%(sx, sy)))
    term.write(term.off)

# /display


def gameloop(x = 80, y=30, mm = 40):
    global cx, cy, redraw, starttime
    global world

    key = None
    cx, cy = 0, 0

    actions = {
        # '': escape,
        'w': up,
        's': down,
        'a': left,
        'd': right,
        '\r': enter,
        ' ': toggle,
        '\03': brk
    }

    world = World(x, y, mm)

    result = OK
    redraw = True
    key = ''

    term.clear()
    head()
    help()

    starttime = time.time()
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(1)

    while result == OK:
        if redraw: 
            world.draw()
            redraw = False
            cpos()
        status('your move   ')
        key = getch()
        if key in actions:
            result = actions[key]()

    signal.alarm(0) #stop timer!
    world.reveal()
    return result


def main():
    import argparse

    global sx, sy, nm
    sx, sy, nm = 50, 20, 10

    parser = argparse.ArgumentParser(description='Console minesweeper',
        argument_default = 'auto')
    parser.add_argument('size', 
            choices = ['s', 'm', 'l', 'xl', 'auto'],
            default = 'auto',
            nargs = '?', #make optional
            help='field size, default: auto fill terminal')

    args = parser.parse_args()

    worldsizes = {
        's': (15, 10, 15),
        'm': (20, 15, 30),
        'l': (30, 20, 60),
        'xl': (80, 30, 250),
        'auto': (term.getSize()[1], term.getSize()[0]-4, 
            term.getSize()[1] * term.getSize()[0]//9)
    }
    sx, sy, nm = worldsizes[args.size]
    term.clear()
    head()
    more = True
    while more:    
        result = gameloop(sx, sy, nm)
        if result == BREAK:
            return 0
        elif result == BOOM:
            help(term.blink+term.bgred+term.bold+
                '       BOOM YOU LOSE! New game? Y/N ' + term.off)
        elif result == WIN:
            help(term.blink + term.bggreen + term.bold + 
                '       WELL DONE YOU WIN. New game? Y/N ' + term.off)


        key = ' '
        while key not in 'yYnN\03':
            key = getch()
        more = (key in 'yY')

    term.writeLine(" ")
    term.writeLine(term.off + "k bye")



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
    assert res == BOOM
    w.reveal()

if __name__ == "__main__":
    main()