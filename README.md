# Sokoban_nuXmv
In this project we made a sokoban solver using nuXmv.
The solver takes a board config as an input in xsb format and solves the board by building a model and then passing it through a model checker.
# Installation
clone repository:

git clone https://github.com/yourusername/Sokoban_nuXmv.git
cd Sokoban_nuXmv

create venv:

python -m venv venv
source venv/bin/activate

install dependencies:
pip install -r requirements.txt

install nuXmv

move project to Bin directory of nuXmv program:

mv Sokoban_nuXmv /path/to/nuxmv/bin
cd /path/to/nuxmv/bin/Sokoban_nuXmv

# Usage
first, create a board using the generator:
run board_to_XSB_gui.py
and click the boxes until the board matches the definitions
#: Wall
-: Empty space
@: Player start position
*: Box on goal
+: Player on goal
$: Goal position

![image](https://github.com/elemenopi/Sokoban_nuXmv/assets/105213458/d825cff4-35a0-4fd2-816d-e7b72f13c2b9)

second, runsokoban.py

![image](https://github.com/elemenopi/Sokoban_nuXmv/assets/105213458/00f4b6f7-279d-4b48-87dc-f3b67caf8980)

paste the board and choose your options.

# options

iterative :

This option allows for iterative model checking.
this is explained thoughrouly in our summary

bdd:

we mainly use a sat model solver but you can also check performance of bdd. it will give solve the model using bdd also, and give time performance metric in comparison.



