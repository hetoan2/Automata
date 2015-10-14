import sys
import getopt
import re
import json
from pprint import pprint

"""
DFA/NFA Processor

Author:  Tom Fuller

Created: 1/28/15
Updated: 2/20/15
"""

# define global variables
verbose = False
strict = True


class DFA(object):
    def __init__(self):
        self.states = list()
        self.input_symbols = list()
        self.delta_transition_table = list()
        self.start_state = None
        self.accepting_states = list()

    def get_end_state(self, start_state, transition):
        return self.delta_transition_table[start_state][str(transition)][0]

    def test_tape(self, transitions):
        current_state = self.start_state
        for transition in transitions:
            if verbose:
                print current_state, "-"+str(transition)+"->",
            current_state = self.delta_transition_table[current_state][str(transition)][0]
        if verbose:
            print current_state

        return current_state in self.accepting_states

    # return the table of state inequivalences
    def table_fill(self):
        """
        Run the table fill algorithm on the DFA, printing a list of indistinguishable pairs.
        :return:
        """
        if verbose:
            print '\n==============================\n'

        # create our list of marked pairs (distinguishable)
        marked = []

        # create a list of state pairs for our table-filling algorithm
        pairs = []
        for p in self.states:
            for q in self.states:
                if q != p:
                    if (q, p) not in pairs and (p, q) not in pairs:
                        # if the state goes to accepting state it must be marked
                        if p in self.accepting_states or q in self.accepting_states:
                            marked.append((p, q))
                        else:
                            pairs.append((p, q))

        # create a list of indistinguishable nodes by listing all pairs and removing the marked ones as we find them
        indistinguishable_pairs = pairs[:]

        # algorithm requires that this be run twice
        for i in range(2):
            for p, q in pairs:
                for transition in self.input_symbols:
                    r = self.delta_transition_table[p][str(transition)]
                    s = self.delta_transition_table[q][str(transition)]
                    if r != [] and s != []:
                        r = r[0]
                        s = s[0]
                        if s < r:
                            _t = s
                            s = r
                            r = _t
                        if (r, s) in marked:
                            if (p, q) not in marked:
                                marked.append((p, q))
                                indistinguishable_pairs.remove((p, q))

        if verbose:
            print "Indistinguishable Pairs:", indistinguishable_pairs
            print '\n==============================\n'

        return indistinguishable_pairs


class NFA(DFA):
    def __init__(self):
        super(NFA, self).__init__()
        self.fringe = list()

    def get_epsilon_states(self, state):
        return self.delta_transition_table[state]['e']

    def test_tape(self, transitions):
        current_states = [self.start_state]
        for transition in transitions:
            if verbose:
                pass
            for current_state in current_states:
                if current_state not in self.fringe:
                    self.fringe.append(current_state)
                for epsilon_state in self.delta_transition_table[current_state]['e']:
                    if epsilon_state not in self.fringe:
                        self.fringe.append(epsilon_state)

            next_states = list()
            for current_state in self.fringe:
                destination_state = self.delta_transition_table[current_state][str(transition)][0]
                if destination_state not in next_states:
                    next_states.append(destination_state)

            current_states = next_states

    def toDFA(self):
        """
        Do the NFA -> DFA algorithm, and return the current NFA as a DFA.
        """
        new_states = list()
        new_accepting_states = list()
        delta = {}
        for state in self.states:
            compound_state = state

            for destination_state in self.get_epsilon_states(state):
                compound_state += destination_state

            # if we have not seen this compound state before, we should add it to our new DFA
            if compound_state not in new_states:
                # first, make sure the compound node is sorted so AB == BA, etc.
                compound_state = ''.join(sorted(compound_state))

                # add the state to the list of new states
                new_states.append(compound_state)

                # check all our accepting states, if this compound state contains a previous accepting state, add it.
                for accepting_state in self.accepting_states:
                    if accepting_state in compound_state:
                        new_accepting_states.append(compound_state)

        for state in new_states:
            for transition in self.input_symbols:
                # get the destination states by following the transition and then epsilon
                # only use the first state in the compound state (state[:1]), since the compound state
                # has a common end state for all the states which compose it.
                destination_states = self.get_epsilon_states(self.get_end_state(state[:1], transition))

                # this new compound state is made up of the destination states following the transition symbol + epsilon
                compound_state = ""
                for destination_state in destination_states:
                    compound_state += destination_state
                compound_state = ''.join(sorted(compound_state))

                # create our new delta table, with transitions for this state.
                delta[state] = {}
                for _transition in self.input_symbols:
                    delta[state][_transition] = {}

                # finally, add the compound state as the result of the transition, (epsilon removed)
                delta[state][transition] = compound_state

        dfa = DFA()
        dfa.delta_transition_table = delta
        dfa.states = new_states
        dfa.accepting_states = new_accepting_states
        dfa.input_symbols = self.input_symbols
        dfa.start_state = self.start_state

        return dfa


class Alphabet(object):
    def __init__(self):
        self.set = list()

    def add(self, symbol):
        # each symbol should only be in set once.
        if self.set.count(symbol) < 1:
            self.set.append(symbol)

    def __contains__(self, item):
        return self.set.count(item) >= 1


class Language(object):
    def __init__(self, alphabet=None):
        # takes an alphabet object
        self.alphabet = alphabet
        # definitions is a list of raw strings or lambda x: functions that define what is in the language
        self.definitions = list()

    def add_definition(self, x):
        self.definitions.append(x)

    def __contains__(self, item):
        # go through every definition in the list
        for definition in self.definitions:
            # if a definition is a list of acceptable strings, then search in list
            if isinstance(definition, list):
                if item in definition:
                    return True
            else:
                try:
                    # this variable might not be a function, so be prepared.
                    bool_answer = definition(item)
                    if isinstance(bool_answer, bool) and bool_answer:
                        return True
                except:
                    pass
        # after exhausting all definitions, if nothing returned true, then return false
        return False


# define the stack for our push-down automata
class Stack(object):
    def __init__(self):
        self.stack_array = []

    def get_current(self):
        try:
            top = self.stack_array[-1]     # returns the top element of the stack
        except:
            return "Z"      # if it can't get an element (empty) return the marker for end of stack
        return top

    def follow_transition(self, transition):
        # pop whatever is at the top of the stack
        self.stack_array.pop()
        transition = ("q1", "XZ")
        # push the new elements back into the stack
        stack_changes = transition[1]
        element1 = transition[1][1]
        element2 = transition[1][0]

        if len(stack_changes) == 2:     # if we have 2 things to add to the stack, then add both
            if element1 != "Z":     # for our end of stack marker, just ignore the input
                self.stack_array.add(element1)

        if element2 != "/":     # for epsilon, do not add to the stack
            self.stack_array.add(element2)

        return not len(self.stack_array)    # will return true if the stack is empty


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
def parse_transition_string(string, sigma, strict=strict):
    """
    Return a list of transitions from a String as tape.
    :param string: Tape sting to parse.
    :param sigma: The alphabet, containing valid transition symbols.
    :param strict: True by default, if False, will add transitions not in the dictionary.
    :return:
    """
    _set = []
    for c in string:
        if int(c) in sigma:
            _set.append(int(c))
        elif not strict:
            _set.append(int(c))
        else:
            print strict
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
    try:
        transition_string = data["tape"]
        direction = data["order"]
    except KeyError:
        transition_string = None
        direction = None
    try:
        for key in data['opt']:
            print key, data['opt'][key]
            globals()[key] = data['opt'][key]
    except KeyError:
        pass
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
def _process_file(filename):
    sigma, q, _q, f, delta, transition_string = read_file(filename)

    _sigma = parse_to_set(sigma, int)
    _states = parse_to_set(q, state)
    _f = parse_to_set(f, state)
    _delta = parse_delta_table(delta, _sigma, _states)
    if transition_string is not None:
        _transitions = parse_transition_string(transition_string, _sigma, strict=False)

    if verbose:
        print_delta_table(_delta, _sigma)

    if transition_string is not None:
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


def process_file(filename):
    # here the mathematical notation from the book is converted to the structure's english name
    sigma, q, _q, f, delta, transition_string = read_file(filename)

    # load the file data here
    _sigma = parse_to_set(sigma, int)
    _states = parse_to_set(q, state)
    _f = parse_to_set(f, state)
    _delta = parse_delta_table(delta, _sigma, _states)

    if transition_string is not None:
        _transitions = parse_transition_string(transition_string, _sigma, strict=strict)

    # print out variables parsed from file
    print "Q (States):", _states
    print "Sigma (Input Symbols):", _sigma
    print "Q0 (Starting State):", _q
    print "F (Final/Accepting State(s)):", _f
    print "delta:", _delta

    dfa = DFA()
    dfa.states = _states
    dfa.input_symbols = _sigma
    dfa.start_state = _q
    dfa.accepting_states = _f
    dfa.delta_transition_table = _delta

    if transition_string is not None:
        print "tape:", _transitions

        result_string = ""
        try:
            result_string += "\nPasses: "+str(dfa.test_tape(_transitions))
        except KeyError:
            result_string += "\n\nError: Tape contains invalid transition."\
                  "\nEnable strict on parse_transition_string() to force only valid transitions."
            result_string += "\nPasses: False."

        return result_string


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
        if opt in ("-i", "--ifile"):
            filename = arg
        if opt in ("-o", "--ofile"):
            log = True
            log_filename = arg
            verbose = True
        if opt in ("-v", "--verbose"):
            verbose = True

    result = process_file(filename)
    print result

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
    print sys.argv[1:]
    main(sys.argv[1:])