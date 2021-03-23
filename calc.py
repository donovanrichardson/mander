import inquirer
import math
import re


calcq = [
    inquirer.Text('phase', message="how many phases",validate=lambda _, x: re.match('\d+', x),),
    inquirer.Text('nodes', message="how many nodes",validate=lambda _, x: re.match('\d+', x),)]

calcans = inquirer.prompt(calcq)   

phases = float(calcans['phase'])
nodes = float(calcans['nodes'])

base = nodes**(1/phases)

print(math.log(200,base))