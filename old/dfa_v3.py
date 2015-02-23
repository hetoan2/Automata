'''
DFA/NFA Processor

Author:  Tom Fuller

Created: 1/28/15
Updated: 2/08/15
'''
# declare imports
import sys, getopt
import re
import json
from pprint import pprint

# define global variables
verbose = False

# define helper class for tree structure
class Node(object):
  def __init__(self, state, parent=None):
    self.state = state # the state of this node (from dictionary) 
    self.children = [] # list of children for this node
    self.transition = None
    self.transitionNumber = None
    self.parent = parent

  def setTransition(self, trans, number):
    self.transition = trans
    self.transitionNumber = number

  def add_child(self, obj):
    #if self.transition == 'e':
    #  print "added child "+obj.state
    self.children.append(obj)

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

# parses the delta transitions from string to table
def parseDeltaTable(delta_string, sigma_set, state_set):
  deltaTable = {}
  t = re.findall("\(([^\)]+)\)",delta_string)

  for s in state_set:
    deltaTable[s] = {}
    deltaTable[s]['e'] = []
    for transition in sigma_set:
      deltaTable[s][str(transition)] = []

  for m in t:
    temp_set = parseToSet("{"+m+"}", state)
    print temp_set
    # add brackets as set markers for parsing
    if temp_set[1] is u'e':
      deltaTable[temp_set[0]]['e'].append(temp_set[2])
    else:
      deltaTable[temp_set[0]][temp_set[1]].append(temp_set[2])

  return deltaTable;

# prints the delta transition table for debugging
def printDeltaTable(deltaTable, sigma_set):
  print deltaTable
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
def readFile(filename):
  json_data = open(filename)
  data = json.load(json_data)
  if verbose:
    print "Input File:\n"
    pprint(data)
  sigma = data["sigma"]
  Q = data["Q"]
  _q = data["start"]
  F = data["F"]
  delta = data["delta"]
  transitionString = data["transitions"]
  return sigma, Q, _q, F, delta, transitionString

# return whether or not the transition string lands in accepting state
def testQuery(transitions, states, q, f, delta, sigma):

  if verbose:
    print "Transition string:\t", 

    print transitions

    print ""

  fringe = []
  head = Node(str(q))
  fringe.append(head)

  # for all transitions in string
  for i in range(len(transitions)):
    
    # start a fringe for children nodes to process next
    newFringe = []

    for node in fringe:
      nextStates = delta[node.state][str(transitions[i])][:]
      # get states from transition
      
      # get states from delta + transition 
      for epsilon in delta[node.state]['e']:
        eState = Node(str(epsilon),node.parent)
        eState.setTransition('e', i-1)
        if node.parent is not None:
          node.parent.add_child(eState)
        else:
          head.add_child(eState)
        #print "Did epsilon from "+node.state+" to "+eState.state 
        _nStates = delta[eState.state][str(transitions[i])][:]
        for s in _nStates:
          child = Node(str(s), eState)
          child.setTransition(transitions[i],i)
          eState.add_child(child)
          newFringe.append(child)

      for nState in nextStates:
        childState = Node(str(nState),node)
        childState.setTransition(transitions[i],i)
        node.add_child(childState)
        newFringe.append(childState)
    
      # reset our next states
      nextStates = []
       

    # clear fringe and update
    del fringe[:]
    fringe = newFringe 

  if verbose:
    print "State Trace\n"
    # recursive print on head node 
    printNode(head)
 
  # iterate over the final states for NFA
  for node in fringe:
    # check if it is in the accepting states
    if node.state in f:
      return True
  # if none of the final states are in accepting states
  return False

# recursive print function to print tree
def printNode(node):
  if node.transitionNumber > 0:
    if node.parent.transition != 'e':
      transitionNumber = node.transitionNumber 
      print "    "*transitionNumber,
      print "-"+str(node.transition)+"->",
  else:
    print " ",

  # process the children
  for child in node.children:
    printNode(child)

# process the given file (and print related data)
def processFile(filename):
  sigma, Q, _q, F, delta, transitionString = readFile(filename)

  _sigma = parseToSet(sigma, int)
  _states =  parseToSet(Q, state)
  _F = parseToSet(F, state)
  _delta = parseDeltaTable(delta, _sigma, _states)
  _transitions = parseTransitionString(transitionString, _sigma)

  if verbose:
    printDeltaTable(_delta, _sigma)

  t = testQuery(_transitions, _states, _q, _F, _delta, _sigma)
  print t

  return t

# main declaration
def main(argv):
  old_stdout = sys.stdout

  global verbose 
 
  filename = "test.json"
  log = False

  # process command line args
  try:
    opts, args = getopt.getopt(argv,"hi:o:v",["ifile=","ofile=","verbose"])
  except getopt.GetoptError:
    print 'dfa.py -i <inputfile> -o <outputfile> -v'
    sys.exit(2)
  for opt, arg in opts:
    if opt == '-h':
      print 'dfa.py -i <inputfile> -o <outputfile> -v'
      sys.exit()
    elif opt in ("-i", "--ifile"):
      filename = arg
    elif opt in ("-o", "--ofile"):
      log_filename = arg
      log = True
      verbose = True
    elif opt in ("-v", "--verbose"):
      verbose = True

  if log:
    log_file = open(log_filename, "w")
    sys.stdout = log_file
  
  result = processFile(filename)
  # restore default stdout (not needed as of yet)
  sys.stdout = old_stdout

  # close our log file when done executing
  if log:
    log_file.close()

# main execution
if __name__ == "__main__":
  main(sys.argv[1:])
