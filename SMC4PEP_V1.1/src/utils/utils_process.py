# -*- coding: utf-8 -*-
"""
utils to process bpmn diagrams
"""

#%% imports

import numpy as np
import matplotlib.pyplot as plt

# own modules
#import correct_diagrams


#%% function - get_children

def get_children(nodeID, Ndiag, Fdiag):
    # get the children of a node
    # Inputs:
    #    > nodeID: ID of node
    #    > Ndiag, Fdiag: nodes and flows of the diagram (see utils_read for details)
    # Outputs:
    #    > children: list of nodes (IDs) that are children of original node
    
    children = []
    
    for flow in Fdiag.keys():
        source, target = flow
        
        if source == nodeID:
            # add target to children list
            children.append(target)
        # end if
    # end for
    
    return children
# end func

#%% function - get_parents

def get_parents(nodeID, Ndiag, Fdiag):
    # get the parents of a node
    # Inputs:
    #    > nodeID: ID of node
    #    > Ndiag, Fdiag: nodes and flows of the diagram (see utils_read for details)
    # Outputs:
    #    > children: list of nodes (IDs) that are children of original node
    
    parents = []
    
    for flow in Fdiag.keys():
        source, target = flow
        
        if target == nodeID:
            # add source to parents list
            parents.append(source)
        # end if
    # end for
    
    return parents
# end func


#%% function - nodeID_fromName

def nodeID_fromName(nodeName, Ndiag):
    # get a node ID from the node's name
    # Inputs:
    #    > nodeName: name node
    #    > Ndiag: nodes of the diagram (see utils_read for details)
    # Outputs:
    #    > nodeID: ID of requested node
    
    for nID in Ndiag.keys():
        if Ndiag[nID]['name'] == nodeName:
            return nID
        # end if
    # end for
    
    # else, wrong name, return None
    return None
# end func


#%% function - get_prob_flow

def get_prob_flow(sourceID, targetID, Ndiag, Fdiag):
    # get the probability of a flow sourceID -> targetID in a diagram
    # Inputs:
    #    > sourceID, targetID: source and target nodes (IDs)
    #    > Ndiag, Fdiag: nodes and flows of diagram (see utils_read for details)
    # Outputs:
    #    > prob: probability of transition
    
    # get flow label
    if (sourceID, targetID) not in Fdiag.keys():
        return -1 # flow doesn't exist
    # end if
    
    label = Fdiag[(sourceID, targetID)]
    if label == '':
        prob = 1 # empty labels have prob 1
    else:
        # for example, if label = '0.5' then prob = 0.5 (convert str to float)
        prob = float(label)
    # end if
    
    return prob
# end func


#%% function - find_start

def find_start(Ndiag):
    # find the start event of a diagram
    # Input:
    #    > Ndiag: diagram nodes (see utils_read for details)
    # Output:
    #    > startID: the ID of start event in N, or None if no start event
    
    for nID in Ndiag.keys():
        if Ndiag[nID]['type'] == 'start':
            return nID
        # end if
    # end for
    
    # no start found, return None
    return None
# end func


#%% function - find_end

def find_end(Ndiag):
    # find the start event of a diagram
    # Input:
    #    > Ndiag: diagram nodes (see utils_read for details)
    # Output:
    #    > startID: the ID of start event in N, or None if no start event
    
    for nID in Ndiag.keys():
        if Ndiag[nID]['type'] == 'end':
            return nID
        # end if
    # end for
    
    # no start found, return None
    return None
# end func
        

#%% function - path_len

def path_len(node1, node2, Ndiag, Fdiag):
    # computes the length of the shortest path from node1 to node2
    # Input:
    #    > node1, node2: two nodes (IDs)
    #    > Ndiag, FdiagL nodes and flwos of the diagram
    # Output:
    #    > pathlen: the length of the path node1 -> node2, or -1 if no path
    
    # we will start a BFS from node1. If we see node2, then it's after
    # else it's not
    
    Q = [(node1, 0)] # queue with node1 at start
    # Q contains pairs of the form: (node_i, path_len from node1)
    V = [] # list of visited nodes
    
    while Q != []:
        # while Q not empty
        node, pathlen = Q.pop(0) # get current node and dist
        
        # if we see node2, then finish
        if node == node2:
            return pathlen 
        # end if
        
        if node in V:
            # if already visited, skip
            continue
        # end if
        
        V.append(node)
        
        # get children of node
        children = get_children(node, Ndiag, Fdiag)
        
        # append children to Q
        # children dist is increased by 1
        pathlen += 1
        for child in children:
            Q.append( (child, pathlen) )
        # end for
    # end while
    
    # node2 unseen, return False
    return -1
# end func


#%% function - order two nodes

def order_nodes(node1, node2, Ndiag, Fdiag):
    # given two nodes, permute them such as node1 is before node2
    # if not possible return None
    # Input:
    #    > node1, node2: two nodes in a diagram
    #    > Ndiag, Fdiag: nodes and flows of the diagram
    # Output:
    #    > (node_before, node_after): correct order of nodes (or None if error)
    
    # find the start node of Ndiag
    startID = find_start(Ndiag)
    
    # get path length from start to node1 and node2
    pathlen01 = path_len(startID, node1, Ndiag, Fdiag)
    pathlen02 = path_len(startID, node2, Ndiag, Fdiag)
    
    # get also the path from the 1st node th the 2nd
    if pathlen01 < pathlen02:
        first = node1
        second = node2
    else:
        first = node2
        second = node1
    # end if
    
    # path len from first to second
    pathlen12 = path_len(first, second, Ndiag, Fdiag)
    
    # if there is a path from first to second, then the order is (first, second)
    # also, the path12 must not contain loops. This will be the case if path12 <
    # path start -> second. But this is the max of path01 and path02
    if pathlen12 != -1 and pathlen12 <= max(pathlen01, pathlen02):
        return (first, second)
    else:
        # if no path from 1st to 2nd, then the nodes are not connected - return None
        return None
    # end if    
# end func


#%% function - get_diag_name_type

def get_diag_name_type(nID, Nall):
    # get diagram number and name, type of a node of a process
    # Input:
    #    > nID: node ID
    #    > Nall: list [Ndiag1, Ndiag2, ...] for all diagrams, where Ndiagi
    #            is a dict containing the nodes of diagram i (see previous)
    # Output:
    #    > n_diag, n_name, n_type: the node's diagram and name, type
    
    node_found = False
    # init to None - return None if node not found
    n_diag = None
    n_name = None
    n_type = None
    
    for i in range(len(Nall)):
        for nIDi in Nall[i].keys():
            if nIDi == nID:
                n_diag = i
                n_name = Nall[i][nIDi]['name']
                n_type = Nall[i][nIDi]['type']
                node_found = True
                break
            # end if
        # end for
        if node_found:
            break
        # end if
    # end for
    
    return n_diag, n_name, n_type
# end func


#%% function - get_flow_nodes

def get_flow_nodes(F):
    # from a list of flows, get the corresponding (unique) nodes involved
    # Input:
    #    > F: input flows of the form: dict[(sourceID, tagretID)] -> label
    # Output:
    #    > nodeIDs: list of the IDs of the nodes found
    
    nodeIDs = []
    
    for fl in F.keys():
        # get source and target node of flow
        nID1, nID2 = fl
        
        # if source or target event not already in list, add it
        if nID1 not in nodeIDs:
            nodeIDs.append(nID1)
        # end if
        if nID2 not in nodeIDs:
            nodeIDs.append(nID2)
        # end if
    # end for
    
    return nodeIDs
# end func


#%% function - find_forward_children

def find_forward_children(nodeID, Ndiag, Fdiag):
    # find the children of nodeID that go forward and not return back
    # e.g., from a decision gate, find the children that go ahead, not back
    # Input:
    #    > nodeID: the ID of the node where we need the children
    # Ndiag, Fdiag: nodes and flows of the diagram, see above functions for details
    # Output:
    #    > forw_children: list containing the IDs of the "forward" children, or empty list
    #                     if they don't exist
    
    # get all children
    all_children = get_children(nodeID, Ndiag, Fdiag)
    
    # for each child in all_children, check if the path nodeID -> child exists
    # if that's the case, it is a forward child, add ot to the list
    forw_children = []
    
    for childID in all_children:
        if order_nodes(nodeID, childID, Ndiag, Fdiag) == (nodeID, childID):
            # the ordering nodeID -> childID is correct
            forw_children.append(childID)
        # end if
    # end for
    
    # ready
    return forw_children
# end func


#%% function - node_order

def node_order(nID1, nID2, Ndiag, Fdiag):
    # find the order of tow nodes nID1, nID2 in a diagram Ndiag, Fdiag
    # e.g. check if nID1 = nID2 (they are the same), nID1 < nID2 (e.g. nID1 is behind
    # nID2), or nID1 > nID2 (e.g. nID1 is after nID2)
    # Input:
    #    > nID1, nID2: the IDs of the two nodes
    #    > Ndiag, Fdiag: nodes and flows of the diagram
    # Output:
    #    > n_order: either 'equal', 'before', 'after', or 'invalid' if a node is
    #               not in the diagram or there's no path between them
    
    if nID1 == nID2:
        n_order = 'same'
        return n_order
    # end if
    
    if order_nodes(nID1, nID2, Ndiag, Fdiag) == (nID1, nID2):
        # nID1 is before nID2
        n_order = 'before' # e.g. nID1 is before nID2
        return n_order
    elif order_nodes(nID1, nID2, Ndiag, Fdiag) == (nID2, nID1):
        # nID1 is after nID2
        n_order = 'after' # e.g. nID1 is before nID2
        return n_order
    else:
        # invalid result; some node is missing from Ndiag, and 'order_nodes' returns None
        # or no path nID1 -> nID2 (parallel branches)
        n_order = 'invalid' # e.g. nID1 is before nID2
        return n_order 
    # end if
# end func


#%% function - order_diag_nodes

def order_diag_nodes(Ndiag, Fdiag):
    # order the nodes of a diagram Ndiag in a BFS way, so that the 1st node
    # is always the start, and subsequent nodes in Ndiag are ordered by their depths
    # Input:
    #    > Ndiag, Fdiag: nodes and flows of the diagram
    # Output:
    #    > Ndiag_ord: the same diagram, but with nodes ordered by BFS
    
    # find the start node
    startID = find_start(Ndiag)
    
    # start BFS from start, and append nodes as we discover them 
    Ndiag_ord = {}
    
    Q = [startID]
    V = []
    
    while Q != []:
        nID = Q.pop(0)
        if nID in V:
            continue
        else:
            V.append(nID)
            Ndiag_ord[nID] = Ndiag[nID] # append new node in Ndiag_ord
        # end if
        
        # get children of nID
        children = get_children(nID, Ndiag, Fdiag)
        
        for chID in children:
            Q.append(chID)
        # end for
    # end while
    
    # ready
    return Ndiag_ord
# end func


#%% function - order_process_nodes

def order_process_nodes(Nall, Fall):
    # for each diagram in a process, order its nodes in a BFS way, so that the 1st node
    # is always the start, and subsequent nodes in Ndiag are ordered by their depths
    # Input:
    #    > Nall, Fall: nodes and flows of the process diagrams
    # Output:
    #    > Nall_new, Fall: the new process where nodes are ordered
    
    Nall_new = []
    
    for diag_i in range(len(Nall)):
        # order the nodes of that diagram
        Ndiag_ord = order_diag_nodes(Nall[diag_i], Fall[diag_i])
        # append it
        Nall_new.append(Ndiag_ord)
    # end for
    
    # ready, return the new process
    return Nall_new, Fall
# end func


#%% function is_deeper

def is_deeper(nID1, nID2, Ndiag, Fdiag):
    # check if nID1 lies deeper than nID2 in the diagram (in a BFS way)
    # Input:
    #    > nID1, nID2: the IDs of the two nodes
    #    > Ndiag, Fdiag: nodes and flows of the diagram
    # Output:
    #    > n_order: either 'equal', 'less deep', 'more deep', or 'invalid' if a node is
    #               not in the diagram
    
    # sanity check
    if nID1 not in Ndiag or nID2 not in Ndiag:
        return 'invalid'
    # end if
    
    if nID1 == nID2:
        return 'equal'
    # end if
    
    # node diag nodes by BFS
    Ndiag_ord = order_diag_nodes(Ndiag, Fdiag)
    
    # check position of the two nodes in the ordered diag
    Ndiag_IDs = list( Ndiag_ord.keys() )
    nID1_pos = Ndiag_IDs.index(nID1)
    nID2_pos = Ndiag_IDs.index(nID2)
    
    if nID1_pos < nID2_pos:
        return 'less deep'
    else: # nID1_pos > nID2_pos
        return 'more deep'
    # end if
# end func



        
    
        
        
        




        
    
        



    

