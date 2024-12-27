# -*- coding: utf-8 -*-
"""
utils to convert a bpmn diagram to prism
"""

#%% imports

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

# own modules
import utils_read
import rem_redundancy
import utils_process


#%% function - lastJoinAnchestor

def lastJoinAnchestor(nodeID, Ndiag, Fdiag):
    # get last join anchestor of node nodeID
    # use reverse BFS
    # Inputs:
    #    > nodeID: a node ID
    #    > Ndiag, Fdiag: nodes and flows of diagram (see utils_process for details)
    # Output:
    #    > join_anchID: ID of last join anchestor of nodeID, or None if not existing
    
    # queue and visited nodes list for BFS
    Q = [nodeID]
    V = []
    join_anchID = None
    found = False
    
    # we to reverse BFS: from the node, get it's parents, and then their parents 
    # etc., until we meet the first join, which we return
    while Q != [] and not found:
        # pop node
        nID = Q.pop(0)
        if nID in V:
            # already visited, continue
            continue
        else:
            # mark as visited
            V.append(nID)
        # end if
        # find parents of nID
        parents = utils_process.get_parents(nID, Ndiag, Fdiag)
        # for all parents
        for parID in parents:
            if Ndiag[parID]['type'] == 'join':
                join_anchID = parID
                found = True
            if parID not in V:
                Q.append(parID)
            # end if
        # end for
    # end while
    
    # finally check that the join found is before the node
    if join_anchID is not None:
        if utils_process.order_nodes(nodeID, join_anchID, Ndiag, Fdiag) == (join_anchID, nodeID):
            return join_anchID
        else:
            # the join found lies after nodeID, it's not an anchestor; return None
            return None
        # end if
    # end if
    
    # otherwise, return none
    return None
# end func


#%% function - diag_to_modules2

def diag_to_modules2(Ndiag, Fdiag):
    # break a diagram down to a list of modules - these will then become prism modules
    # Input:
    #    > Ndiag, Fdiag: diagram nodes and flows (see utils_process for details)
    # Output:
    #    > Modules: list of dicts of type nodeID: (name, type). One dict for each module, 
    #               that contains the module's nodes
    #    > Mod_nodes: dict of type nodeID: module_no, containing the module where each node
    #                 of Ndiag is assigned to
    
    # find the start node
    startID = utils_process.find_start(Ndiag)
    
    # init
    Qs = [[startID]] # one queue for each module, initially only one
    Modules = [{}] # only one module containing the start node
    Mod_nodes = {} # the start goes to the 1st module (module no 0)
    
    V = [] # list of visited nodes
    
    nonmepty_Q = True
    
    # start loop: get 1st open module and expand it
    while True:
        # get 1st non-empty queue
        nonmepty_Q = False
        mod_i = None
        for i in range(len(Qs)):
            Q = Qs[i]
            if Q != []:
                mod_i = i
                nonmepty_Q = True
                break
            # end if
        # end for
        # if all queues empty, we're done (all nodes and modules added)
        if nonmepty_Q == False:
            break
        # end if
            
        # pop node from 
        nID = Qs[mod_i].pop(0)
        
        if nID not in Modules[mod_i]:
            # add visited node into its module
            Modules[mod_i][nID] = Ndiag[nID]
            # mark also the module number of the added node
            Mod_nodes[nID] = mod_i 
            if nID not in V:
                V.append(nID)
            # end if
        else:
            continue
        # end if
        
        # get node type
        # if start, task or join, expand normally
        if Ndiag[nID]['type'] in ['start', 'task', 'join', 'event']:
            # get curr node's children (it's only one)
            next_nodeID = utils_process.get_children(nID, Ndiag, Fdiag)[0]
            
            # if next node is not join, append it in Q
            if Ndiag[next_nodeID]['type'] != 'join':
                Qs[mod_i].append(next_nodeID)
            else:
                # if it's join, make a new queue (module) and put it there
                # unless it's already visited
                if next_nodeID not in V:
                    Qnew = [next_nodeID]
                    Qs.append(Qnew)
                    Modules.append({})
                    V.append(next_nodeID)
                # end if
            # end if
        elif Ndiag[nID]['type'] == 'end':
            # nothing to do
            continue
        elif Ndiag[nID]['type'] == 'fork':
            # get curr node's children
            next_nodes = utils_process.get_children(nID, Ndiag, Fdiag)
            # start a new module with each of them, unless visited
            for chID in next_nodes:
                if chID not in V:
                    Qnew = [chID]   
                    Qs.append(Qnew)
                    Modules.append({})
                    V.append(chID)
                # end if
            # end for
        elif Ndiag[nID]['type'] == 'decision':
            # get curr node's children
            next_nodes = utils_process.get_children(nID, Ndiag, Fdiag)
            
            # append child to module only if it belongs there
            # this happens if it has the same join anchestor as
            # the current node
            for chID in next_nodes:
                if lastJoinAnchestor(chID, Ndiag, Fdiag) == lastJoinAnchestor(nID, Ndiag, Fdiag):
                    Qs[mod_i].append(chID)
                # end if
            # end for
        # end if
    # end while
    
    # ready
    return Modules, Mod_nodes
# end func


#%% function - diag_dependencies

def diag_dependencies(Ndiag, Fdiag, Nall, Fall, Fmsg):
    # find the "critical segments" of other diagrams that diagram Ndiag depends on
    # that is: suppose Ndiag recieves a message flow on node 1 from diagram x, and
    # sends back a message to diagram x at node 5: ev1_x --> node1 -> ... -> node5 --> ev2_x
    # then Ndiag depends on x. We return this as a tuple diag_x: (ev1, ev2) that shows
    # the Ndiag depends on the critical segment ev1 -> ... -> ev2 of diag_x
    # Input:
    #    > Ndiag, Fdiag: the input diagram
    #    > Nall, Fall: all diagrams of the process
    #    > Fmsg: messagel flows of the process, in the form (nID1, nID2)
    # Output:
    #    > critical_segm: a dict of the form diag_x: (ev1_x, ev2_x), showing that
    #                     Ndiag depends on the critical segment ev1_x -> ... -> ev2_x of diag_x
    
    
    critical_segm = {}
    # for each Ndiag_x, critical_segm contains a list of the critical segments
    # fir that diagram: diag_x: [(evID1_x, evID2_x), (evID3_x, evID4_x), ...]
    for i in range(len(Nall)):
        critical_segm[i] = []
    # end for
    
    # for each diagram in the process
    for i in range(len(Nall)):
        Ndiag_x = Nall[i]
        Fdiag_x = Fall[i]
        
        # find all flows that come to Ndiag from Ndiag_x
        Fmsg_in = {} # dict of type sourceID: targetID
        # and all nodes that go Ndiag --> Ndiax_g
        Fmsg_out = {}
        
        for fl in Fmsg:
            # get the flow evID1 --> evID2
            evID1, evID2 = fl
            
            if evID1 in Ndiag_x and evID2 in Ndiag:
                # incoming flow: Ndiag_x --> Ndiag
                #Fmsg_in.append((evID1, evID2))
                Fmsg_in[evID1] = evID2
            elif evID1 in Ndiag and evID2 in Ndiag_x:
                # outgoing flow: Ndiag --> Ndiag_x
                #Fmsg_out.append((evID1, evID2))
                Fmsg_out[evID1] = evID2
            # end if
        # end for
        
        # now, we have all flows Ndiag_x --> Ndiag, and Ndiag --> Ndiag_x
        # we need to find the critical segments: 
        # evID1_x --> evID1 -> taskID1 -> ... -> evID2 --> evID2_x
        
        # to do this, we pop one incoming flow evID1_x --> evID1
        # from there, we search for the nearest outgoing flow evID2 --> evID2_x
        # such that: evID2 >= evID1 and evID2_x >= evID1_x; e.g. evID2 is after
        # evID1 and evID2_x is after evID1_x
        
        for evID1_x in Fmsg_in:
            # get an incoming flow
            evID1 = Fmsg_in[evID1_x]
            
            # start BFS from evID, until we find some evID2 so that 
            # there's a flow evID2 --> evID2_x with evID2_x >= evID1_x
            Q = [evID1]
            V = []
            
            while Q != []:
                nID = Q.pop(0)
                
                if nID in Fmsg_out:
                    evID2_x =  Fmsg_out[nID]
                    if utils_process.order_nodes(evID1_x, evID2_x, Ndiag_x, Fdiag_x) == (evID1_x, evID2_x):
                        # evID2_x is after evID1_x, we found it
                        # so (evID1_x, evID2_x) is a critical segment
                        critical_segm[i].append((evID1_x, evID2_x))
                        break
                    # end if
                # end if
                        
                
                if nID in V:
                    continue
                else:
                    V.append(nID)
                # end if
                
                # get nID's children
                children = utils_process.get_children(nID, Ndiag, Fdiag)
                for chID in children:
                    if chID not in V:
                        Q.append(chID)
                    # end if
                # end for
            # end while
        # end for
    # end for
    
    # ready
    return critical_segm
# end func


#%% function - dependencies_all

def dependencies_all(Nall, Fall, Fmsg):
    # find, for each diagram, all critical segments of other diagrams that it depends on
    # Input:
    #    > Nall, Fall: all diagrams of the process
    #    > Fmsg: messagel flows of the process, in the form (nID1, nID2)
    # Output:
    #    > critical_segm_all: list of dicts of the form diag_i -> {diag_x: [(ev1_x, ev2_x)], diag_y:[]}, showing that
    #                     diag_i depends on the critical segment ev1_x -> ... -> ev2_x of diag_x, etc.
    
    
    critical_segm_all = [None for _ in range(len(Nall))]
    
    # for each diagram
    for i in range(len(Nall)):
        # get all critical segments of the other diagrams that diag i depends on
        # use function diag_dependencies to do this
        Ndiag = Nall[i]
        Fdiag = Fall[i]
        critical_segm_i = diag_dependencies(Ndiag, Fdiag, Nall, Fall, Fmsg)
        # store the dependencies
        critical_segm_all[i] = critical_segm_i.copy()
    # end for
    
    # ready
    return critical_segm_all
# end func


#%% function - crit_segment_diag

def crit_segment_diag(diag_x, critical_segm_all, Nall, Fall):
    # find all segments contained in diagram diag_i
    # Input:
    #    > diag_x: diagram number of the process, must be 0 <= diag_x < len(Nall)
    #    > critical_segm_all: list of dicts of the form diag_i -> {diag_x: [(ev1_x, ev2_x)], diag_y:[]}, showing that
    #                     diag_i depends on the critical segment ev1_x -> ... -> ev2_x of diag_x, etc.
    #                     Output of the function 'dependencies_all'
    #    > Nall, Fall: all diagrams of the process
    # Output:
    #    > crit_segm_x: list of type [segm1, segm2,...] listing all critical segments
    #                   contained in diag_x. Here, segm_i = (evID1_x, evID2_x) as usual
    
    crit_segm_x = []
    
    if diag_x < 0 or diag_x >= len(Nall):
        raise ValueError('Diagram number must be between 0 and len(Nall) - 1!')
    # end if
    
    # for all diagrams
    for i in range(len(Nall)):
        if i == diag_x:
            # diag_x can't depend on itself
            continue
        # end if
        
        # get all critical segments that diag_i depends on
        crit_segm_i = critical_segm_all[i]
        # this is a dict of type diag_j:[segm1, segm2...] showing the segments and diagrams
        # that diag_i depends on
        
        for diag_j in crit_segm_i:
            if diag_j == diag_x:
                # if diag_i depends on diag_x, then the segments in there are inside diag_x
                # append them in th list (e.g. if crit_segm_x = [segm1, segm2] and crit_segm_i[diag_j] = [segm3, segm4] 
                # now we have crit_segm_x = [segm1, sgm2, segm3, segm4])
                crit_segm_x += crit_segm_i[diag_j]
            # end if
        # end for
    # end for
    
    # ready
    return crit_segm_x
# end func


#%% function - diag_level_depend    

def diag_level_depend(critical_segm_all, Nall, Fall):
    # record dependencies on the diagram level
    # e.g., if diag_i depends on a critical segment lying inside diagram diag_x
    # then we say that diag_i depends on diag_x
    #    > critical_segm_all: list of dicts of the form diag_i -> {diag_x: [(ev1_x, ev2_x)], diag_y:[]}, showing that
    #                     diag_i depends on the critical segment ev1_x -> ... -> ev2_x of diag_x, etc.
    #                     Output of the function 'dependencies_all'
    #    > Nall, Fall: all diagrams of the process
    # Output:
    #    > dependencies: dict of type diag_i:[diag1, diag2,...], meaning that diag_i 
    #                    depends on diag1, diag2,..., for each diag_i
    
    dependencies = {}
    n_diags = len(Nall)
    # def a dependency matrix depend_mat[i, j] = 1 if diag i depends on diag j, 0 else
    depend_mat = np.zeros( (n_diags, n_diags), int )
    
    for i in range(n_diags):
        # critical_segm_all[i] is a dict of type diag_j:[segm1_j, segm2_j] etc, so i depends
        # on j. So we add j in the dependency list of i
        dep_diags_i = critical_segm_all[i].keys()
        for j in dep_diags_i:
            # for each j that i depends on, make the array entry 1
            if critical_segm_all[i][j] != []:
                depend_mat[i, j] = 1
            # end if
        # end for
    # end for
    
    # now get the final dependencies
    # if diag_i depends on diag_j, and diag_j depends on diag_k, then diag_i also
    # depends on diag_k
    for i in range(n_diags):
        # do BFS starting from diag i
        # if diag_i depends on diag_j, visit diag_j
        # we visit all diagrams this way that diag_i depends on
        
        Q = [i]
        V = []
        
        while Q != []:
            curr_diag = Q.pop(0)
            V.append(curr_diag)
            
            # get the unvisited children of curr_diag
            # these are the diagrams that curr_diag depends on
            # curr_diag depends on all diagrams j where depend_mat[curr_diag, j] = 1
            children_curr = list( np.where( depend_mat[curr_diag, :] == 1 )[0] )
            for ch_diag in children_curr:
                if ch_diag not in V:
                    Q.append(ch_diag)
                # end if
            # end for
        # end while
        
        # the diagrams that diag i depends on are all diagrams lying in V,
        # except i itself, which we remove
        V.remove(i)
        V.sort()
        
        dependencies[i] = V.copy()
    # end for
    
    
    # return
    return dependencies
# end func


#%% function - diags_depend_on

def diag_descendants(diag_i, dependencies, Nall, Fall):
    # given diagram, find all diagrams that depend on it (directly or not)
    # Input:
    #    > diag_i: the diag number
    #    > dependencies: dict of type diag_i:[diag1, diag2,...], meaning that diag_i 
    #                    depends on diag1, diag2,..., for each diag_i
    #    > Nall, Fall: all diagrams of the process
    # Output:
    #    > depend_diags: a list of the diagrams that depend diag_i
    
    depend_diags_i = []
    
    # sanity check
    if diag_i < 0 or diag_i >= len(Nall):
        raise ValueError('diag_i must be >= 0 and < len(Nall)!')
    # end if
    
    # for each diagram
    for diag_y in range(len(Nall)):
        # check if diag_y depends on diag_i
        depend_y = dependencies[diag_y] # list of diagrams that diag_y depends on
        if diag_i in depend_y:
            # append diag_y in the list (as it depends on diag_i)
            if diag_y not in depend_diags_i:
                depend_diags_i.append(diag_y)
            # end if
        # end if
    # end for
    
    # remove duplicates
    
    # ready
    return depend_diags_i
# end func


#%% function - diags_decendants

def diags_decendants(diags_list, dependencies, Nall, Fall):
    # given a list of diagrams, find all diagrams that depend on them directly or indirectly
    # Input:
    #    > diags_list: list of diagram numbers
    #    > dependencies: dict of type diag_i:[diag1, diag2,...], meaning that diag_i 
    #                    depends on diag1, diag2,..., for each diag_i
    #    > Nall, Fall: all diagrams of the process
    # Output:
    #    > depend_diags: a list of the diagrams that depend on diags_list
    
    depend_diags = set([])
    
    # for each diagram, append all it's dependent diagrams in the set
    for diag_i in diags_list:
        depend_i = diag_descendants(diag_i, dependencies, Nall, Fall) # list of diagrams that depend on diag_i
        # append them (we use set to avoid double counting)
        depend_diags = depend_diags.union(set(depend_i))
    # end for
    
    # ready
    return list(depend_diags)
# end func
        

#%% function - crit_segment_depend

def crit_segment_depend(critical_segm, dependencies, Nall, Fall):
    # given each critical segment semg = (evID1, evID2, diag_i) of diagram i
    # find all diagrams that depend on it, either directly or inderecltly
    # that means, if diag_i jumps "behind" the critical segment, then
    # all dependent diagrams need to restart
    # Input:
    #    > critical_segm: list dicts of critical segments of each diagram, in the form 
    #                     critical_segm[diag_i] = {diag_x:[(evID1_x, evID2_x), (evID3_x, evID4_x)], diag_y:[...]}
    #                     output of function dependencies_all
    #    > Nall, Fall: all diagrams of the process
    #    > dependencies: dict of type diag_i:[diag1, diag2,...], meaning that diag_i 
    #                    depends on diag1, diag2,..., for each diag_i
    # Output:
    #    > crit_segm_dep_all: dict of type {segm1: [diag_i, diag_j], segm2: []}
    #                     eg. for each critical segment segm1 = (evID1_x, evID2_x)
    #                     list all diagrams that depend on it, either directly or not
    
    crit_segm_dep_all = {}
    
    # for each diagram                     
    for diag_i in range(len(Nall)):
        # for each segment that diag_i depends on
        for diag_x in critical_segm[diag_i]:
            segments_x = critical_segm[diag_i][diag_x]
            for segm_x in segments_x:
                # append it
                crit_segm_dep_all[segm_x] = []
            # end for
        # end for
    # end for
    
    # step 2: for each segment, find all diags that depend on it directly
    for segm in crit_segm_dep_all:
        for diag_i in range(len(critical_segm)):
            for diag_x in critical_segm[diag_i]:
                segments_x = critical_segm[diag_i][diag_x]
                for segm_x in segments_x:
                    if segm_x == segm:
                        crit_segm_dep_all[segm].append(diag_i)
                    # end if
                # end for
            # end for
        # end for
    # end for
    
    # step 3: now for each segm find also the diagrams that depend indirectly
    for segm in crit_segm_dep_all:
        depend_segm = crit_segm_dep_all[segm] # list of diags that directly depend on segm
        # get all dependencies (also indirect)
        depend_indirect = diags_decendants(depend_segm, dependencies, Nall, Fall)
        # update
        crit_segm_dep_all[segm] = depend_segm + depend_indirect
    # end for
    
    # ready
    return crit_segm_dep_all
# end func


#%% function - process_to_modules

def process_to_modules(Nall, Fall):
    # convert a process to prism modules
    # Input:
    #    > Nall, Fall: nodes and flows of the process
    # Output:
    #    > Modules_all: Modules_all[diag_i] list of dicts of type nodeID: (name, type). One dict 
    #                   for each module, that contains the module's nodes
    #    > Mod_nodes_all: Mod_nodes_all[diag_i] is a dict of type nodeID: module_no, containing 
    #                     the module where each node of Ndiag is assigned to
    
    # init
    Modules_all = []
    Mod_nodes_all = []
    
    for diag_i in range(len(Nall)):
        Modules_i, Mod_nodes_i = diag_to_modules2(Nall[diag_i], Fall[diag_i])
        Modules_all.append(Modules_i)
        Mod_nodes_all.append(Mod_nodes_i)
    # end for
    
    # ready
    return Modules_all, Mod_nodes_all
# end func


#%% function - ids_to_prism_states

def ids_to_prism_states(Nall, Fall, Modules_all, Mod_nodes_all):
    # for each nodeID find the corresponding prism module and prism state
    # map also the opposite (e.g. for each diag, module no. and prism state get the nodeID)
    # Input:
    #    > Nall, Fall: nodes and flows of the process
    #    > Modules_all: Modules_all[diag_i] list of dicts of type nodeID: (name, type). One dict 
    #                   for each module, that contains the module's nodes. Returned by 'process_to_modules'
    #    > Mod_nodes_all: Mod_nodes_all[diag_i] is a dict of type nodeID: module_no, containing 
    #                     the module where each node of Ndiag is assigned to. Returned by 'process_to_modules'
    # Output:
    #    > ids2prism: list, where ids2prism[diag_i] is a dict of type nodeID: (module no, prism state)
    #    > prism2ids: list, where prism2ids[diag_i] is a dict of type (prism state, module no): nodeID  
    
    ids2prism = [{} for _ in range(len(Nall))]
    prism2ids = [{} for _ in range(len(Nall))]
    
    # for all diagrams
    for diag_i in range(len(Modules_all)):
        # for every module of the diagram'
        for mod_i in range(len(Modules_all[diag_i])):
            # for each node in the module
            node_cnt = 0 # node counter, equal to the prism state
            for nID in Modules_all[diag_i][mod_i]:
                node_cnt += 1
                # store nID in dict, with it's prism state (node_cnt) and mod_i
                ids2prism[diag_i][nID] = {'prism_state': node_cnt, 'prism_mod': mod_i}
                # also store the reverse
                prism2ids[diag_i][(node_cnt, mod_i)] = nID
            # end for
        # end for
    # end for
    
    # ready, return
    return ids2prism, prism2ids
# end func


#%% function - flows_to_prism_vars

def flows_to_prism_vars(Fmsg):
    # assign a prism variable fl_i to each msg flow in a process
    # fl_i will be '1' if the flow_i (evID1 --> evID2) is activated,
    # e.g. diag_1 has reached evID1 (and thus diag_2 can proceed), and
    # it will be zero otherwise
    # Input:
    #    > Fmsg: the msg flows of the process
    # Output:
    #    > flow_vars: dict that assigns, to each flow (evID1, evID2): fl_i
    #                 a prism variable fl_i
    #    > flow_vars_inv: the inverse dict of the above, e.g. fl_i: (evID1, evID2)
    
    flow_vars = {}
    flow_vars_inv = {}
    flows_cnt = 0
    
    for fl in Fmsg:
        flows_cnt += 1
        flow_vars[fl] = flows_cnt
        flow_vars_inv[flows_cnt] = fl
    # end for

    # ready
    return flow_vars, flow_vars_inv
# end func


#%% function - start_end_states

def start_end_states(Modules_all):
    # for each prism module, find it's start and end state
    # Input:
    #    > Modules_all: Modules_all[diag_i] list of dicts of type nodeID: (name, type). One dict 
    #                   for each module, that contains the module's nodes. Returned by 'process_to_modules'
    # Output:
    #    > starts_ends: list of dicts [{...}, {...}, ], one dict for each diag. starts_ends[diag_i][mod_i]: 
    #                   {'start_state': (s1, nID1), 'end_state': (s2, nID2), 'n_states': n_states}
    #                   start_state is the starting prism state, _end_state the end prism state
    #                   and n_states the number of states of that module. Here, s1,s2 are prism states,
    #                   and we also store the node ID (nID)
    
    starts_ends = [{} for _ in range(len(Modules_all))]
    
    # for all diagrams
    for diag_i in range(len(Modules_all)):
        # for each module in diag_i
        for mod_i in range(len(Modules_all[diag_i])):
            if len(Modules_all[diag_i]) == 1:
                # the whole diagram is only one module, then the start is the diag 
                # start, and similar for the end
                s_start = 1 # the module starts at the start state, which has prism state 1
                nID_start = list( Modules_all[diag_i][mod_i] )[0] # the 1st node is the start
                s_end = len(Modules_all[diag_i][mod_i]) # end is the last state
                nID_end = list( Modules_all[diag_i][mod_i] )[-1] # end node lies in the last node of module 
                n_states = len(Modules_all[diag_i][mod_i]) # number of states
                # store info
                starts_ends[diag_i][mod_i] = {'start_state': (s_start, nID_start), 
                                              'end_state': (s_end, nID_end), 'n_states': n_states}
                break # only one module, no need to proceed
            # end if
            # the first module of each diag contains the start of the diagram, and
            # needs to start there (corresponding to prism state s = 1)
            if mod_i == 0:
                # 1st module contains the start at the 1st node
                s_start = 1 # the module starts at the start state, which has prism state 1
                nID_start = list( Modules_all[diag_i][mod_i] )[0] # the 1st node is the start
                s_end = 0 # all intermediate modules must end at the idle state 0
                nID_end = None # the idel state corresponds to no node
                n_states = len(Modules_all[diag_i][mod_i]) # number of states
                # store info
                starts_ends[diag_i][mod_i] = {'start_state': (s_start, nID_start), 
                                              'end_state': (s_end, nID_end), 'n_states': n_states}
            elif mod_i == len(Modules_all[diag_i]) - 1:
                # the last module of diag_i contains the end state as it's final node
                s_start = 0 # the module starts at the idle state, which has prism state 0
                nID_start = None # idle has no node ID
                s_end = len(Modules_all[diag_i][mod_i]) # end is the last state
                nID_end = list( Modules_all[diag_i][mod_i] )[-1] # end node lies in the last node of module 
                n_states = len(Modules_all[diag_i][mod_i]) # number of states
                # store info
                starts_ends[diag_i][mod_i] = {'start_state': (s_start, nID_start), 
                                              'end_state': (s_end, nID_end), 'n_states': n_states}
            else:
                # an intermediate module (neither start or end)
                # it must start and finish at the idle state
                s_start = 0 # the module starts at the idle state, which has prism state 0
                nID_start = None # idle has no node ID
                s_end = 0
                nID_end = None # idle has no node ID
                n_states = len(Modules_all[diag_i][mod_i]) # number of states
                # store info
                starts_ends[diag_i][mod_i] = {'start_state': (s_start, nID_start), 
                                              'end_state': (s_end, nID_end), 'n_states': n_states}
            # end if
        # end for
    # end for
    
    # return
    return starts_ends
# end func


#%% modules_diag_end_last

def modules_diag_end_last(Modules_diag):
    # for a diagram's modules, put the end node in the last position
    # this will ensure that end will be the last state
    # Input:
    #    > Modules_diag: the modules of a diagram, as given by 'diag_to_modules'
    # Output:
    #    > Modules_diag_new: module diagrams where the end states are always last
    
    Modules_diag_new = Modules_diag.copy()
    end_mod = None
    endID = None
    
    for mod_i in range(len(Modules_diag_new)):
        # find the module that contains the 'end'
        for nID in Modules_diag_new[mod_i]:
            if Modules_diag_new[mod_i][nID]['type'] == 'end':
                end_mod = mod_i
                endID = nID
                break
            # end if
        # end for
    # end for
    
    if end_mod is None:
        # invalid - one diagram must contain 'end'
        raise ValueError('One module must contain the diagram end state!')
        #return None
    # end if
    
    # pop the end node and put it back - in that way it goes at the end of the dict
    end_info = Modules_diag_new[end_mod].pop(endID)
    Modules_diag_new[end_mod][endID] = end_info
    
    # ready
    return Modules_diag_new
# end func
    

#%% function - process_to_modules2

def process_to_modules2(Nall, Fall):
    # convert a process to prism modules
    # Input:
    #    > Nall, Fall: nodes and flows of the process
    # Output:
    #    > Modules_all: Modules_all[diag_i] list of dicts of type nodeID: (name, type). One dict 
    #                   for each module, that contains the module's nodes
    #    > Mod_nodes_all: Mod_nodes_all[diag_i] is a dict of type nodeID: module_no, containing 
    #                     the module where each node of Ndiag is assigned to
    
    # init
    Modules_all = []
    Mod_nodes_all = []
    
    for diag_i in range(len(Nall)):
        Modules_i, Mod_nodes_i = diag_to_modules2(Nall[diag_i], Fall[diag_i])
        # reorder modules so that the end state is always last in its module
        Modules_i2 = modules_diag_end_last(Modules_i)
        Modules_all.append(Modules_i2)
        Mod_nodes_all.append(Mod_nodes_i)
    # end for
    
    # ready
    return Modules_all, Mod_nodes_all
# end func 


#%% function - helper_make_trans

def helper_make_trans(label, s, nID, wait_flows, s_next, nID_next, probs, trig_flows, untrig_flows):
# helper function to define a prism transition in the form 
# [thelabel] s0 = s & [wait_flows = 1] -> s0 = probs[0]: s_next[0] & [trig-untrig flows[0]]   
#                                         + s0 = probs[1]: s_next[1] & [trig-untrig flows[1]] etc.
# Input:
#    > label: the transition's label (string or '')
#    > s: the current prism state (int)
#    > nID: the node ID of the current state, or None if we're at an aux state
#    > wait_flows: flow variables that must be true to proceed; for example (f1 = 1) & (f2 = 1)
#    > s_next: list of next prism states
#    > nID_next: list of next node IDs, where some of them can be None in case we move to aux states
#    > trig_flows: list of lists, where trig_flows[i] = [f1, f2, ...] are the flows that are
#                  triggered (become 1) by the transition s -> s_next[i]
#    > untrig_flows: list of lists, where untrig_flows[i] = [f1, f2, ...] are the flows that are
#                  un-triggered (must become 0) by the transition s -> s_next[i] (in case of a backward transition)
# Output:
#    > trans: a dict containing all these information

    trans = {}
    trans['label'] = label
    trans['s'] = s
    trans['nID'] = None
    trans['wait_flows'] = []
    trans['s_next'] = s_next.copy()
    trans['nID_next'] = nID_next.copy()
    trans['probs'] = probs.copy()
    trans['trig_flows'] = trig_flows.copy()
    trans['untrig_flows'] = untrig_flows.copy()
    
    return trans
# end func


#%% function - helper_init_prism_mod

def helper_init_prism_mod(mod_i, Modules_i, starts_ends_i, flow_vars, Fmsg):
    # initialize a prism module with its basic information: start state, end state, etc.
    # Input:
    #    > mod_i: the module to be initialized
    #    > Modules_i: modules for diag_i
    #    > starts_ends_i: start-end states for the modules
    #    > flow_vars: the flow variables of the process
    #    > Fmsg: flows of the process
    # Output:
    #    > info: dict containing the module info
    #    > flows_mod_i: list containing the flow vars that belong to mod_i - i.e.
    #                   flows evID1 --> evID2 where evID1 belongs to diag_i (and thus
    #                   the flow is (un)triggered by it)
    
    # get start, end and number of states
    s_start, nID_start = starts_ends_i[mod_i]['start_state']
    s_end, nID_end = starts_ends_i[mod_i]['end_state']
    n_states = starts_ends_i[mod_i]['n_states']
    
    info = {'start_state': s_start, 'end_state': s_end, 'n_states': n_states, 'n_aux_states': 0}
    
    # get also the flow vars controlled by that module
    flows_mod_i = []
    
    # this happens when a flow fl = evID1 --> evID2 has the evID1 in mod_i
    for fl in Fmsg:
        evID1, evID2 = fl
        if evID1 in Modules_i[mod_i]:
            flows_mod_i.append(flow_vars[fl])
        # end if
    # end for
    
    return info, flows_mod_i
# end func


#%% function - helper_get_wait_flows

def helper_get_wait_flows(nID, flow_vars, Fmsg):
    # for a node nID, find the waiting flows, that is, the nodes that must be
    # true so that the diagram can proceed after nID
    # Input:
    #    > nID: node ID
    #    > flow_vars: the flow variables of the process
    #    > Fmsg: the msg flows of the process
    # Output:
    #    > wait_flows_nID: list of the flow vars that nID must wait for
    
    wait_flows_nID = []
    
    for fl in Fmsg:
        evID1, evID2 = fl
        if evID2 == nID:
            wait_flows_nID.append(flow_vars[fl])
        # end if
    # end for
    
    return wait_flows_nID
# end func


#%% function - helper_get_trig_flows

def helper_get_trig_flows(nID_next, flow_vars, Fmsg):
    # get the flow vars that get triggered (become true) when the diagram 
    # reaches node nID_next
    # Input:
    #    > nID: node ID
    #    > flow_vars: the flow variables of the process
    #    > Fmsg: the msg flows of the process
    # Output:
    #    > trig_flows_nID_next: list of the flow vars that nID must wait for
    
    # find the flows that get triggered when the diagram reaches nID_next
    trig_flows_nID_next = []
    for fl in Fmsg:
        evID1, evID2 = fl
        if evID1 == nID_next:
            trig_flows_nID_next.append(flow_vars[fl])
        # end if
    # end for
    
    return trig_flows_nID_next
# end func


#%% function - helper_make_label

def helper_make_label(label_type, diag_i, diag_labels):
    # create a new label for a prism transition of type [label] s = a -> ...
    # the label spec is 'f'_{diag_i}_{fork_cnt}. 'f' for fork, 'j' for join, 'd' for decision
    # Input:
    #    > diag_i: the diagram we work on
    #    > diag_labels: diagram labels of type diag_labels[label_type] = [label1, label2, ...]
    #                   e.g. a dict that for each label types has a list of the existing labels
    #                   in a diagram
    #    > label_type: the type of label to build: either 'fork', 'join' or 'decision'
    # Output:
    #    > thelabel: the new created label
    
    if label_type == 'fork':
        label_letter = 'f'
    elif label_type == 'join':
        label_letter = 'j'
    elif label_type == 'decision':
        label_letter = 'd'
    else:
        raise ValueError('label type must be either fork, join or decision!')
    # end if
    
    label_cnt = len(diag_labels[label_type])
    
    thelabel = label_letter + str(diag_i) + '_' + str(label_cnt) 
    return thelabel
# end func


#%% function - forward_trans

def forward_trans(nID, chID, Ndiag, Fdiag):
    # check if the transition nID -> chID is forward of backward
    # Input:
    #    > nID, chID: nodes of the transition
    # Ndiag, Fdiag: nodes and flows of the diag
    # Output:
    #     > is_forward: True if transition is forward (chID >= nID), False if backward
    
    if utils_process.order_nodes(nID, chID, Ndiag, Fdiag) == (nID, chID):
        # forward transition
        return True
    else:
        return False
    # end if
# end func

#%% function - helper_violated_segm

def helper_violated_segm(nID, chID, crit_segm_i, Ndiag, Fdiag):
    # find the critical segments of diag_i that get violated by the transition nID -> chID
    # Input:
    #    > nID, chID: the nod IDs of the transition nID -> chID
    #    > crit_segm_i: the critical segments of diagram i
    #    > Ndiag, Fdiag: nodes and flows of diag_i
    # Output:
    #    > violated_segm_ch: list of violated segments
    
    violated_segm_ch = []
    # if transition goes forward, no violations
    if forward_trans(nID, chID, Ndiag, Fdiag) == True:
        return []
    # end if
    
    # for all crit segments within diag_i
    for segm in crit_segm_i:
        evID1, evID2 = segm
        # if nID >= evID1 and chID < evID1 (e.g. chID <= evID1 and chID != evID1)
        cond1 = utils_process.order_nodes(evID1, nID, Ndiag, Fdiag) == (evID1, nID)
        cond2 = utils_process.order_nodes(chID, evID1, Ndiag, Fdiag) == (chID, evID1)
        if cond1 and cond2 and chID != evID1:
            # the segment is violated, append
            violated_segm_ch.append(segm)
        # end if
    # end for
    
    return violated_segm_ch
# end func


#%% function - helper_trig_flows_jump

def helper_trig_flows_jump(nID, chID, flow_vars, Ndiag, Fdiag, Fmsg):
    # in case of a jump (due to a decision gate) nID -> chID, find the
    # flow variables that need to be triggered or untriggered by that jump
    # Input:
    #    > nID, chID: the nod IDs of the transition nID -> chID
    #    > flow_vars: flow variables (for prism)
    #    > Ndiag, Fdiag, Fmsg: nodes and flows of diag_i, and message flows of process    
    # Output:
    #   > trig_flows_chID: list of flow vars that get triggered by the transition (e.g. set to true)
    #   > untrig_flows_chID: list of flow vars that get untriggered (set to 0) due to the jump
    
    trig_flows_chID = []
    untrig_flows_chID = []
    
    # check if transition nID -> chID is forward or backward
    forward_trans = False
    backward_trans = False
    if utils_process.order_nodes(nID, chID, Ndiag, Fdiag) == (nID, chID):
        # forward transition
        forward_trans = True
    else:
        # backward trans
        backward_trans = True
    # end if
    
    # if transition is forward, all flows with a "head" before or at chID
    # must be activated
    if forward_trans == True:
        for fl in Fmsg:
            evID1, evID2 = fl
            # if nID < evID1 <= chID, activate that flow
            cond1 = utils_process.order_nodes(nID, evID1, Ndiag, Fdiag) == (nID, evID1) 
            cond2 = utils_process.order_nodes(evID1, chID, Ndiag, Fdiag) == (evID1, chID)
            if cond1 and cond2 and nID != evID1:
                trig_flows_chID.append(flow_vars[fl])
            # end if
        # end for
    elif backward_trans == True:
        for fl in Fmsg:
            evID1, evID2 = fl
            # if evID1 > chID and evID1 <= nID, deactivate that flow
            cond1 = utils_process.order_nodes(evID1, nID, Ndiag, Fdiag) == (evID1, nID)
            cond2 = utils_process.order_nodes(chID, evID1, Ndiag, Fdiag) == (chID, evID1)
            if cond1 and cond2 and chID != evID1:
                untrig_flows_chID.append(flow_vars[fl])
            # end if
        # end for
    # end if
    
    return trig_flows_chID, untrig_flows_chID
# end func


#%% function - helper_make_task_trans

def helper_make_task_trans(nID, nID_next, diag_i, diag_labels, prism_mod, Mod_nodes_i, 
                           ids2prism_i, flow_vars, Ndiag, Fdiag, Fmsg):
    # helper function top make a prism transition in case nID is not fork or decision
    # Input:
    #    > nID, nID_next: node IDs of current and next node
    #    > diag_i: the current diagram number
    #    > diag_labels: diagram labels of type diag_labels[label_type] = [label1, label2, ...]
    #                   e.g. a dict that for each label types has a list of the existing labels
    #                   in a diagram
    #    > Modules_i: list of dicts of type nodeID: (name, type). One dict for each module, 
    #               that contains the module's nodes
    #    > Mod_nodes_i: dict of type nodeID: module_no, containing the module where each node
    #                 of Ndiag is assigned to 
    #    > flow_vars: dict that assigns, to each flow (evID1, evID2): fl_i
    #                 a prism variable fl_i
    #    > ids2prism_i: dict of type nodeID: (module no, prism state)
    #    > prism_mod: list, one for each module. prism_mod[mod_i]['info'] contains info about
    #                 the module, such as start state, number of states, etc
    #                 prism_mod[mod_i]['transitions'] contains a list of transitions, with various
    #                 attributes. An example: {'curr_state':.., 'next_states':..., 'probs':..., }
    # Output:
    #    > prism_mod: appends the new transitions to the corresp prism modules
    
    # get module of curr node
    mod_curr = Mod_nodes_i[nID]
    # get prism state of curr node
    s_curr = ids2prism_i[nID]['prism_state']
    
    # get the waiting flow vars of nID
    wait_flows_nID = helper_get_wait_flows(nID, flow_vars, Fmsg)
    
    # get module and prism state of child
    mod_next = Mod_nodes_i[nID_next]
    s_next = ids2prism_i[nID_next]['prism_state']
    
    # find the flows that get triggered when the diagram reaches nID_next
    trig_flows_nID_next = helper_get_trig_flows(nID_next, flow_vars, Fmsg)
    
    # case 1: transition stays inside the current module
    if mod_next == mod_curr:
        # create the transition []: s = s_curr & (fl_wait1 = 1) & ... & (fl_wait_k = 1) 
        # -> 1:(s' = s_next) & (fl_trig1' = 1) & ... & (fl_trig_k' = 1)
        trans = {}
        trans['label'] = '' # no label here
        trans['s'] = s_curr
        trans['nID'] = nID # keep also nIDs for debugging
        trans['wait_flows'] = wait_flows_nID.copy()
        trans['s_next'] = [s_next] # only one next state here
        trans['nID_next'] = [nID_next]
        trans['probs'] = [1.0] # transition with prob = 1.0 here
        trans['trig_flows'] = [trig_flows_nID_next.copy()]
        # append transition
        prism_mod[mod_curr]['transitions'].append(trans)
    else:
        # transition goes out of module (goes to join)
        # we need 2 transitions: one to set curr module to zero
        # and another to start the next module
        # label will be 'j' (from join) + diag_i + '_' + join_cnt
        
        # trans 1: [j{diag_i}_{join_cnt}] s = s_curr & (fl_wait1 = 1) & ... & (fl_wait_k = 1)  
        # -> 1:(s' = 0)
        trans = {}
        has_label = False
        if nID_next in diag_labels['join']:
            has_label = True
            # the label for nID_next already exists, we use it
            the_label = diag_labels['join'][nID_next]
        else:
            # otherwise, we create a new join jabel
            the_label =  helper_make_label('join', diag_i, diag_labels)
            diag_labels['join'][nID_next] = the_label # append new label
        # end if
        trans['label'] = the_label
        trans['s'] = s_curr
        trans['nID'] = nID
        trans['wait_flows'] = wait_flows_nID.copy()
        trans['s_next'] = [0] # go to idle state
        trans['nID_next'] = [None]
        trans['probs'] = [1.0] # transition with prob = 1.0 here
        trans['trig_flows'] = [[]] # no flow is triggred when restarting
        # append transition
        prism_mod[mod_curr]['transitions'].append(trans)
        
        # trans 2 (at next module): [j{diag_i}_{join_cnt}] s = 0
        # -> 1:(s' = s_next) & (fl_trig1' = 1) & ... & (fl_trig_k' = 1) 
        # this is not needed if has_label is True, because if label already
        # exists, then the next module has already been triggered by another 
        # module going to the join
        if has_label == False:
            trans = {}
            trans['label'] = the_label
            trans['s'] = 0
            trans['nID'] = None
            trans['wait_flows'] = []
            trans['s_next'] = [s_next] # only one next state here
            trans['nID_next'] = [nID_next]
            trans['probs'] = [1.0] # transition with prob = 1.0 here
            trans['trig_flows'] = [trig_flows_nID_next]
            # append transition
            prism_mod[mod_next]['transitions'].append(trans)
        # end if
    # end if
    
    # ready, return
    return
# end func


#%% function - helper_make_fork_trans

def helper_make_fork_trans(nID, diag_i, diag_labels, prism_mod, Mod_nodes_i, 
                           ids2prism_i, flow_vars, Ndiag, Fdiag, Fmsg):
    # helper function top make a prism transition in case nID is a fork
    # Input:
    #    > nID, nID_next: node IDs of current and next node
    #    > diag_i: the current diagram number
    #    > diag_labels: diagram labels of type diag_labels[label_type] = [label1, label2, ...]
    #                   e.g. a dict that for each label types has a list of the existing labels
    #                   in a diagram
    #    > Modules_i: list of dicts of type nodeID: (name, type). One dict for each module, 
    #               that contains the module's nodes
    #    > Mod_nodes_i: dict of type nodeID: module_no, containing the module where each node
    #                 of Ndiag is assigned to 
    #    > flow_vars: dict that assigns, to each flow (evID1, evID2): fl_i
    #                 a prism variable fl_i
    #    > ids2prism_i: dict of type nodeID: (module no, prism state)
    #    > prism_mod: list, one for each module. prism_mod[mod_i]['info'] contains info about
    #                 the module, such as start state, number of states, etc
    #                 prism_mod[mod_i]['transitions'] contains a list of transitions, with various
    #                 attributes. An example: {'curr_state':.., 'next_states':..., 'probs':..., }
    # Output:
    #    > prism_mod: appends the new transitions to the corresp prism modules
    
    # it's a fork!
    
    # get module of curr node
    mod_curr = Mod_nodes_i[nID]
    # get prism state of curr node
    s_curr = ids2prism_i[nID]['prism_state']
    
    # get the waiting flow vars of nID
    wait_flows_nID = helper_get_wait_flows(nID, flow_vars, Fmsg)
    
    # get curr node's children
    next_nodes = utils_process.get_children(nID, Ndiag, Fdiag)
    
    # transition 1: close curr module
    # [f_{diag_i}_{fork_cnt}] s = s_curr + [wait_flows] -> 1: (s' = 0)
    trans = {}
    the_label =  helper_make_label('fork', diag_i, diag_labels)
    diag_labels['fork'].append(the_label)
    trans['label'] = the_label
    trans['s'] = s_curr
    trans['nID'] = nID
    trans['wait_flows'] = wait_flows_nID.copy()
    trans['s_next'] = [0] # go to idle state
    trans['nID_next'] = [None]
    trans['probs'] = [1.0] # transition with prob = 1.0 here
    trans['trig_flows'] = [[]] # no flow is triggred when restarting
    # append transition
    prism_mod[mod_curr]['transitions'].append(trans)  
    
    # now, for each child chID of the fork add transition
    # [f_{diag_i}_{fork_cnt}] s = 0 -> 1: (s' = s_next[chID]) & [trig_flows]
    for chID in next_nodes:
        # get module and prism state of child
        mod_next = Mod_nodes_i[chID]
        # get prism state of next node
        s_next = ids2prism_i[chID]['prism_state']
        # find the flows that get triggered when the diagram reaches nID_next
        trig_flows_chID = helper_get_trig_flows(chID, flow_vars, Fmsg)
        
        # make trans
        trans = {}
        trans['label'] = the_label
        trans['s'] = 0
        trans['nID'] = None
        trans['wait_flows'] = []
        s_next = s_next # start
        trans['s_next'] = [s_next] # only one next state here
        trans['nID_next'] = [chID]
        trans['probs'] = [1.0] # transition with prob = 1.0 here
        trans['trig_flows'] = [trig_flows_chID]
        # append transition
        prism_mod[mod_next]['transitions'].append(trans)
    # end for
    
    # ready, return
    return
# end func


#%% function - helper_make_dec_trans

def helper_make_dec_trans(nID, diag_i, diag_labels, prism_mod, restart_labels, Mod_nodes_i, 
                           ids2prism_i, flow_vars, crit_segm_i, Ndiag, Fdiag, Fmsg):
    # helper function top make a prism transition in case nID is a decision gate
    # Input:
    #    > nID, nID_next: node IDs of current and next node
    #    > diag_i: the current diagram number
    #    > diag_labels: diagram labels of type diag_labels[label_type] = [label1, label2, ...]
    #                   e.g. a dict that for each label types has a list of the existing labels
    #                   in a diagram
    #    > Modules_i: list of dicts of type nodeID: (name, type). One dict for each module, 
    #               that contains the module's nodes
    #    > Mod_nodes_i: dict of type nodeID: module_no, containing the module where each node
    #                 of Ndiag is assigned to 
    #    > flow_vars: dict that assigns, to each flow (evID1, evID2): fl_i
    #                 a prism variable fl_i
    #    > ids2prism_i: dict of type nodeID: (module no, prism state)
    #    > prism_mod: list, one for each module. prism_mod[mod_i]['info'] contains info about
    #                 the module, such as start state, number of states, etc
    #                 prism_mod[mod_i]['transitions'] contains a list of transitions, with various
    #                 attributes. An example: {'curr_state':.., 'next_states':..., 'probs':..., }
    #    > crit_segm_i: list of type [segm1, segm2,...] listing all critical segments
    #                   contained in diag_i. Here, segm_i = (evID1_x, evID2_x) as usual
    # Output:
    #    > prism_mod: appends the new transitions to the corresp prism modules
    #    > restart_labels: dict of the form segm: label_x, indicating the segment violated
    #                      by label_x
       
    # get module of curr node
    mod_curr = Mod_nodes_i[nID]
    # get prism state of curr node
    s_curr = ids2prism_i[nID]['prism_state']
    
    # get the waiting flow vars of nID
    wait_flows_nID = helper_get_wait_flows(nID, flow_vars, Fmsg)
    
    # decision gate, ugh!
    # get curr node's children
    next_nodes = utils_process.get_children(nID, Ndiag, Fdiag)
    
    # make a transition to aux states, one for each child
    trans = {}
    trans['label'] = ''
    trans['s'] = s_curr
    trans['nID'] = nID
    trans['wait_flows'] = wait_flows_nID.copy()
    # next transitions are from state s[n_states + n_aux + 0] 
    # up to s[n_states + n_aux + len(next_nodes)-1] 
    n_states = prism_mod[mod_curr]['info']['n_states']
    n_aux = prism_mod[mod_curr]['info']['n_aux_states']
    trans['s_next'] = np.arange(n_states + n_aux + 1, n_states + n_aux + len(next_nodes) + 1)   
    trans['nID_next'] = [None for _ in range(len(next_nodes))]
    prism_mod[mod_curr]['info']['n_aux_states'] += len(next_nodes)
    # get the probs for the transitions
    probs = []
    for chID in next_nodes:
        p = utils_process.get_prob_flow(nID, chID, Ndiag, Fdiag)
        probs.append(p)
    # end for
    trans['probs'] = probs # transition with prob = 1.0 here
    trans['trig_flows'] = [[] for _ in range(len(probs))]
    # append transition
    prism_mod[mod_curr]['transitions'].append(trans)
    
    # go through children
    # if child in same module, just add transition with prob
    # if child out of module, then:
    # add extra auxiliary state, go there with prob p
    # from aux state, go to zero with label [d + ID of decision gate]
    # to the new module put start tranision with the same label
    
    # additionally: for each transition of the decision gate, look if it
    # violates a critical segment of some diagrams. If yes, these diagrams
    # need to restart. To do this, we make the 'violating transition'
    # labeled to an auxiliary state, and use that label later at the other
    # diags to restart them
    # for example, suppose that the trans decision -> child1 jumps behind
    # the critical segment of diag_2. Then, make the transition decision -> child1
    # labeled with thelabel = [d_{diag_i}_{dec_count}], and afterwards use thelabel
    # to restart diag_2
    
    # also, if a transition jumps backwards it may deactivate some msg flows
    aux_cnt = n_states + n_aux # counter correspondin each aux state to each chID
    for chID in next_nodes:
        aux_cnt += 1
         # get module and prism state of child
        mod_next = Mod_nodes_i[chID]
        # get prism state of next node
        s_next = ids2prism_i[chID]['prism_state']
        
        # get triggered and untriggered flows
        trig_flows_chID, untrig_flows_chID = helper_trig_flows_jump(nID, chID, flow_vars, Ndiag, Fdiag, Fmsg)
        
        # second, if transition goes backwards, check whether it violates some 
        # critical segment evID1 -> evID2. This happens if nID >= enID1 but chID < evID1
        violated_segm_ch = helper_violated_segm(nID, chID, crit_segm_i, Ndiag, Fdiag)
        
        # check if transition is forward or backward
        forw_trans = forward_trans(nID, chID, Ndiag, Fdiag)
        
        if mod_next == mod_curr and len(violated_segm_ch) == 0:
            # in this case, child stays in the same moodle, and doesn't trigger a segment
            # we don't need a label in this case
            # add transition from the corresponding aux state to chID
            # make trans
            trans = {}
            trans['label'] = '' # no label needed here
            trans['s'] = aux_cnt
            trans['nID'] = None
            trans['wait_flows'] = []
            trans['s_next'] = [s_next] # only one next state here
            trans['nID_next'] = [chID]
            trans['probs'] = [1.0] # transition with prob = 1.0 here
            if forw_trans:
                trans['trig_flows'] = [trig_flows_chID] 
            else:
                trans['untrig_flows'] = [untrig_flows_chID] 
            # end if
            prism_mod[mod_curr]['transitions'].append(trans)
        elif mod_next == mod_curr and len(violated_segm_ch) > 0:
            # in this case, the child stays in the moodle, but violates
            # some critical segments. This case is very similar to the 
            # previous one, but we need a lable in order to be able to
            # restart diagrams that depend on the segments
            trans = {}
            the_label = helper_make_label('decision', diag_i, diag_labels)
            trans['label'] = the_label
            diag_labels['decision'].append(the_label)
            # store also this label together with the crit segments in the 
            # restarting info
            for segm in violated_segm_ch:
                # all diagrams depending on segm need to get a restart label
                # equal to the_label
                restart_labels[segm] = the_label
            # end for
            trans['s'] = aux_cnt
            trans['nID'] = None
            trans['wait_flows'] = []
            trans['s_next'] = [s_next] # only one next state here
            trans['nID_next'] = [chID]
            trans['probs'] = [1.0] # transition with prob = 1.0 here
            if forw_trans:
                trans['trig_flows'] = [trig_flows_chID] 
            else:
                trans['untrig_flows'] = [untrig_flows_chID] 
            # end if
            prism_mod[mod_curr]['transitions'].append(trans)
        elif mod_next != mod_curr:
            # the decision jumps out of the module; here we need a label anyway
            trans = {}
            # there can also be the case that the child is a join; in that case
            # we will use the join label (if it exists) or create it
            if Ndiag[chID]['type'] == 'join':
                if chID in diag_labels['join']:
                    the_label = diag_labels['join'][chID]
                else:
                    # make a new join label
                    the_label = helper_make_label('join', diag_i, diag_labels)
                    diag_labels['join'][chID] = the_label
                # end if
            else:
                # otherwise it's a normal node, make a decision label
                the_label = helper_make_label('decision', diag_i, diag_labels)
                diag_labels['decision'].append(the_label)
            # end if
            trans['label'] = the_label
            # store also this label together with the crit segments in the 
            # restarting info
            for segm in violated_segm_ch:
                # all diagrams depending on segm need to get a restart label
                # equal to the_label
                restart_labels[segm] = the_label
            # end for
            trans['s'] = aux_cnt
            trans['nID'] = None
            trans['wait_flows'] = []
            trans['s_next'] = [0] # next state is idle, since we jump out
            trans['nID_next'] = [None]
            trans['probs'] = [1.0] # transition with prob = 1.0 here
            if forw_trans:
                trans['trig_flows'] = [trig_flows_chID] 
            else:
                trans['untrig_flows'] = [untrig_flows_chID] 
            # end if
            prism_mod[mod_curr]['transitions'].append(trans)
            
            # add also the transition to start the new module
            trans = {}
            trans['label'] = the_label
            trans['s'] = 0 # the next module was idle before
            trans['nID'] = None
            trans['wait_flows'] = []
            trans['s_next'] = [s_next]
            trans['nID_next'] = [chID]
            trans['probs'] = [1.0] # transition with prob = 1.0 here
            # we checked the flows before, but no harm to do it again
            if forw_trans:
                trans['trig_flows'] = [trig_flows_chID] 
            else:
                trans['untrig_flows'] = [untrig_flows_chID]
            # end if
            prism_mod[mod_next]['transitions'].append(trans)
        # end if
    # end for
    
    # ready, return
    return
# end func


#%% function - diag_modulesToPrism2

def diag_modulesToPrism2(diag_i, Nall, Fall, Fmsg, Modules_i, Mod_nodes_i, starts_ends_i, 
                        flow_vars, flow_vars_inv, ids2prism_i, prism2ids_i, crit_segm_i):
    # given a diagram and it's discovered modules, we convert these modules in prism
    # Input:
    #    > diag_i: diagram number
    #    > Nall, Fall: nodes and flows of the process
    #    > Modules_i: list of dicts of type nodeID: (name, type). One dict for each module, 
    #               that contains the module's nodes
    #    > Mod_nodes_i: dict of type nodeID: module_no, containing the module where each node
    #                 of Ndiag is assigned to 
    #    > starts_ends: dict. starts_ends[mod_i]: 
    #                   {'start_state': (s1, nID1), 'end_state': (s2, nID2), 'n_states': n_states}
    #                   start_state is the starting prism state, _end_state the end prism state
    #                   and n_states the number of states of that module. Here, s1,s2 are prism states,
    #                   and we also store the node ID (nID). Computed by 'start_end_states' 
    #    > flow_vars: dict that assigns, to each flow (evID1, evID2): fl_i
    #                 a prism variable fl_i
    #    > flow_vars_inv: the inverse dict of the above, e.g. fl_i: (evID1, evID2)
    #    > ids2prism_i: dict of type nodeID: (module no, prism state)
    #    > prism2ids_i: dict of type (prism state, module no): nodeID  
    #    > crit_segm_i: list of type [segm1, segm2,...] listing all critical segments
    #                   contained in diag_i. Here, segm_i = (evID1_x, evID2_x) as usual
    # Output:
    #    > prism_mod: list, one for each module. prism_mod[mod_i]['info'] contains info about
    #                 the module, such as start state, number of states, etc
    #                 prism_mod[mod_i]['transitions'] contains a list of transitions, with various
    #                 attributes. An example: {'curr_state':.., 'next_states':..., 'probs':..., }
    #    > restart_labels: dict of the form segm: label_x, indicating the segment violated
    #                      by label_x
    
    if diag_i < 0 or diag_i >= len(Nall):
        raise ValueError('diagram number must be >= 0 and < len(Nall)!')
    # end if
    
    Ndiag = Nall[diag_i]
    Fdiag = Fall[diag_i]
    
    # inits
    restart_labels = {}
    prism_mod = [ {} for _ in range(len(Modules_i)) ]
    
    for mod_i in range(len(Modules_i)):
        # init module
        info, flows_mod_i = helper_init_prism_mod(mod_i, Modules_i, starts_ends_i, flow_vars, Fmsg)

        prism_mod[mod_i]['info'] = info
        prism_mod[mod_i]['transitions'] = [] # a list that will hold the module's transitions
        prism_mod[mod_i]['flow_vars'] = flows_mod_i # holds the flow variables that only mod_i can trigger
        prism_mod[mod_i]['restart_labels'] = [] # labels for restarting the module
    # end for
    
    # init labels for the diagram
    diag_labels = {'fork': [], 'join': {}, 'decision': []}
    # label specification: ['f'{diag_i}_{fork_cnt}]
    # the join labels depend on the nodeID of the join, so we store a dict nodeID:label_no
    # for a new node, if it goes to a join with existing label we use htis, else we make a 
    # new label
    
    # go through all nodes and connect them
    for nID in Ndiag:
        
        # get the node's type (start, end, task etc.)
        nID_type = Ndiag[nID]['type']    
        
        # if node is 'start', 'join', 'task' or 'event'
        if nID_type in ['start', 'join', 'task', 'event']:
            # get it's children - in this case it's only one
            nID_next = utils_process.get_children(nID, Ndiag, Fdiag)[0]
            
            # call helper function to make the transitions for a task node
            helper_make_task_trans(nID, nID_next, diag_i, diag_labels, prism_mod, Mod_nodes_i, 
                           ids2prism_i, flow_vars, Ndiag, Fdiag, Fmsg)
        elif nID_type == 'end':
            # nothing is needed here (end has no further transitions), continue
            continue
        elif nID_type == 'fork':
            # call helper to handle the fork's transitions
            helper_make_fork_trans(nID, diag_i, diag_labels, prism_mod, Mod_nodes_i, 
                           ids2prism_i, flow_vars, Ndiag, Fdiag, Fmsg)
        elif nID_type == 'decision':
            # call helper to handle the decision gate
            helper_make_dec_trans(nID, diag_i, diag_labels, prism_mod, restart_labels, Mod_nodes_i, 
                           ids2prism_i, flow_vars, crit_segm_i, Ndiag, Fdiag, Fmsg)
        # end if
    # end for
    
    # ready, return
    return prism_mod, restart_labels
# end func


#%% function - add_restart_trans

def add_restart_trans(restart_label, prism_mod):
    # on a prism module list for a diagram, append a restarting label in each module
    # if triggered, each module must return to it's starting state
    # Input:
    #    > restart_label: the label name for restarting (string)
    #    > prism_mod: list, one for each module. prism_mod[mod_i]['info'] contains info about
    #                 the module, such as start state, number of states, etc
    #                 prism_mod[mod_i]['transitions'] contains a list of transitions, with various
    #                 attributes. An example: {'curr_state':.., 'next_states':..., 'probs':..., } 
    # Output:
    #    > prism_mod: the prism_mod, with the restart labels added

    # for each module
    for mod_i in range(len(prism_mod)):
        # append the restart label in module
        prism_mod[mod_i]['restart_labels'].append(restart_label)
    # end for
    
    # return
    return
# end func
        
        

#%% function - processToPrism

def processToPrism(Nall, Fall, Fmsg, Modules, Mod_nodes, starts_ends, flow_vars, 
                   flow_vars_inv, ids2prism, prism2ids, critical_segm_all, crit_segm_dep_all):
    # given a process, we convert it in prism
    # Input:
    #    > Nall, Fall: nodes and flows of the process
    #    > Modules: list: Modules[diag_i] = list of dicts of type nodeID: (name, type). One dict 
    #               for each module, that contains the module's nodes
    #    > Mod_nodes: list: Modules[diag_i] = dict of type nodeID: module_no, containing the module where each node
    #                 of Ndiag is assigned to 
    #    > starts_ends: dict. starts_ends[mod_i]: 
    #                   {'start_state': (s1, nID1), 'end_state': (s2, nID2), 'n_states': n_states}
    #                   start_state is the starting prism state, _end_state the end prism state
    #                   and n_states the number of states of that module. Here, s1,s2 are prism states,
    #                   and we also store the node ID (nID). Computed by 'start_end_states' 
    #    > flow_vars: dict that assigns, to each flow (evID1, evID2): fl_i
    #                 a prism variable fl_i
    #    > flow_vars_inv: the inverse dict of the above, e.g. fl_i: (evID1, evID2)
    #    > ids2prism: = list: ids2prism[diag_i] = dict of type nodeID: (module no, prism state)
    #    > prism2ids_i: list: prism2ids_i[diag_i] = dict of type (prism state, module no): nodeID  
    #    > crit_segm: list: crit_segm[diag_i] = list of type [segm1, segm2,...] listing all critical segments
    #                   contained in diag_i. Here, segm_i = (evID1_x, evID2_x) as usual
    #    > crit_segm_dep_all: dict of type {segm1: [diag_i, diag_j], segm2: []}
    #                     eg. for each critical segment segm1 = (evID1_x, evID2_x)
    #                     list all diagrams that depend on it, either directly or not
    # Output:
    #    > prism_mod_proc: prism_mod_proc[diag_i] = list, one for each module. prism_mod[mod_i]['info'] contains 
    #                 info about the module, such as start state, number of states, etc
    #                 prism_mod[mod_i]['transitions'] contains a list of transitions, with various
    #                 attributes. An example: {'curr_state':.., 'next_states':..., 'probs':..., }
    #    > restart_labels: List: restart_labels[diag_i] = dict of the form segm: label_x, indicating 
    #                      the segment violated by label_x
    
    prism_mod_proc = []
    restart_labels = []
    
    # for each diagram
    for diag_i in range(len(Nall)):
        # create the prism modules of that diagram and the restart labels
        # for the diag's critical segments
        crit_segm_i = crit_segment_diag(diag_i, critical_segm_all, Nall, Fall)
        prism_mod_i, restart_labels_i = diag_modulesToPrism2(diag_i, Nall, Fall, 
                        Fmsg, Modules[diag_i], Mod_nodes[diag_i], starts_ends[diag_i], 
                        flow_vars, flow_vars_inv, ids2prism[diag_i], prism2ids[diag_i], 
                        crit_segm_i)
        # store them
        prism_mod_proc.append(prism_mod_i.copy())
        restart_labels.append(restart_labels_i)
    # end for
    
    # additionally, for each critical segment triggered by a label, add this label
    # as a restarter to all diagrams that depend on it (directly or not)
    for diag_i in range(len(Nall)):
        # for all segments contained in each diagram
        for segm in restart_labels[diag_i]:
            # get the segment's restarting label
            restart_label = restart_labels[diag_i][segm]
            # find all diagrams that depend on segm
            dependent_diags = crit_segm_dep_all[segm]
            # attach the restarting label in each one of those diags
            for diag_j in dependent_diags:
                add_restart_trans(restart_label, prism_mod_proc[diag_j])
            # end for
        # end for
    # end for
    
    # ready
    return prism_mod_proc
# end func


#%% function - print_end_state

def print_end_state(prism_mod_proc):
    # print the end state of a process in the DAT file
    # the end state is the goal where all diagrams - modules have finished
    # Input:
    #    > prism_mod_proc: prism_mod_proc[diag_i] = list, one for each module. prism_mod[mod_i]['info'] contains 
    #                 info about the module, such as start state, number of states, etc
    #                 prism_mod[mod_i]['transitions'] contains a list of transitions, with various
    #                 attributes. An example: {'curr_state':.., 'next_states':..., 'probs':..., }
    # Output:
    #   > end_state_str: string of the end state (for prism)
    
    end_state_str = 'label "end_state" = '
    
    # for all diagrams
    for diag_i in range(len(prism_mod_proc)):
        # for all modules
        for mod_i in range(len(prism_mod_proc[diag_i])):
            # get end state of that module
            end_state = prism_mod_proc[diag_i][mod_i]['info']['end_state']
            # prism state specification: s{diag_i}_{mod_i}
            end_state_str += '(s{}_{} = {}) & '.format(diag_i, mod_i, end_state)
        # end for
    # end for
    
    # now, end_state_str ends like end_state_str = '... & (s5_2 = 5) & '
    # but it must end like '... & (s5_2 = 5);'
    # so we remove the last 3 characters and append ';'
    end_state_str = end_state_str[0:-3] + ';'
    return end_state_str
# end func


#%% function - print_rewards

def print_rewards(rewards_all, ids2prism):
    # prints the rewards of the process in the prism DAT file
    # Input:
    #    > rewards_all: list with length equal to the number of diagrams; 
    #                   rewards_all[i] is a dict of the form [nodeID] -> rew,
    #                   containing all rewards of the diagram i 
    #                   Computed by 'assign_rew_process2'
    #    > ids2prism: = list: ids2prism[diag_i] = dict of type 
    #                         nodeID: (module no, prism state)
    # Output:
    #    > rewards_str: string of the process rewards (for prism)
    
    rewards_str = 'rewards \n'
    
    for diag_i in range(len(rewards_all)):
        rewards_str += '\n// diagram {} \n'.format(diag_i)
        # for all nodes in diag_i
        for nID in rewards_all[diag_i]:
            # get reward
            rew = rewards_all[diag_i][nID]
            # get also prims state corresponding to nID
            s_state = ids2prism[diag_i][nID]['prism_state']
            s_mod = ids2prism[diag_i][nID]['prism_mod']
            # if rew is not zero, append it
            if rew != 0:
                # prism rewards are like: s1_2 = 3: rew;
                rewards_str += 's{}_{} = {}: {:.2f}; \n'.format(diag_i, s_mod, s_state, rew)
            # end if
        # end for
    # end for
    
    rewards_str += 'endrewards \n'
    
    return rewards_str
# end func


#%% function - print_transition

def print_transition(trans, diag_i, mod_i):
    # print out a transition for the prism dat file
    # a transition is specified as follows:
    # [label] s = 1 & (fl1 = 1) & (fl2 = 1) -> 
    # 0.5:(s' = 2) & (fl3' = 1) & (fl4' = 0) + 0.5:(s' = 3);
    # fl are the process flows that are we need to wait for, or that get triggered
    # by the transition
    # Input:
    #    > trans: a dict containing the transition information, such as 's', 's_next',
    #             probabilities, waiting flows, etc.
    #    > diag_i, mod_i: the diagram and module of the transition (int)
    # Output:
    #    > trans_str: the string containing the transition
    
    # get transition info
    the_label = trans['label']
    s = trans['s']
    wait_flows = trans['wait_flows']
    next_states = trans['s_next']
    probs = trans['probs']
    if 'trig_flows' in trans:
        trig_flows = trans['trig_flows']
    else:
        trig_flows = [[] for _ in range(len(next_states))]
    # end if
    if 'untrig_flows' in trans:
        untrig_flows = trans['untrig_flows']
    else:
        untrig_flows = [[] for _ in range(len(next_states))]
    # end if
    
    # start str
    trans_str = '[{}] s{}_{} = {} '.format(the_label, diag_i, mod_i, s)
    for fl_var in wait_flows:
        trans_str += '& (fl{} = 1) '.format(fl_var)
    # end for
    trans_str += ' -> '
    
    for i in range(len(next_states)):
        pi = probs[i]
        si = next_states[i]
        trans_str += '{}: (s{}_{}\' = {}) '.format(pi, diag_i, mod_i, si)
        for fl_var in trig_flows[i]:
            trans_str += '& (fl{}\' = 1) '.format(fl_var)
        # end for
        for fl_var in untrig_flows[i]:
            trans_str += '& (fl{}\' = 0) '.format(fl_var)
        # end for
        trans_str += '+ '
    # end for
    
    # trans_str ends now in '(...) + ' but we want '(...);'
    # so remove 3 last chars and append ';'
    trans_str = trans_str[0:-3] + ';'
    
    return trans_str
# end func


#%% function - print_process

def print_process(prism_mod_proc, rewards_all, ids2prism):
    # print out the entire process into a prism dat file
    # Input:
    #    > prism_mod_proc: prism_mod_proc[diag_i] = list, one for each module. prism_mod[mod_i]['info'] contains 
    #                 info about the module, such as start state, number of states, etc
    #                 prism_mod[mod_i]['transitions'] contains a list of transitions, with various
    #                 attributes. An example: {'curr_state':.., 'next_states':..., 'probs':..., }
    #    > rewards_all: list with length equal to the number of diagrams; 
    #                   rewards_all[i] is a dict of the form [nodeID] -> rew,
    #                   containing all rewards of the diagram i 
    #                   Computed by 'assign_rew_process2'
    #    > ids2prism: = list: ids2prism[diag_i] = dict of type 
    #                         nodeID: (module no, prism state)
    # Output:
    #    > process_str: string of the process rewards (for prism)   
    
    process_str = 'mdp \n\n'
    
    # print end state
    end_state_str = print_end_state(prism_mod_proc)
    
    process_str += end_state_str + '\n\n'
    
    # print also rewards if they excist
    if rewards_all is not None:
        rewards_str = print_rewards(rewards_all, ids2prism)
        process_str += rewards_str + '\n\n'
    # end if
    
    # for all diagrams
    for diag_i in range(len(prism_mod_proc)):
        # for all modules
        process_str += '// diagram {} \n'.format(diag_i)
        for mod_i in range(len(prism_mod_proc[diag_i])):
            module_str = ''
            # get start state of mod_i, etc.
            s_start = prism_mod_proc[diag_i][mod_i]['info']['start_state']
            n_states = prism_mod_proc[diag_i][mod_i]['info']['n_states']
            n_aux_states = prism_mod_proc[diag_i][mod_i]['info']['n_aux_states']
            n_total_states = n_states + n_aux_states
            flow_vars = prism_mod_proc[diag_i][mod_i]['flow_vars']
            restart_labels = prism_mod_proc[diag_i][mod_i]['restart_labels']
            
            # def module header (variable declatations etc)
            module_str += 'module M{}_{} \n'.format(diag_i, mod_i) # e.g. module M1_2
            # e.g s1_2: [0..5] init 1;
            module_str += 's{}_{}: [{}..{}] init {}; \n'.format(diag_i, mod_i, 0, n_total_states, s_start)
            
            # now, we need also to declare the flow vars that belong to the module
            for fl_var in flow_vars:
                module_str += 'fl{}: [{}..{}] init 0; \n'.format(fl_var, 0, 1)
            # end for
            module_str += '\n'
            
            # next, print out all transitions of the module
            for trans in prism_mod_proc[diag_i][mod_i]['transitions']:
                module_str += print_transition(trans, diag_i, mod_i) + '\n'
            # end for
            
            # finally, print also all restarting transitions, based on the restart labels
            # these are transitions in the form [restart_label] s >= 0 -> 1: (s' = s_start)
            for the_label in restart_labels:
                module_str += '[{}] s{}_{} >= 0 -> 1:(s{}_{}\' = {}); \n'.format(the_label, diag_i, mod_i, diag_i, mod_i, s_start)
            # end for
            
            # ready, close module
            module_str += 'endmodule \n\n\n'
            process_str += module_str
        # end for
    # end for
    
    # ready
    return process_str
# end func


#%% function convert_process

def convert_process(Nall, Fall, Fmsg, rewards_all):
    # a function thast converts a process to a prism file, combining the above methods
    # Input:
    #    > Nall, Fall, Fmsg: the process nodes and flows and msg
    #    > list of dics of type nodeID: reward, one for ach diagram
    # Output:
    #    > process_str: a str describing the generated dat file
    
    # assign a prism variable to each flow
    flow_vars, flow_vars_inv = flows_to_prism_vars(Fmsg)
    
    # order diagram nodes in BFS way (for convenience)
    Nall, _ = utils_process.order_process_nodes(Nall, Fall)
    
    # convert process to modules
    Modules_all, Mod_nodes_all = process_to_modules2(Nall, Fall)
    
    # get start and end states for modules
    starts_ends = start_end_states(Modules_all)
    
    # get all prism states and modules of nodes
    ids2prism, prism2ids = ids_to_prism_states(Nall, Fall, Modules_all, Mod_nodes_all)
    
    # find the critical segments
    critical_segm_all = dependencies_all(Nall, Fall, Fmsg)
    
    # get the diagrams that depend on each critical segment
    dependencies = diag_level_depend(critical_segm_all, Nall, Fall)
    
    crit_segm_dep_all = crit_segment_depend(critical_segm_all, dependencies, Nall, Fall)
    
    # ready to run the beast :p
    prism_mod_proc = processToPrism(Nall, Fall, Fmsg, Modules_all, Mod_nodes_all, starts_ends, 
                            flow_vars, flow_vars_inv, ids2prism, prism2ids, critical_segm_all, crit_segm_dep_all)
    
    
    process_str = print_process(prism_mod_proc, rewards_all, ids2prism)
    
    # ready, return
    return process_str
# end func


#%% function - nodes_to_states_map

def nodes_to_states_map(Nall, Fall, Fmsg):
    # maps the diagram nodes to their corresponding prism states
    # and returns a table; e.g. nID1 <-> s0_1, nID2 <-> s0_2 etc.
    # the table contains the following columns: 
    # diagram no. | node ID | node name | node type | prism module | prism state
    # Input:
    #    > Nall, Fall, Fmsg: nodes, flows and message flows of the process
    # Output:
    #    > nodes_states: data frame containing the table data described above
    
    # order diagram nodes in BFS way (for convenience)
    Nall, _ = utils_process.order_process_nodes(Nall, Fall)
    
    # convert process to modules
    Modules_all, Mod_nodes_all = process_to_modules2(Nall, Fall)
    
    # get all prism states and modules of nodes
    ids2prism, prism2ids = ids_to_prism_states(Nall, Fall, Modules_all, Mod_nodes_all)
    
    # holds the data to return
    data = []
    column_names = ['diagram no.', 'node ID', 'node name', 
                    'node type', 'prism module', 'prism state']
    
    # for all diagrams
    for diag_i in range(len(Nall)):
        # for all nodes
        for nID in Nall[diag_i]:
            # get node info
            nID_name = Nall[diag_i][nID]['name']
            nID_type = Nall[diag_i][nID]['type']
            # get corresp. prism state
            nID_state = ids2prism[diag_i][nID]['prism_state']
            nID_module = ids2prism[diag_i][nID]['prism_mod']
            # our prism module specification is M{diag_i}_{mod_i}
            s_module = 'M{}_{}'.format(diag_i, nID_module)
            # store info
            node_info = [diag_i, nID, nID_name, nID_type, s_module, nID_state]
            data.append(node_info)
        # end for
    # end for
    
    # make dataframe
    df = pd.DataFrame(data, columns = column_names)
    return df
# end func

            
            
            
        
    


    








    


    
    



    
    
    
    
    
    
    


    
    
            


                    
                            
            
            
                
            
            
            
        
        
        
        
            
        

            
         







