"""
DFA Minimizer

Author:  Tom Fuller

Created: 2/24/15
"""
# declare imports
import sys
import os
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
        # add brackets as set markers for parsing
        if temp_set[1] is u'e':
            delta_table[temp_set[0]]['e'].append(temp_set[2])
        else:
            delta_table[temp_set[0]][temp_set[1]].append(temp_set[2])

    return delta_table


# prints the delta transition table for debugging
def print_delta_table(delta_table, sigma_set):
    print "\n", delta_table
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
        print '\n==============================\n'
    sigma = data["sigma"]
    q = data["Q"]
    _q = data["start"]
    f = data["F"]
    delta = data["delta"]

    return sigma, q, _q, f, delta


# return the table of state inequivalences
def table_fill(state_list, f, delta_table, sigma):
    if verbose:
        print '\n==============================\n'

    # create our list of marked pairs (distinguishable)
    marked = []

    # create a list of state pairs for our table-filling algorithm
    pairs = []
    for p in state_list:
        for q in state_list:
            if q != p:
                if (q, p) not in pairs and (p, q) not in pairs:
                    # if the state goes to accepting state it must be marked
                    if p in f or q in f:
                        marked.append((p, q))
                    else:
                        pairs.append((p, q))

    # create a list of indistinguishable nodes by listing all pairs and removing the marked ones as we find them
    indistinguishable_pairs = pairs[:]

    # algorithm requires that this be run twice
    for i in range(2):
        for p, q in pairs:
            for transition in sigma:
                r = delta_table[p][str(transition)]
                s = delta_table[q][str(transition)]
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


# process the given file (and print related data)
def process_file(filename):
    sigma, q, _q, f, delta = read_file(filename)

    _sigma = parse_to_set(sigma, int)
    _states = parse_to_set(q, state)
    _f = parse_to_set(f, state)
    _delta = parse_delta_table(delta, _sigma, _states)

    accepting_states = ''
    for s in _f:
        accepting_states = accepting_states + " " + str(s)

    original = """digraph finite_state_machine {
  rankdir=LR;
  size="8,5"
  node [shape = doublecircle];
 """

    original += accepting_states + ";"  # List of accepting states: S_0 S_1 S_4 etc;
    original += "\n  node [shape = circle];"

    for startState, transitions in _delta.iteritems():
        original += "  " + str(startState) + ";\n"
        for t in transitions:
            for endState in _delta[str(startState)][str(t)]:
                original += "  " + str(startState) + " -> " + str(endState)
                original += "[label = \""+str(t)+"\"];\n"

    original += "  node [style = invis, shape = none, label = \"\", width = 0, height = 0];\n" 
    original += "  pointer -> " + _q + ";\n"
    original += "  labelloc=\"t\";\n"
    original += "  label=\"Original DFA\";\n"
    original += "}"

    print original

    if verbose:
        print_delta_table(_delta, _sigma)

    remappings = table_fill(_states, _f, _delta, _sigma)
    removed = []

    for x, deleted_node in remappings:
        removed.append(deleted_node)

    for merge_node, removed_node in remappings:
        _delta.pop(removed_node)
        preserved_node_for_merging = _delta.pop(merge_node)
           
        _delta[merge_node+removed_node] = preserved_node_for_merging

        # combine both nodes into a new node
        for start_node in _delta.keys():
            for transition in _delta[start_node]:
                if removed_node in _delta[start_node][transition]:
                    _delta[start_node][transition].remove(removed_node)
                    _delta[start_node][transition].append(merge_node)
    
    for start in _delta:    
        # rename all transitions to old nodes to merged node
        for transition in _delta[start]:
            dest_node_list = _delta[start][transition]
            for m, r in remappings:
                if m in dest_node_list:
                    dest_node_list.remove(m)
                    dest_node_list.append(m+r)
                if r in dest_node_list:
                    dest_node_list.remove(r)
                    dest_node_list.append(m+r)
        
    if verbose:
        print "Reduced Delta Table"
        print_delta_table(_delta, _sigma)

    # rename our starting state if it was changed
    for m, r in remappings:
        if _q == m or _q == r:
            _q = m+r

    # rename accepting states
    accepting_states = ''
    for s in _f:
        for m, r in remappings:
            if s == m or s == r:
                s = m+r
            accepting_states = accepting_states + " " + str(s)
 
    digraph = """digraph finite_state_machine {
  rankdir=LR;
  size="8,5"
  node [shape = doublecircle];
 """

    digraph += accepting_states + ";"  # List of accepting states: S_0 S_1 S_4 etc;
    digraph += "\n  node [shape = circle];"

    for startState, transitions in _delta.iteritems():
        digraph += "  " + str(startState) + ";\n"
        for t in transitions:
            for endState in _delta[str(startState)][str(t)]:
                digraph += "  " + str(startState) + " -> " + str(endState)
                digraph += "[label = \""+str(t)+"\"];\n"

    digraph += "  node [style = invis, shape = none, label = \"\", width = 0, height = 0];\n"
    digraph += "  pointer -> " + _q + ";\n"
    
    digraph += "  labelloc=\"t\";\n"
    digraph += "  label=\"Reduced DFA\";\n"
    digraph += "}"

    return digraph, original


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
            log_filename = log_filename[:log_filename.rfind(".")]
            log = True
            verbose = True
        elif opt in ("-v", "--verbose"):
            verbose = True

    try:
        reduced, original = process_file(filename)
    except:
        print "Please input a DFA to be reduced. This is either an NFA or a improperly formatted file."
        log = False     # set log to false to avoid saving garbage

    if log:
        reduced_graph = open(log_filename + ".dot", "w")
        sys.stdout = reduced_graph
        print reduced
        reduced_graph.close()
        og_graph = open(log_filename + "_original.dot", "w")
        sys.stdout = og_graph
        print original
        og_graph.close()

    # restore default stdout (not needed as of yet)
    sys.stdout = old_stdout

    # close our log file when done executing
    if log:
        # generate the graphviz image
        os.system("dot -Tpng " + log_filename + ".dot" + " -o reduced.png")
        os.system("dot -Tpng " + log_filename + "_original.dot" + " -o original.png")
        combined = """graph {
     node [shape=none, label=""]
     d1 [image="original.png"]
     d2 [image="reduced.png"]
}"""
        final_graph = open(log_filename + "_combined.dot", "w")
        sys.stdout = final_graph
        print combined
        final_graph.close()
        os.system("dot -Tpng " + log_filename + "_combined.dot -o " + log_filename + ".png") 

# main execution
if __name__ == "__main__":
    main(sys.argv[1:])
