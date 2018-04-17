# pysweeper

A simple console minesweeper clone as a python excercise. Needs python3 and py-term to run. 

## Installation

`pip3 install py-term`

## Command line

`python3 pysweeper [s|m|l|xl|auto]`

The only optional parameter is game size, which defaults to filling the available window.

## Controls

**wasd** - move around

**space** - toggle mine/question/unknown

**Enter** - Open unknown tile. Similar to the original, it will also open the neighboring tiles of an open tile which has its neighboring mines already marked.

## To do

+ make it python2 compatible
+ package for easier distribution
+ windows port maybe?
