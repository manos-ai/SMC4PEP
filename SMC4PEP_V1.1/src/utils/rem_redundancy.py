# -*- coding: utf-8 -*-
"""
remove redundancy
"""

#%% imports

import numpy as np

# own modules
import utils_read
import utils_process


#%% function - check_equal_diag

def check_equal_diag(N1, F1, N2, F2):
    # check if the 2 diagrams (N1, F1) and (N2, F2) are the same
    # same means this: diag1 and diag2 have the same node names and types
    # Input:
    #    > N1, F1, N2, F2: nodes and flows of diagram 1 and 2 respectively
    #                      see utils_read for data struct details of N, F
    # Output:
    #    > are_equal: boolean, True or False
    
    # find start node of diags 1 and 2
    startID1 = utils_process.find_start(N1)
    startID2 = utils_process.find_start(N2)
    
    # starting from the start nodes, do pairwise BFS on both
    # diagrams. Check that every node has the same children (in name and type)
    # If this is true for all nodes, return equal. Else, not equal
    
    # queues 1 and 2 and visited nodes lists
    Q1 = [startID1]
    V1 = []
    Q2 = [startID2]
    V2 = []
    
    while Q1 != [] and Q2 != []:
        # pop nodes from Q1 and Q2
        node1 = Q1.pop(0)
        node2 = Q2.pop(0)
        
        # append to visited
        if node1 not in V1:
            V1.append(node1)
        # end if
        if node2 not in V2:
            V2.append(node2)
        # end if
        
        # check if they are equal
        type1 = N1[node1]['type']
        type2 = N2[node2]['type']
        
        if type1 != type2:
            # types are different, diagrams not equal
            return False
        # end if
        
        # next, if the nodes are not gates, then check also the names
        if type1 not in ['fork', 'join', 'decision']:
            name1 = N1[node1]['name']
            name2 = N2[node2]['name']
            
            if name1 != name2:
                # names are not the same, diagrams not equal
                return False
            # end if
        # end if
        
        # get the children of node1 and node2
        children1 = utils_process.get_children(node1, N1, F1)
        children2 = utils_process.get_children(node2, N2, F2)
        
        # keep only the unvisited children
        unvisited_children1 = []
        unvisited_children2 = []
        
        for child1 in children1:
            if child1 not in V1: 
                unvisited_children1.append(child1)
            # end if
        # end for
        for child2 in children2:
            if child2 not in V2: 
                unvisited_children2.append(child2)
            # end if
        # end for
        
        # now, for each child in children1, find an equal child in children2
        corresp_children2 = []
        unvisited_children2_temp = unvisited_children2.copy()
        
        for child1 in unvisited_children1:
            children_list2 = unvisited_children2_temp.copy()
            for child2 in children_list2:
                # check if they are equal
                name1 = N1[child1]['name']
                type1 = N1[child1]['type']
                
                name2 = N2[child2]['name']
                type2 = N2[child2]['type']
                
                if type1 != type2:
                    continue
                # end if
                
                if type1 not in ['fork', 'join', 'decision']:
                    if name1 != name2:
                        continue
                    # end if
                # end if
                
                # if equal, then add child2 as corresponding child to child1
                # and remove it from the children2 list (since it's already
                # matched with child1)
                corresp_children2.append(child2)
                unvisited_children2_temp.remove(child2)
                # finally, since we found the child, break the inner loop
                break
            # end for
        # end for
        
        # if a child is left unmatched, then diagrams are not equal
        if len(unvisited_children2) != len(corresp_children2):
            # some children in 2 are left unmatched - diagrams not equal
            return False
        # end if
        
        # finally, append the unvisited children in the queues
        # in Q2, we append the corresp children, so that the 
        # matching children get in the 2 queues in the same order
        Q1 = Q1 + unvisited_children1
        Q2 = Q2 + corresp_children2
    # end while
    
    # final check: if a queue is empty but the other not, diagrams are unequal
    if len(Q1) != len(Q2):
        # both sould be zero, else unequal
        return False
    # end if
    
    # if we reach here, all checks are correct - diagrams equal!
    return True        
# end func


#%% function - get_events

def get_events(Nall, Fall):
    # finds the events that match with each other
    # Input:
    #    > Nall, Fall: all nodes and flows of a process (all diagrams)
    #                  {diag_id}: Ndiag (and Fdiag respectivly)
    #                  where Ndiag = dict of type [node_id]:{name, type} (see
    #                  before), Fdiag = dict [(source, target)]: label
    # Output:
    #    > Eall: dict of all events in the process, of type [diag_id]: [eventID1, eventID2,..]
    
    Eall = {} # inti
    
    for i in range(len(Nall)):
        # init evry diagram with an empty list of event IDs
        Eall[i] = []
    # end for
    
    # for all diagrams i
    for i in range(len(Nall)):
        # for all nodes of diagram i
        for nIDi in Nall[i].keys():
            # if node is an event, add it to the list
            if Nall[i][nIDi]['type'] in ['event', 'start', 'end']:
                Eall[i].append(nIDi)
            # end if
        # end for
    # end for
    
    return Eall
# end func


#%% function - pools_or_events

def pools_or_events(Eall):
    # check if a process is written in pool or event form
    # Input:
    #    > Eall: dict of all events in the process, of type [diag_id]: [eventID1, eventID2,..]
    #            computed by function get_events
    # Output:
    #    > process_type: either 'pool' or 'event'
    
    # find the total number of events in the process
    n_events = 0
    for i in range(len(Eall)):
        # add the events of diagram i
        n_events += len(Eall[i])
    # end for
    
    if n_events == 0:
        # no events found => pools
        process_type = 'pool'
    else:
        # events found => events
        process_type = 'event'
    # end if
    
    return process_type
# end func


#%% function - interm_event_name_type

def interm_event_name_type(ev_full_name):
    # for intermediate events that are connected, get their name and type
    # intermediate events should be in the form like 'Start X'
    # then the name is 'X' and the type is 'Start'
    # Input:
    #    > ev_full_name: full name of an evnt (like 'Start X')
    # Output:
    #    > ev_type, ev_name: type and name of the event (like 'Start', 'X')
    
    # get pos of gap in 'Start X'
    gap_pos = ev_full_name.find(' ')
    
    # 1st part is the type, 2nd is the name
    ev_type = ev_full_name[:gap_pos]
    ev_name = ev_full_name[(gap_pos + 1):]
    
    # check correctness - type must be either 'Start', End' or 'Int'
    if ev_type not in ['Start', 'End', 'Int']:
        # event has not the correct format for an intermediate connectd event
        # throw error
        raise TypeError('Intermediate event name has not the right form of Start/End/Int X')
    # end if
    
    return ev_type, ev_name
# end func


#%% function - rem_event

def rem_event(eventID, N, F):
    # remove an event from a diagram
    # remove all flows that go to the event and send them to it's child ( events
    # have only one child)
    # example: we have: event -> child
    # for a parent p with p -> event do these
    # 1: remove the flow p -> event
    # 2: add the flow p -> child
    # finally, remove the event from the diagram nodes
    
    # Input:
    #    > eventID: ID of the event
    #    > N, F: nodes and flows of diagram
    # Output:
    #    > Nnew, Fnew: modified nodes and flows, as described above
    
    # if node is not event, do nothing
    if N[eventID]['type'] != 'event':
        return N, F # return as it is
    # end if
    
    Nnew = N.copy()
    Fnew = F.copy()
    
    # get child of event
    child = utils_process.get_children(eventID, N, F)[0] # list of one element
    
    # get parents of event
    parents = utils_process.get_parents(eventID, N, F)
    
    # for all flows
    for flow in F.keys():
        source, target = flow
        label = F[flow]
        
        # if flow is of type event -> child, remove it
        if source == eventID and target == child:
            Fnew.pop(flow)
        # end if
        
        # if flow is of type parent -> event, then
        if source in parents and target == eventID:
            # remove flow parent -> event
            Fnew.pop(flow)
            
            # add flow parent -> child (with same label)
            parent = source
            Fnew[ (parent, child) ] = label 
        # end if
    # end for
    
    # finally, remove event from nodes N
    Nnew.pop(eventID)
    
    # ready
    return Nnew, Fnew
# end for


#%% function - get_msg_flow_events

def get_msg_flow_events(ev_source, ev_target, diag_source, diag_target, N, F):
    # add a msg flow from the parent task of ev_source to the parent of ev_target
    # that is, we have: task1 -> ev_source in diag1 and task2 -> ev_target in diag2
    # now we connect task1 and task2 with the messag flow task1 ---> task2
    # Input:
    #    > ev_source, ev_target: the source and target events (IDs)
    #    > diag_source, diag_target: the source and target diagrams
    #    > N, F: nodes and flow of the (event- based) process
    # Output:
    #    > flow: the message flow (task1, task2)
    
    # get parents of ev_source
    parents = utils_process.get_parents(ev_source, N[diag_source], F[diag_source])
    
    # find task among parents (must be only one)
    for node in parents:
        if N[diag_source][node]['type'] == 'task':
            task1 = node
            break
        # end if
    # end for
    
    # same for event_target
    # get parents of ev_target
    parents = utils_process.get_parents(ev_target, N[diag_target], F[diag_target])
    
    # find task among parents (must be only one)
    for node in parents:
        if N[diag_target][node]['type'] == 'task':
            task2 = node
            break
        # end if
    # end for
    
    # return message flow between task1 and task2
    flow = (task1, task2)
    return flow
# end func


#%% function - conn_events_to_msg_flows

def conn_events_to_msg_flows(Emsg, Nall, Fall):
    # convert a list of matching events Emsg into a the corresponding
    # msg flows in a pool-based diagram. For each matching events pair (ev1, ev2),
    # a msg flow between their parents par1->par2 is created
    # Input:
    #    > Emsg: dict of corresponding events in the form [(evID1, evID2)] -> label,
    #            e.g. ev1->ev2
    #    > Nall, Fall: nodes and flows of all process diagrams (list of dicts, see before)
    # Output:
    #    > Fmsg: the corresponding msg flows of the diagram, in the form [(par1, par2)] -> label
    
    Fmsg = {} # init
    
    # for all event pairs
    for ev_pair in Emsg.keys():
        # get the events
        evID1, evID2 = ev_pair
        
        # get the event diagrams
        diag1, _, _ = utils_process.get_diag_name_type(evID1, Nall)
        diag2, _, _ = utils_process.get_diag_name_type(evID2, Nall)
        
        # find the corresponding message flow
        flow = get_msg_flow_events(evID1, evID2, diag1, diag2, Nall, Fall)
        
        # add it to the flows list (labels are just empty here, no probabilities etc)
        Fmsg[flow] = ''
    # end for
    
    return Fmsg
# end func


#%% function - remove_events

def remove_events(eventIDs, Nall, Fall):
    # remove a list of events from a process
    # Input:
    #    > eventIDs: list of the events (IDs) to be removed
    #    > Nall, Fall: nodes and flows of all process diagrams (list of dicts, see before)
    # Output:
    #    > Nnew, Fnew: new process with the events removed
    
    Nnew = Nall.copy()
    Fnew = Fall.copy()
    
    for evID in eventIDs:
        # get diagram of event
        ev_diag, _, _ = utils_process.get_diag_name_type(evID, Nnew)
        # remove that event
        Nnew_diag, Fnew_diag = rem_event(evID, Nnew[ev_diag], Fnew[ev_diag])
        # append diagram in new
        Nnew[ev_diag] = Nnew_diag.copy()
        Fnew[ev_diag] = Fnew_diag.copy()
    # end for
    
    return Nnew, Fnew
# end func


#%% function - remove_equal_diagrams

def remove_equal_diagrams(Nall, Fall):
    # remove equal diagrams from a process - two diagrams are equal if they
    # have exactly the same names, types, flows, etc.
    # Input:
    #    > Nall, Fall: nodes and flows of all process diagrams (list of dicts, see before)
    # Output:
    #    > Nnew, Fnew: nw process with equal diagrams removed
    #    > matching_diags: 2D array with arr[i,j] = 1 if diag_i = diag_j, and 0 else
    
    Nnew = Nall.copy()
    Fnew = Fall.copy()
    
    diags_to_remove = [] # the diagrams to be removed
    # array to hold which diagrams are equal. Aij = 1 if diag_i = diag_j
    matching_diags = np.zeros( (len(Nall), len(Nall)), int)
    
    for i in range(len(Nall)):
        # get diagram i
        Ni = Nall[i]
        Fi = Fall[i]
        
        for j in range(i+1, len(Nall)):
            # get diagram j
            Nj = Nall[j]
            Fj = Fall[j]
            
            # check if i and j are equal
            are_equal = check_equal_diag(Ni, Fi, Nj, Fj)
            matching_diags[i, j] = are_equal
            
            # if j is equal to i and not yet in the list, add it
            if are_equal and j not in diags_to_remove:
                diags_to_remove.append(j)
            # end if
        # end for
    # end for
    
    # now, remove the equal diagrams from the process
    for n_diag in diags_to_remove:
        Nnew.pop(n_diag)
        Fnew.pop(n_diag)
    # end for
    
    # return the new process
    return Nnew, Fnew, matching_diags
# end func


#%% function - find_equal_diagrams

def find_equal_diagrams(Nall, Fall):
    # find the equal diagrams in a process - two diagrams are equal if they
    # have exactly the same names, types, flows, etc.
    # Input:
    #    > Nall, Fall: nodes and flows of all process diagrams (list of dicts, see before)
    # Output:
    #    > Nnew, Fnew: nw process with equal diagrams removed
    #    > matching_diags: 2D array with arr[i,j] = 1 if diag_i = diag_j, and 0 else
    
    # array to hold which diagrams are equal. Aij = 1 if diag_i = diag_j
    matching_diags = np.zeros( (len(Nall), len(Nall)), int)
    
    for i in range(len(Nall)):
        # get diagram i
        Ni = Nall[i]
        Fi = Fall[i]
        
        for j in range(i+1, len(Nall)):
            # get diagram j
            Nj = Nall[j]
            Fj = Fall[j]
            
            # check if i and j are equal
            are_equal = check_equal_diag(Ni, Fi, Nj, Fj)
            matching_diags[i, j] = are_equal
        # end for
    # end for
    
    # return the new process
    return matching_diags
# end func


#%% function check_nodes_match

def check_nodes_match(nodeIDs1, N1, nodeIDs2, N2):
    # check if two lists of nodes match with each other - e.g. are the same
    # the two lists must be equal, up to reordering
    # Input:
    #    > nodeIDs1, nodeIDs2: lists of nodes to check 
    #    > N1, N2: nodes of the two diagrams
    
    # get names and types of nodes in a list
    nodes1 = []
    
    for nID1 in nodeIDs1:
        n_name = N1[nID1]['name']
        n_type = N1[nID1]['type']
        n_info = (n_name, n_type)
        nodes1.append(n_info)
    # end for
    
    nodes2 = []
    
    for nID2 in nodeIDs2:
        n_name = N2[nID2]['name']
        n_type = N2[nID2]['type']
        n_info = (n_name, n_type)
        nodes2.append(n_info)
    # end for
    
    # check if lists are equal, by converting them in sets
    if set(nodes1) == set(nodes2):
        return True
    else:
        return False
    # end if
# end func
        
        
#%% function - find_corresp_node

def find_corresp_node(nID1, N1, F1, N2, F2):
    # given two equal diagrams N1,F1 and N2,F2, and a node nID1 of diag 1,
    # find the corresponding node nID2 in diag 2. It must be in the same
    # position and have the same parents and children with nID1
    # Input:
    #    > nID1: node (ID) of diagram 1
    #    > N1,F1 and N2,F2: nodes and flows of diag 1 and 2 respectively
    # Output:
    #    > nID2: node ID of th correpsonding node in diag 2
    
    # if diagrams not equal, error, return None
    if check_equal_diag(N1, F1, N2, F2) == False:
        return None
    # end if
    
    # get start of diag1
    start1 = utils_process.find_start(N1)
    # get depth of nID1 (distance from the start)
    depth1 = utils_process.path_len(start1, nID1, N1, F1)
    
    # get parents and children of node 1
    parents1 = utils_process.get_parents(nID1, N1, F1)
    children1 = utils_process.get_children(nID1, N1, F1)
    
    # get start of diag 2
    start2 = utils_process.find_start(N2)
    
    # for all nodes in diag2
    for nID2 in N2.keys():
        # get depth of nID2
        depth2 = utils_process.path_len(start2, nID2, N2, F2)
        
        # get parents and children of node 2
        parents2 = utils_process.get_parents(nID2, N2, F2)
        children2 = utils_process.get_children(nID2, N2, F2)
        
        # check if depths, parents and children are equal
        parents_equal = check_nodes_match(parents1, N1, parents2, N2)
        children_equal = check_nodes_match(children1, N1, children2, N2)
        
        if depth1 == depth2 and parents_equal and children_equal:
            # corresponding node, found, return
            return nID2
        # end if
    # end for
    
    return None # in case not found
# end func


#%% function - diag_equal_to

def diag_equal_to(n_diag, matching_diags):
    # for a given diagram with number n_diag, find if another
    # diagram is equal to it (and thus, n_diag should be replaced)
    # Input:
    #    > mathing_diags: an array showing which diagrams are equal (computed from
    #                     the function remove_equal_diagrams). Aij = 1 if diag_i = diag_j
    # Output:
    #    > n_diag_eq: the diagram number that is equal to n_diag, or -1 if such
    #                 diagram doesn't exist
    
    # we alwyas replace diagrams in numerical order
    # that is, if diag1 = diag2, we always keep diag1 and remove diag2
    
    # get column n_diag from mathcing_diags
    matches = matching_diags[:, n_diag]
    # keep only the elements up to n_diag-1, because n_diag will be
    # replaced only by a previous diagram (if any)
    matches = matches[:n_diag - 1]
    
    # find the 1st 1 in this array
    idx = np.where(matches == 1)[0]
    
    # if no 1 found, then no matching diagram, return None
    if len(idx) == 0:
        return None
    # end if
    
    # else, return the 1st match found
    idx = np.array(idx)
    idx.sort()
    n_diag_eq = idx[0]
    
    return n_diag_eq
# end func
        

#%% function - rem_redund_fix_flows

def rem_redund_fix_flows(Fmsg, Nall, Fall, matching_diags):
    # fix the message flow after we remove the redundant diagrams
    # if the nodes nID1 -> nID2 of a flow f belong to a redundant
    # diagram that was removed, then we have to redirect the flow
    # like f' = nID1' -> nID2', where nID1' is the equivalent of 
    # nID1 on the non-removed diagram
    # Input:
    #    > Fmsg: the original message flows of the process
    #    > Nall, Fall: the original nodes and flows of the process
    #    > mathing_diags: an array showing which diagrams are equal (computed from
    #                     the function remove_equal_diagrams). Aij = 1 if diag_i = diag_j
    # Output:
    #    > Fmsg_new: the new (fixed) message flows 
    
    Fmsg_new = {} # init
    
    # for each msg flow
    for fl in Fmsg.keys():
        # get the flow's nodes nID1 -> nID2
        nID1, nID2 = fl
        
        # find diagrams of nID1 and nID2
        diag1, _, _ = utils_process.get_diag_name_type(nID1, Nall)
        diag2, _, _ = utils_process.get_diag_name_type(nID2, Nall)
        
        # check if either diag1 or diag2 are redundant
        diag1_equal = diag_equal_to(diag1, matching_diags)
        diag2_equal = diag_equal_to(diag2, matching_diags)
        
        # if a diagram is equal to another, find the corresponding node there
        if diag1_equal is not None:
            nID1_equal = find_corresp_node(nID1, Nall[diag1], Fall[diag1], 
                                           Nall[diag1_equal], Fall[diag1_equal])
        else:
            # else keep node as it is
            nID1_equal = nID1
        # end if
        
        # same for node 2
        if diag2_equal is not None:
            nID2_equal = find_corresp_node(nID2, Nall[diag2], Fall[diag2], 
                                           Nall[diag2_equal], Fall[diag2_equal])
        else:
            # else keep node as it is
            nID2_equal = nID2
        # end if
        
        # the new msg flow is now: nID1_equal -> nID2_equal, make it
        Fmsg_new[(nID1_equal, nID2_equal)] = ''
    # end for
    
    return Fmsg_new
# end func
    

#%% function - remove_redundancy
            
def remove_redundancy(Nall, Fall, Fmsg):       
    # remove redundancies in a pool - based process
    # Input:
    #    > Nall, Fall: the original nodes and flows of the process
    #    > Fmsg: the original message flows of the process
    # Output:
    #    > Nall_new, Fall_new, Fmsg_new: the new process (without redundancy)
    
    
    # find the diagrams that are equal
    matching_diags = find_equal_diagrams(Nall, Fall)
    
    # fix the msg flows (remove flows from redundant diagrams and redirect)
    Fmsg_new = rem_redund_fix_flows(Fmsg, Nall, Fall, matching_diags)
    
    # finally, remove the redundant diagrams
    Nall_new, Fall_new, _ = remove_equal_diagrams(Nall, Fall)
    
    # ready
    return Nall_new, Fall_new, Fmsg_new
# end func
        

#%% function - convert_events_to_pools

def convert_events_to_pools(Nall, Fall):
    # convert an event-based process into a pool-based one
    # we find the corresponding events and connect them with a message flow
    # finally, we remove the events
    # Input:
    #    > Nall, Fall: the original nodes and flows of the process
    # Output:
    #    > Nall_new, Fall_new, Fmsg_new: the new process (pool-based)
    
    # get all events of the process
    Eall = get_events(Nall, Fall)
    
    # find the matching events
    Emsg = find_matching_events3(Nall, Fall, Eall)
    
    # from the matching events, get the message flows
    Fmsg_new = conn_events_to_msg_flows(Emsg, Nall, Fall)
    
    # get the list of events
    eventIDs = utils_process.get_flow_nodes(Emsg)
    
    # finally, remove the events
    Nall_new, Fall_new = remove_events(eventIDs, Nall, Fall)
    
    # ready
    return Nall_new, Fall_new, Fmsg_new
# end func


#%% function - event_handler_Int

def event_handler_Int(evIDi, diag_i, Nall, Fall, Eall, Emsg):
    # a helper function for matching the corresponding events in the diagrams
    # given an event ID in diagram i, it tries to find the corresponding events
    # in diag j. This function searches for the "triangles" of the form
    # evIDi --> evIDj1 -> ... -> evIDj2 --> evIDi
    # Input:
    #    > evIDi: event ID in diag_i
    #    > diag_i: nomuber of diagram i
    #    > Nall, Fall: nodes and flows of the process
    #    > Eall: dict of all events in the process, of type [diag_id]: [eventID1, eventID2,..]
    #            computed by function get_events
    #    > Emsg: dict of the msg flows in the form (evID1, evID2): ''
    # Output:
    #    > Emsg: new found flows will be appended in the dict
    
    # sanity check: 0 <= diag_i < len(Nall)
    if diag_i < 0 or diag_i >= len(Nall):
        raise ValueError('Diagram number must be >= 0 and < len(Nall)!')
    # end if
    
    # get name and type of event
    evi_type, evi_name = interm_event_name_type( Nall[diag_i][evIDi]['name'] )
    
    # if the event is not Int, the handler returns
    if evi_type != 'Int':
        return
    # end if
    
    # search all other diagrams
    diag_j_found = False
    diag_j = None
    evIDs_Xj = []
    for j in range(len(Eall)):
        if j == diag_i:
            continue
        # end if
        for nIDj in Eall[j]:
            # get name and type of event
            evj_type, evj_name = interm_event_name_type( Nall[j][nIDj]['name'] )
            # if same name with event nIDi, add it in the list
            if evj_name == evi_name:
                evIDs_Xj.append(nIDj)
                diag_j_found = True
            # end if
        # end for
        if diag_j_found == True:
            diag_j = j
            break
        # end if
    # end for
    
    # if not found, return
    if diag_j_found == False:
        return
    # end if
    
    if len(evIDs_Xj) == 2:
        # for the traingle we need to find two events
        # this is the case where the event i triggers the 1st event in j
        # and waits until j reaches the 2nd event
        # first, order the events of diag j
        evIDj1, evIDj2 = utils_process.order_nodes(evIDs_Xj[0], evIDs_Xj[1], Nall[diag_j], Fall[diag_j])

        # all events must be 'Int' otherwise handlre returns
        evj1_type, evj1_name = interm_event_name_type( Nall[diag_j][evIDj1]['name'] )
        evj2_type, evj2_name = interm_event_name_type( Nall[diag_j][evIDj2]['name'] )
        
        if [evj1_type, evj2_type] != ['Int', 'Int']:
            return
        # end if
        
        # now we need to add the following flows:
        # evIDi --> evIDj1 (event i triggers the 1st Int event in j)
        # evIDj2 --> evIDi (event i is triggered back when diag j reaches evIDj2)
        
        Emsg[(evIDi, evIDj1)] = '' # evIDi --> evIDj1
        Emsg[(evIDj2, evIDi)] = '' # evIDj2 --> evIDi
    # end if
    
    # ready, return
    return
# end func


#%% function - event_handler_noInt

def event_handler_noInt(evIDi, diag_i, Nall, Fall, Eall, Emsg):
    # a helper function for matching the corresponding events in the diagrams
    # given an event ID in diagram i, it tries to find the corresponding events
    # in diag j. This function searches for non-triangles, of the form either
    # End_i --> Start_j, End_i --> Int_j
    # Input:
    #    > evIDi: event ID in diag_i
    #    > diag_i: nomuber of diagram i
    #    > Nall, Fall: nodes and flows of the process
    #    > Eall: dict of all events in the process, of type [diag_id]: [eventID1, eventID2,..]
    #            computed by function get_events
    #    > Emsg: dict of the msg flows in the form (evID1, evID2): ''
    # Output:
    #    > Emsg: new found flows will be appended in the dict
    
    # sanity check: 0 <= diag_i < len(Nall)
    if diag_i < 0 or diag_i >= len(Nall):
        raise ValueError('Diagram number must be >= 0 and < len(Nall)!')
    # end if
    
    # get name and type of event
    evi_type, evi_name = interm_event_name_type( Nall[diag_i][evIDi]['name'] )
    
    # if the event is not End, the handler returns
    if evi_type != 'End':
        return
    # end if
    
    # search all other diagrams
    diag_j_found = False
    diag_j = None
    evIDj = None
    for j in range(len(Eall)):
        if j == diag_i:
            continue
        # end if
        for nIDj in Eall[j]:
            # get name and type of event
            evj_type, evj_name = interm_event_name_type( Nall[j][nIDj]['name'] )
            # if same name with event nIDi, stop search
            if evj_name == evi_name:
                evIDj = nIDj
                diag_j_found = True
                diag_j = j
                break
            # end if
        # end for
        if diag_j_found == True:
            diag_j = j
            break
        # end if
    # end for
    
    # if not found, return
    if diag_j_found == False:
        return
    # end if
    
    # check that the type of the other event is either 'Int' or 'Start'
    evj_type, evj_name = interm_event_name_type( Nall[diag_j][evIDj]['name'] )
    if evj_type not in ['Int', 'Start']:
        # if not, return
        return
    # end if
    
    # otherwise add the flow evIDi --> evIDj
    Emsg[(evIDi, evIDj)] = '' # evIDi --> evIDj
    
    # ready, return
    return
# end func


#%% function - find_matching_events3
def find_matching_events3(Nall, Fall, Eall):
    # finds the events that match with each other
    # Input:
    #    > Nall, Fall: all nodes and flows of a process (all diagrams)
    #                  {diag_id}: Ndiag (and Fdiag respectivly)
    #                  where Ndiag = dict of type [node_id]:{name, type} (see
    #                  before), Fdiag = dict [(source, target)]: label
    #    > Eall: dict of all events in the process, of type [diag_id]: [eventID1, eventID2,..]
    #            computed by function get_events
    # Output:
    #    > Emsg: dict of matching events in the form [(sourceID, targetID)]: label
    #            not yet message flow, since the events have to be removed at the
    #            conversion. We only keep which event matches with which
    
    Emsg = {} # init
    
    # the only cases for the flows of diag i are the following:
    # case 1: 'End X' (diag i) --> 'Int X' (diag j)
    # case 2: 'End X' (diag i) --> 'Start X' (diag j)
    # case 3: 'Int X' (diag i) --> 'Int X' no. 1 (diag j) and 'Int X' no.2 (diag j) --> 'Int X' (diag i)
    # case 4: 'Int X' (diag j) --> 'Int X' no. 1 (diag i) and 'Int X' no.2 (diag i) --> 'Int X' (diag j)
    
    # for all diagrams i
    for i in range(len(Eall)):
        # for all events of diagram i
        diag_i = i
        for evIDi in Eall[i]:
            # get name and type of event
            evi_type, evi_name = interm_event_name_type( Nall[i][evIDi]['name'] )
            
            # if type is 'End', we have cases 1 or 2. We call the handler for noInt events
            if evi_type == 'End':
                event_handler_noInt(evIDi, diag_i, Nall, Fall, Eall, Emsg)
            elif evi_type == 'Int':
                # call the Int events handler
                event_handler_Int(evIDi, diag_i, Nall, Fall, Eall, Emsg)
            # end if
            # we don't need to handle other cases; for example the case
            # Start_i --> End_j will be handled by the End_j event of diag j
        # end for
    # end for
    
    # ready, return 
    return Emsg
# end func


#%% function - events_to_flows3

def events_to_flows3(Nall, Fall):
    # convert an event-based process into a pool-based one
    # we find the corresponding events and connect them with a message flow
    # we do not remove the events
    # Input:
    #    > Nall, Fall: the original nodes and flows of the process
    # Output:
    #    > Nall_new, Fall_new, Fmsg_new: the new process (pool-based)
    
    # get all events of the process
    Eall = get_events(Nall, Fall)
    
    # find the matching events
    Emsg = find_matching_events3(Nall, Fall, Eall)
    
    # from the matching events, get the message flows
    Fmsg = Emsg.copy()
    
    # ready
    return Nall, Fall, Fmsg
# end func









    
    
    
    
    

                

