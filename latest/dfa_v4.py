"""
DFA/NFA Processor

Author:  Tom Fuller

Created: 1/28/15
Updated: 2/20/15
"""
# declare imports
import sys
import getopt
import re
import json
from pprint import pprint

# define global variables
verbose = False


# define helper class for tree structure
class Node(object):
    def __init__(self, current_state, parent=None):
        self.state = current_state  # the state of this node (from dictionary)
        self.children = []  # list of children for this node
        self.transition = None
        self.transition_number = None
        self.parent = parent

    def set_transition(self, trans, number):
        self.transition = trans
        self.transition_number = number

    def add_child(self, obj):
        # if self.transition == 'e':
        #  print "added child "+obj.state
        self.children.append(obj)


# returns the set from string applying type function
def parse_to_set(string, typecast):
    _set = []
    # get set from between brackets
    for n in string[string.index("{")+1:string.index("}")].split(","):
        _set.append(typecast(n))
    return _set


# strip any extra space when determining state (more flexible string parsing)
def state(string):
    return string.strip()


# returns the list of transitions
def parse_transition_string(string, sigma):
    _set = []
    for c in string:
        if int(c) in sigma:
            _set.append(int(c))
    return _set


# parses the delta transitions from string to table
def parse_delta_table(delta_string, sigma_set, state_set):
    delta_table = {}
    t = re.findall("\(([^\)]+)\)", delta_string)

    for s in state_set:
        delta_table[s] = {}
        delta_table[s]['e'] = []
        for transition in sigma_set:
            delta_table[s][str(transition)] = []

    for m in t:
        temp_set = parse_to_set("{"+m+"}", state)
        print temp_set
        # add brackets as set markers for parsing
        if temp_set[1] is u'e':
            delta_table[temp_set[0]]['e'].append(temp_set[2])
        else:
            delta_table[temp_set[0]][temp_set[1]].append(temp_set[2])

    return delta_table


# prints the delta transition table for debugging
def print_delta_table(delta_table, sigma_set):
    print delta_table
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
    for key in delta_table.keys():
        print key, "|",
        for transition in sigma_set:
            cell = ""
            for endState in delta_table[key][str(transition)]:
                cell += endState+", "
            cell = cell[:-2]
            print '{:^13}'.format(cell)+"| ",
        print ""
    print "--|--------------"+(len(sigma_set)-1)*"|---------------"+"|\n"


# load inputs from file
def read_file(filename):
    json_data = open(filename)
    data = json.load(json_data)
    if verbose:
        print "Input File:\n"
        pprint(data)
    sigma = data["sigma"]
    q = data["Q"]
    _q = data["start"]
    f = data["F"]
    delta = data["delta"]
    transition_string = data["tape"]
    direction = data["order"]
    if direction == "<-":
        transition_string = transition_string[::-1]

    return sigma, q, _q, f, delta, transition_string


# return whether or not the transition string lands in accepting state
def test_query(transitions, states, q, f, delta, sigma):

    if verbose:
        print "Transition string:\t",

        print transitions

        print ""

    fringe = []
    head = Node(str(q))
    fringe.append(head)

    paths_taken = {}

    # for all transitions in string
    for i in range(len(transitions)):

        # start a fringe for children nodes to process next
        new_fringe = []

        # maintain fringe for delta transitions to avoid looping
        delta_fringe = []

        for node in fringe:
            # create node in path structure
            if node.state not in paths_taken:
                paths_taken[node.state] = {}

            next_states = delta[node.state][str(transitions[i])][:]
            # get states from transition

            if 'e' not in paths_taken[node.state]:
                paths_taken[node.state]['e'] = {}
            # get states from delta + transition
            for epsilon in delta[node.state]['e']:
                epsilon_state = Node(str(epsilon), node.parent)
                epsilon_state.set_transition('e', i-1)

                # if we have already taken the epsilon transition in the past
                if epsilon in paths_taken[node.state]['e']:
                    pass
                else:
                    paths_taken[node.state]['e'][str(epsilon)] = len(next_states) + 1
                if node.parent is not None:
                    node.parent.add_child(epsilon_state)
                else:
                    head.add_child(epsilon_state)
                # print "Did epsilon from "+node.state+" to "+epsilon_state.state
                _nStates = delta[epsilon_state.state][str(transitions[i])][:]
                for s in _nStates:
                    child = Node(str(s), epsilon_state)
                    child.set_transition(transitions[i], i)
                    epsilon_state.add_child(child)
                    new_fringe.append(child)

            for nState in next_states:
                child_node = Node(str(nState), node)
                child_node.set_transition(transitions[i], i)
                node.add_child(child_node)
                new_fringe.append(child_node)
                if transitions[i] not in paths_taken[node.state]:
                    paths_taken[node.state][str(transitions[i])] = {}
                paths_taken[node.state][str(transitions[i])][child_node.state] = 1

            # reset our next states
            next_states = []

        # clear fringe and update
        del fringe[:]
        fringe = new_fringe

        # if verbose:
        # print "State Trace\n"
        # recursive print on head node
        # print_node(head)

    # iterate over the final states for NFA
    for node in fringe:
        # check if it is in the accepting states
        if node.state in f:
            return True, paths_taken, fringe
    # if none of the final states are in accepting states
    return False, paths_taken, fringe


# recursive print function to print tree
def print_node(node):
    if node.transitionNumber > 0:
        transition_number = node.transitionNumber
        print "    "*transition_number,
        print "-"+str(node.transition)+"->",
    else:
        print " ",

    # process the children
    for child in node.children:
        if child.children and child.transition == 'e':
            print_node(child)
        elif child.transition != 'e':
            print_node(child)


# process the given file (and print related data)
def process_file(filename):
    sigma, q, _q, f, delta, transition_string = read_file(filename)

    _sigma = parse_to_set(sigma, int)
    _states = parse_to_set(q, state)
    _f = parse_to_set(f, state)
    _delta = parse_delta_table(delta, _sigma, _states)
    _transitions = parse_transition_string(transition_string, _sigma)

    if verbose:
        print_delta_table(_delta, _sigma)

    t, paths, end_fringe = test_query(_transitions, _states, _q, _f, _delta, _sigma)
    print t

    accepting_states = ''
    for s in _f:
        accepting_states = accepting_states + " "+str(s)

    print paths

    digraph = """digraph finite_state_machine {
  rankdir=LR;
  size="8,5"
  node [shape = doublecircle];
  """

    digraph += accepting_states + ";"  # List of accepting states: S_0 S_1 S_4 etc;
    digraph += "\n  node [shape = circle];"

    for startState, transitions in _delta.iteritems():
        if not in_fringe(str(startState), end_fringe):
            if str(startState) in paths:
                digraph += "  " + str(startState) + " [style = filled, fillcolor=lightblue];\n"
        else:
            if str(startState) in _f:
                digraph += "  " + str(startState) + " [style = filled, fillcolor=olivedrab1, color=limegreen];\n"
            else:
                if str(startState) in paths:
                    digraph += "  " + str(startState) + " [style = filled, fillcolor=lightblue, color=crimson];\n"
                else:
                    digraph += "  " + str(startState) + " [style = filled, fillcolor=lightcoral];\n"
        for t in transitions:
            for endState in _delta[str(startState)][str(t)]:
                visited = False
                try:
                    # if the node is in the paths table, then mark visited on graph
                    if paths[str(startState)][str(t)][str(endState)]:
                        visited = True
                except LookupError:
                    pass
                digraph += "  " + str(startState) + " -> " + str(endState)
                if visited:
                    digraph += "[color=dodgerblue, label = \""+str(t)+"\"];\n"
                else:
                    digraph += "[color=gray75, label = \""+str(t)+"\"];\n"

    digraph += "  labelloc=\"t\";\n"
    digraph += "  label=\"" + str(_transitions) + "\";\n"
    digraph += "}"

    return digraph


def in_fringe(find_state, fringe):
    for s in fringe:
        if s.state == find_state:
            return True
    return False


# main declaration
def main(argv):
    old_stdout = sys.stdout

    global verbose

    filename = "test.json"
    log = False

    # process command line args
    try:
        opts, args = getopt.getopt(argv, "hi:o:v", ["ifile=", "ofile=", "verbose"])
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

    result = process_file(filename)

    if log:
        log_file = open(log_filename, "w")
        sys.stdout = log_file
        print result

    # restore default stdout (not needed as of yet)
    sys.stdout = old_stdout

    # close our log file when done executing
    if log:
        log_file.close()


# main execution
if __name__ == "__main__":
    main(sys.argv[1:])
