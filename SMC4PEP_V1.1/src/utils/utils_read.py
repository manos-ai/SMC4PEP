# -*- coding: utf-8 -*-
"""
utils to read BPMN diagrams from an xml file
"""


# imports
# https://stackoverflow.com/questions/51679677/how-to-create-dict-with-2-keys-and-one-value
#from collections import defaultdict
#from collections import OrderedDict

import matplotlib.pyplot as plt

import networkx as nx # for making and plotting graphs

import xmltodict   # for reading xml files

#import pickle # for storing python objects

# own modules
import utils_process


#%% function - orddict2list

def orddict2list(ordDict):
    # convert an ordered dict to a list of one 
    if type(ordDict) == list:
        return ordDict
    l = []
    l.append(ordDict)
    return l
# end func

#%% class - IDmap

class IDmap():
    # a method to map long IDs such as 'adas123...'
    # into numbers such as 0, 1, 2, etc.
    
    def __init__(self, integer_ids = False):
        # def a dictionary that holds all IDs given so far
        self.mydict = {}
        self.integer_ids = integer_ids
    # end func
    
    def map_id(self, myID):
        # the method to map IDs into numbers
            # into numbers such as 0, 1, 2, etc.
        # Input:
        #    > myID:    an ID of xml, such as 'qwe78'
        #    > mydict:  a dict mapping already encountered xml IDs to numbers
        #               e.g. mydict = {'aaa12' : 0, 'abc34': 1}
        # Output:
        #    > mydict: mydict with the new ID inserted in
        #              for example, mydict = {'aaa12' : 0, 'abc34': 1, 'qwe78': 2}
        
        if self.integer_ids == False:
            # return id as it is (str)
            return myID
        # end if
        
        if myID not in self.mydict: # ID not in dict
            # append new ID to dict
            ID_new = len(self.mydict) # new number = length of dict (see example above)
            self.mydict[myID] = ID_new
        # end if
        return self.mydict[myID]
    # end func
    
# end class


#%% function - read_xml

def read_xml(xml_file):
    # read the xml file in python
    # Input:
    #    > xml_file: the xml file name (such as 'aaa.xml') or path ('files\aaa.xml')
    # Output:
    #    > bpmn_dict: a dict of dicts containing the BPMN diagrams (e.g. process['nodes'])
    
    # gead xml and convert to dict
    xml_data = open(xml_file, 'r').read()  # Read data
    xmlDict = xmltodict.parse(xml_data)  # Parse XML
    
    # get the process elements (diagrams with nodes, edges, etc)
    bpmn_dict = xmlDict['bpmn:definitions']
    
    return bpmn_dict
# end func


#%% function - rem_unconnected

def rem_unconnected(Ndiag, Fdiag):
    # remove unconnected nodes from Ndiag
    # remove unconnected nodes (there are 2-3 mistakes in the diagrams, where
    # some nodes are unconnected - probably remained from previous diagrams)
    # Input:
    #    > Ndiag, Fdiag: dictionaries of diagram nodes and flows
    #                    Ndiag: dict of type {nodeID: [nodeName, nodeType]}
    #                    Fdiag: dict of type (nodeID_in, nodeID_out): label
    # Output:
    #    > Ndiag, Fdiag: same as above, with unconnected nodes removed
    
    N = [] # list of nodes
    
    # get all connected nodes
    for elem in Fdiag:
        # get source and target
        source, target = elem
        
        if source not in N:
            N.append(source)
        # end if
        if target not in N:
            N.append(target)
        # end if
    # end for
    
    # the rest is unconnected - remove them from Ndiag
    Nrem = [] # nodes to remove
    for node in Ndiag.keys():
        if node not in N:
            # add node to be removed
            Nrem.append(node)
        # end if
    # end for
    
    for node in Nrem:
        # remove node from dict
        Ndiag.pop(node)
    # end for
    
    # ready
    return Ndiag, Fdiag
# end func


#%% function - read_diagram

def read_diagram(diagram):
    # read the elements (nodes, edges) form a diagram
    # diagrams are contained in the BPMN file, in
    # xmlDict['bpmn:definitions']['bpmn:process']: this contains a list of 
    # idagrams - diagram above is only one of them
    
    # Input: 
    #    > diagram: xml part containing info of a diagram, for example:
    #      xmlDict['bpmn:definitions']['bpmn:process'][1] for the 1st diagram    
    # Output:
    #    > Ndiag, Fdiag: dictionaries of diagram nodes and flows
    #                    Ndiag: dict of type {nodeID: [nodeName, nodeType]}
    #                    Fdiag: dict of type (nodeID_in, nodeID_out): label
    
    
    
    # dicts to hold nodes and flows
    Ndiag = {}
    Fdiag = {}
    
    # get diagram name
    diag_name = diagram['@name']
    
    # get tasks
    if 'bpmn:task' in diagram.keys():
        for elem in orddict2list( diagram['bpmn:task'] ):
            # make ID
            node_id = elem['@id']
            # get name
            node_name = elem['@name']
            # get type
            node_type = 'task'
            # put it in dict
            Ndiag[node_id] = {'name': node_name, 'type': node_type}
        # end for
    # end if
    
    # start event(s)
    if 'bpmn:startEvent' in diagram.keys():
        for elem in orddict2list( diagram['bpmn:startEvent'] ):
            # make ID
            node_id = elem['@id']
            # get name
            node_name = elem['@name']
            # get type
            node_type = 'start'
            # put it in dict
            Ndiag[node_id] = {'name': node_name, 'type': node_type}
        # end for
    # end if
    
    # end event(s)
    if 'bpmn:endEvent' in diagram.keys():
        for elem in orddict2list( diagram['bpmn:endEvent'] ):
            # make ID
            node_id = elem['@id']
            # get name
            node_name = elem['@name']
            # get type
            node_type = 'end'
            # put it in dict
            Ndiag[node_id] = {'name': node_name, 'type': node_type}
        # end for
    # end if
    
    # intermediate events
    if 'bpmn:intermediateThrowEvent' in diagram.keys():
        for elem in orddict2list( diagram['bpmn:intermediateThrowEvent'] ):
            # make ID
            node_id = elem['@id']
            # get name
            node_name = elem['@name']
            # get type
            node_type = 'event'
            # put it in dict
            Ndiag[node_id] = {'name': node_name, 'type': node_type}
        # end for
    # end if
    
    # intermediate events 2 (catch events)
    if 'bpmn:intermediateCatchEvent' in diagram.keys():
        for elem in orddict2list( diagram['bpmn:intermediateCatchEvent'] ):
            # make ID
            node_id = elem['@id']
            # get name
            node_name = elem['@name']
            # get type
            node_type = 'event'
            # put it in dict
            Ndiag[node_id] = {'name': node_name, 'type': node_type}
        # end for
    # end if
    
    # decision gates
    decis_cnt = 0
    if 'bpmn:exclusiveGateway' in diagram.keys():
        for elem in orddict2list( diagram['bpmn:exclusiveGateway'] ):
            # make ID
            node_id = elem['@id']
            # get name
            decis_cnt += 1
            node_name = 'decision' + str(decis_cnt)
            # get type
            node_type = 'decision'
            # put it in dict
            Ndiag[node_id] = {'name': node_name, 'type': node_type}
        # end for
    # end if
    
    # parallel gates
    fork_cnt = 0
    join_cnt = 0
    if 'bpmn:parallelGateway' in diagram.keys():
        for elem in orddict2list( diagram['bpmn:parallelGateway'] ):
            # make ID
            node_id = elem['@id']
            # get type (either list of nodes or string with one outgoing node)
            if type(elem['bpmn:outgoing']) == list and len(elem['bpmn:outgoing']) > 1: 
                fork_cnt += 1
                node_name = 'fork' + str(fork_cnt)
                node_type = 'fork'
            else:
                join_cnt += 1
                node_name = 'join' + str(join_cnt)
                node_type = 'join'
            # put it in dict
            Ndiag[node_id] = {'name': node_name, 'type': node_type}
        # end for
    # end if
    
    # finally get the flows
    if 'bpmn:sequenceFlow' in diagram.keys():
        for elem in orddict2list( diagram['bpmn:sequenceFlow'] ):
            # get label if it exists
            if '@name' in elem:
                flow_label = elem['@name']
            else:
                flow_label = ''
            # end if
            
            # get source and target
            source = elem['@sourceRef']
            target = elem['@targetRef']
            
            # put it in flow dict
            Fdiag[(source, target)] = flow_label
        # end for
    # end 
    
    # remove unconnected nodes (there are 2-3 mistakes in the diagrams, where
    # some nodes are unconnected - probably remained from previous diagrams)
    Ndiag, Fdiag = rem_unconnected(Ndiag, Fdiag)
    
    # all ready, return
    return diag_name, Ndiag, Fdiag
# end func


#%% function - plot_diagram

def plot_diagram(Ndiag, Fdiag, save_name = None):
    # simple method for plotting a diagram (for debugging)
    # Input:
        # > Ndiag: dict of diagram nodes: nodeID: {name, type}
        # > Fdiag: dict of diagram flows: [source, target]: flow_label
        # > save_name: the location to store the plot, or None for not storing it
    # Output:
        # > A plot of the diagram, using the networkx library
        # > edges: a list of edges, where each edge is a tuple: (source_name, target_name) 
    
    # define an nx directed graph
    # https://stackoverflow.com/questions/28533111/plotting-networkx-graph-with-node-labels-defaulting-to-node-name
    Gnx = nx.MultiDiGraph()
    
    # we need multigraph due to the parallel edges
    # https://networkx.org/documentation/stable/reference/classes/index.html
    
    edges = []
    
    # insert all edges
    for elem in Fdiag.keys():
        # get source and target
        source, target = elem
        
        # get source and target names
        source_name = Ndiag[source]['name']
        target_name = Ndiag[target]['name']
        
        # append edge in Gnx
        Gnx.add_edge(source_name, target_name)
        edges.append((source_name, target_name))
    # end for
    
    # ready, plot Gnx with labels
    nx.draw(Gnx, with_labels = True)
    
    if save_name != None:
        plt.savefig(save_name)
    # end if
    return edges
# end func


#%% function - get_seq_flows

def get_seq_flows(bpmn_dict):
    # get the sequence flows of a process
    # Input:
    #    > bpmn_dict: a bpmn dict read from the xml file (see xmlDict above)
    #                 it's in xmlDict['bpmn:definitions'], and contains all
    #                 BPMN data of the process
    # Output:
    #    > Fmsg: dict of message flows in the form (source, target): label
    #            label of message flows is usually empty
    
    Fmsg = {}
    
    # get msg flow data from the xml file
    try:
        bpmn_msg_flows = bpmn_dict['bpmn:collaboration']['bpmn:messageFlow']
    except:
        bpmn_msg_flows = []
        for proc_fl in bpmn_dict['bpmn:collaboration']:
            for elem in proc_fl['bpmn:messageFlow']:
                bpmn_msg_flows.append(elem)
            # end for
        # end for
    # end try
    
    for fl in bpmn_msg_flows:
        # get source and target
        source_id = fl['@sourceRef']
        target_id = fl['@targetRef']
        
        # insert in Fmsg (with empty label)
        Fmsg[(source_id, target_id)] = ''
    # end for
    
    # ready
    return Fmsg
# end func


#%% function - read_process_pools

def read_process_pools(xml_file):
    # read a pool - based process from an xml file
    # Input:
    #    > xml_file: string containing the file name
    # Output:
    #    > N, F, Fmsg: dict of type {pool_id}:Npool, Fpool,
    #                  where Npool = dict of type [node_id]:{name, type} (see
    #                  before), Fpool = dict [(source, target)]: label, and
    #                  Fmsg is the dict of message flows: [source, target]: label
    
    # read the bpmn info
    bpmn_dict = read_xml(xml_file)
    
    # get process (pools)
    process = bpmn_dict['bpmn:process']
    
    N = {}
    F = {}
    Fmsg = {}
    
    cnt = -1
    
    # read each pool
    if type(process) != list:
        # handle single diagram case
        process = [process]
    # end if
    for diagram in process:
        cnt += 1
        # read current diagram
        diag_name, Ndiag, Fdiag = read_diagram(diagram)
        
        # if diagram empty, skip it
        if len(Ndiag) == 0:
            continue
        # end if
        
        # append Ndiag, Fdiag in total
        N[cnt] = Ndiag
        F[cnt] = Fdiag
    # end for
    
    # read also the message flows
    Fmsg = get_seq_flows(bpmn_dict)
    
    # ready, return
    return N, F, Fmsg
# end func

#%% function - merge_nodes_flows

def merge_nodes_flows(N, F):
    # merge the nodes and flows of a process in 2 single dicts
    # Input:
    #    > N: dict of type [diagram_no] : Ndiag, where Ndiag are the nodes of 
    #         that diagram (see read_diagram above)
    #    > F: dict of type [diagram_no] : Fdiag, where Fdiag are the flows of
    #         that diagram (see read_diagram above)
    # Output:
    #    > Nall: dict of type [nodeID] :{node_name, node_type} for all nodes
    #             of the process
    #    > Fall: dict of type [(sourceID, targetID)]: flow_label, for all 
    #            flows of the process
    
    Nall = {}
    Fall = {}
    
    for i in N.keys():
        # append nodes of diagram i into Nall
        # https://www.geeksforgeeks.org/python-merging-two-dictionaries/
        
        Nall.update(N[i])
    # end for
    
    for i in F.keys():
        # append flows of diagram i into Fall
        
        Fall.update(F[i])
    # end for
    
    return Nall, Fall
# end func


#%% function - read_process_events

def read_process_events(xml_file):
    # read an event - based process from an xml file
    # Input:
    #    > xml_file: string containing the file name
    # Output:
    #    > N, F, Timeline: dict of type {pool_id}:Npool, Fpool,
    #                  where Npool = dict of type [node_id]:{name, type} (see
    #                  before), Fpool = dict [(source, target)]: label, and
    #                  Timeline is the timeline of the process
    
    # read the bpmn info
    bpmn_dict = read_xml(xml_file)
    
    # get process (pools)
    process = bpmn_dict['bpmn:process']
    
    N = {}
    F = {}
    
    cnt = -1
    
    # read each pool
    if type(process) != list:
        # handle single diagram case
        process = [process]
    # end if
    for diagram in process:
        cnt += 1
        # read current diagram
        diag_name, Ndiag, Fdiag = read_diagram(diagram)
        
        # if diagram empty, skip it
        if len(Ndiag) == 0:
            continue
        # end if
        
        # if diagram is timeline, store it separately
        if diag_name.lower() == 'timeline':
            Ntimeline = Ndiag
            Ftimeline = Fdiag
            Timeline = {'nodes': Ntimeline, 'flows': Ftimeline}
            
            continue
        # end if
        
        # else, append Ndiag, Fdiag in total
        N[cnt] = Ndiag
        F[cnt] = Fdiag
    # end for
    
    # ready, return
    return N, F, Timeline
# end func

#%% function - remove_dangling_diag

def remove_dangling_diag(Ndiag, Fdiag):
    # remove dangling nodes and flows from a diagram
    # Input:
    #    > Ndiag, Fdiag: diagram nodes and flows (dicts, see prev.)
    # Output:
    #    > Nnew, Fnew: the new diagram, with dangling nodes and flows removed
    #    > has_dangling: True if the original diagram had dangling nodes/flows, False else
    
    Nnew = {}
    Fnew = {}
    
    # for all nodes
    for nID in Ndiag.keys():
        # each node not 'start' or 'end' must have at least one parent and one child
        # the start node must have no parents and one child
        # then end node must have at least one parent and no children
        
        # get type of node
        n_type = Ndiag[nID]['type']
        # get also number of parents and children
        n_parents = len( utils_process.get_parents(nID, Ndiag, Fdiag) )
        n_children = len( utils_process.get_children(nID, Ndiag, Fdiag) )
        
        # check cases
        if n_type not in ['start', 'end'] and n_parents >= 1 and n_children >= 1:
            Nnew[nID] = Ndiag[nID].copy()
        # end if
        
        if n_type == 'start':
            if n_children >= 1 and n_parents == 0:
                Nnew[nID] = Ndiag[nID].copy()
                continue
            else:
                # if the start node is wrong, then we have an error, return None
                return {}, {}, True
            # end if
        # end if
        
        if n_type == 'end':
            if n_parents >= 1 and n_children == 0:
                Nnew[nID] = Ndiag[nID].copy()
                continue
            else:
                # if the start node is wrong, then we have an error, return None
                return {}, {}, True
            # end if
        # end if
    # end for
    
    # now remove also dangling flows
    for fl in Fdiag.keys():
        # get flow
        nID1, nID2 = fl
        
        # both nodes must be in Nnew
        if nID1 in Nnew.keys() and nID2 in Nnew.keys():
            Fnew[fl] = Fdiag[fl]
        # end if
    # end for
    
    if len(Nnew) < len(Ndiag) or len(Fnew) < len(Fdiag):
        has_dangling = True
    else:
        has_dangling = False
    # end if
    
    return Nnew, Fnew, has_dangling
# end func


#%% function - remove_dangling_proc

def remove_dangling_proc(Nall, Fall, Timeline = None, Fmsg = None):
    # remove dangling nodes and flows from a process
    # Input:
    #    > Nall, Fall: diagram nodes and flows for all diagrams
    # Output:
    #    > Nnew, Fnew: the new process, with dangling nodes and flows removed
    #    > Timeline_new, Fmsg_new: the new timeline or message flows (otpional)
    
    Nnew = {}
    Fnew = {}
    Timeline_new = {}
    Fmsg_new = {}
    
    # for all diagrams of the process
    for i in range( len(Nall) ):
        # remove danglings of diagram i
        Nnew_diag, Fnew_diag, has_dangling = remove_dangling_diag(Nall[i], Fall[i])
        # if still dangling remain, return error (we remove only single-level)
        # dangling nodes and not dangling paths etc
        _, _, has_dangling = remove_dangling_diag(Nnew_diag, Fnew_diag)
        if has_dangling:
            return {}, {}, {}, {}
        # end if
        
        # else, put new diagram in
        Nnew[i] = Nnew_diag.copy()
        Fnew[i] = Fnew_diag.copy()
    # end for
    
    # fix also timeline and msg flows if available
    if Timeline is not None:
        # get nodes and flows of timeline
        TN = Timeline['nodes']
        TF = Timeline['flows']
        
        # remove dandling
        TNnew, TFnew, has_dangling = remove_dangling_diag(TN, TF)
        # if still dangling remain, return error (we remove only single-level)
        # dangling nodes and not dangling paths etc
        _, _, has_dangling = remove_dangling_diag(TNnew, TFnew)
        if has_dangling:
            return {}, {}, {}, {}
        # end if
        
        # else Timeline fixed
        Timeline_new = {'nodes': TNnew, 'flows': TFnew}
    # end if
    
    # fix also msg flows if available
    if Fmsg is not None:
        for fl in Fmsg.keys():
            # get flow nID1 -> nID2
            nID1, nID2 = fl
            # check if both nodes exist
            diag1, _, _ = utils_process.get_diag_name_type(nID1, Nnew)
            diag2, _, _ = utils_process.get_diag_name_type(nID2, Nnew)
            # if both exist => flow exists => add it in
            if diag1 is not None and diag2 is not None:
                Fmsg_new[fl] = ''
            # end if
        # end for
    # end if
    
    # ready
    return Nnew, Fnew, Timeline_new, Fmsg_new        
# end func



        
        
        
            
        
        

