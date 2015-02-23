'''
Deterministic Finite Automaton 

Tom Fuller
1/28/15
'''
import re
import json
from pprint import pprint
# define strings for testing

transitionString = '010111011011101' # string to test
Q = '{A, B, C}' # finite set of states
sigma = '{0, 1, 2}' # finite set of input symbols (alphabet)
delta = '{(A, 1, B), (A, 0, C), (B, 1, C), (B, 0, A), (C, 1, A), (C, 0, B), (A, 1, C), (C, 0, A), (C, 2, B), (C, 2, A)}'
# set of delta transitions in form (From, InputSymbol, To)
F = '{C}' # accepting states (must be in Q)
_q = 'A' # start state (must be in Q)

# returns the set from string applying type function
def parseToSet(string, typecast):
  _set = []
  # get set from between brackets 
  for n in string[string.index("{")+1:string.index("}")].split(","):
    _set.append(typecast(n))
  return _set;

# strip any extra space when determining state (more flexible string parsing)
def state(string):
  return string.strip();

# returns the list of transitions
def parseTransitionString(string, sigma):
  _set = []
  for c in string:
    if int(c) in sigma:
      _set.append(int(c))
  return _set;

def parseDeltaTable(delta_string, sigma_set, state_set):
  deltaTable = {}
  t = re.findall("\(([^\)]+)\)",delta_string)

  for s in state_set:
    deltaTable[s] = {}
    for transition in sigma_set:
      deltaTable[s][str(transition)] = []

  for m in t:
    temp_set = parseToSet("{"+m+"}", state)
    # add brackets as set markers for parsing
    deltaTable[temp_set[0]][temp_set[1]].append(temp_set[2])

  return deltaTable;

def printDeltaTable(deltaTable, sigma_set):
  print "\n   -- Delta Table "+(len(sigma_set)-1)*"---------------|"
  print "",
  for transition in sigma_set:
    print " |  ", transition, " \t",
  print " |"
  divider = "__"
  for transition in sigma_set:
    if transition is 0:
      divider += "|______________"
    else:
      divider += "|_______________"
  print divider+"|"
  for key in deltaTable.keys():
    print key, "|",
    for transition in sigma_set:
      cell = ""
      for endState in deltaTable[key][str(transition)]:
        cell += endState+", "
      cell = cell[:-2]
      print '{:^13}'.format(cell)+"| ",
    print ""
  print "--|--------------"+(len(sigma_set)-1)*"|---------------"+"|\n" 
 
# load inputs from file
def readFile():
  json_data = open('test.json')
  data = json.load(json_data)
  pprint(data)
  sigma = data["sigma"]
  Q = data["Q"]
  _q = data["start"]
  F = data["F"]
  delta = data["delta"]
  transitionString = data["transitions"]
  return sigma, Q, _q, F, delta, transitionString


sigma, Q, _q, F, delta, transitionString = readFile()

_sigma = parseToSet(sigma, int)
_states =  parseToSet(Q, state)
_F = parseToSet(F, state)
_delta = parseDeltaTable(delta, _sigma, _states)
_transitions = parseTransitionString(transitionString, _sigma)

paths = {}

# validity check stub in case i need this for NFA
def check_validity(state_set):
  return;

# return whether or not the transition string lands in accepting state
def testQuery(transitions, states, q, f, delta, sigma):
  paths[0] = [str(q)]
  print "Transition string:\t", 

  print transitions

  print ""
  # for all transitions in string
  for i in range(len(transitions)):
    # find next state for each of the possible previous states
    previousStates = paths[i]
    
    paths[i+1] = []
    for state in previousStates:
      nextStates = delta[state][str(transitions[i])]
      for nState in nextStates:
        if nState not in paths[i+1]:
          paths[i+1].append(str(nState))

  print "State Trace\n"
 
  for i in range(len(transitions)):
    print paths[i], "--"+str(transitions[i])+"-->", paths[i+1]
 
  # iterate over the final states for NFA
  for state in paths[len(transitions)]:
    # check if it is in the accepting states
    if state in f:
      return True

  # if none of the final states are in accepting states
  return False

printDeltaTable(_delta, _sigma)
print testQuery(_transitions, _states, _q, _F, _delta, _sigma)
