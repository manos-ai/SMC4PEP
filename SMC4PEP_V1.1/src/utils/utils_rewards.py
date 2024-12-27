# -*- coding: utf-8 -*-
"""
utils to get rewards from a timeline
"""

#%% imports

import numpy as np

# own modules
import utils_process


#%% function - get_reward_paths

def get_reward_paths(Timeline):
    # gets the rewards for the paths ev1 -> .. -> ev2, as found by the
    # timeline
    # Input:
    #    > Timeline: dict of 'nodes' and 'flows' of th timeline diagram
    #                (for the description of nodes and flows, see f.e. utils_process)
    # Output:
    #    > Rewards: dict of type (ev1, ev2): reward
    
    # get the nodes and flows of the timeline
    Nt = Timeline['nodes']
    Ft = Timeline['flows']
    
    # find all start nodes of the timeline diagrams
    start_nodes = []
    for nID in Nt:
        if Nt[nID]['type'] == 'start':
            start_nodes.append(nID)
        # end if
    # end for
    
    # every diagram in timeline is like this: 
    # start -> rew0 -> ev1 -> rew1 -> rew2 -> ... -> end
    # the 1st event is start, the next is an event named as some number of days
    # and the event after it is the 2nd event in the path - then we repeat
    Rewards = {}
    
    # for all start nodes
    for startID in start_nodes:
        curr_evID = startID
        next_evID = startID
        
        while Nt[curr_evID]['type'] != 'end':
            # the child of the curr event is the 'reward event'
            interm_evID = utils_process.get_children(curr_evID, Nt, Ft)[0]
            # get the reward from it (event name be like '5 days', get the '5')
            interm_name = Nt[interm_evID]['name']
            try:
                gap_pos = interm_name.find(' ') # find the gap position in '5 days'
                rew = int(interm_name[:gap_pos]) # get the part of the str up to the '5'
            except:
                # in case of exception, we usually have something like evID -> end
                # in this case the reward is 0, continue
                curr_evID = interm_evID
                continue
            # end try
            # get the event after the reward
            next_evID = utils_process.get_children(interm_evID, Nt, Ft)[0]
            # append to the rewards dict
            Rewards[(curr_evID, next_evID)] = rew
            # this is the new current event, repeat the process
            curr_evID = next_evID
        # end while
    # end for
    
    # return rewards
    return Rewards
# end func


#%% function - get_reward_paths2

def get_reward_paths2(Timeline):
    # gets the rewards for the paths ev1 -> .. -> ev2, as found by the
    # timeline
    # Input:
    #    > Timeline: dict of 'nodes' and 'flows' of th timeline diagram
    #                (for the description of nodes and flows, see f.e. utils_process)
    # Output:
    #    > Rewards: list dicts of type (ev1, ev2): reward, one for each diagram in timeline
    
    # get the nodes and flows of the timeline
    Nt = Timeline['nodes']
    Ft = Timeline['flows']
    
    # find all start nodes of the timeline diagrams
    start_nodes = []
    for nID in Nt:
        if Nt[nID]['type'] == 'start':
            start_nodes.append(nID)
        # end if
    # end for
    
    # every diagram in timeline is like this: 
    # start -> rew0 -> ev1 -> rew1 -> rew2 -> ... -> end
    # the 1st event is start, the next is an event named as some number of days
    # and the event after it is the 2nd event in the path - then we repeat
    Rewards = [{} for _ in range(len(start_nodes))] 
    
    # for all start nodes
    cnt = -1
    for startID in start_nodes:
        cnt += 1
        curr_evID = startID
        next_evID = startID
        
        while Nt[curr_evID]['type'] != 'end':
            # the child of the curr event is the 'reward event'
            interm_evID = utils_process.get_children(curr_evID, Nt, Ft)[0]
            # get the reward from it (event name be like '5 days', get the '5')
            interm_name = Nt[interm_evID]['name']
            try:
                gap_pos = interm_name.find(' ') # find the gap position in '5 days'
                rew = int(interm_name[:gap_pos]) # get the part of the str up to the '5'
            except:
                # in case of exception, we usually have something like evID -> end
                # in this case the reward is 0, continue
                curr_evID = interm_evID
                continue
            # end try
            # get the event after the reward
            next_evID = utils_process.get_children(interm_evID, Nt, Ft)[0]
            # append to the rewards dict
            Rewards[cnt][(curr_evID, next_evID)] = rew
            # this is the new current event, repeat the process
            curr_evID = next_evID
        # end while
    # end for
    
    # return rewards
    return Rewards
# end func


#%% function - assign_rew_diags

def assign_rew_diags(Rewards, Timeline, Nall, Fall):
    # assign the rewards found in the timeline to the diagrams
    # that is, from the timeline we have (evID1_T, ev_ID2_T) -> rew,
    # where evID1_T, evID2_T are th event IDs of the timeline
    # find the diagram that contains the corresponding events (evID1, evID2)
    # and assign the reward (evID1, evID2, diag_i) -> rew to that diagram
    # collect th rewards in a dict
    # Input:
    #    > Rewards: dict of type (ev1_T, ev2_T): reward for the timeline events 
    #               (found by the function 'get_reward_paths')
    #    > Timeline: dict of 'nodes' and 'flows' of th timeline diagram
    #                (for the description of nodes and flows, see f.e. utils_process)
    #    > Nall, Fall: nodes and flows of diagram (see utils_read for details)
    # Output:
    #    > Rew_diag: dict of type (evID1, evID2, diag_i): reward, now for the 
    #               diagram IDs
    
    Rew_diag = {}
    
    # get the nodes and flows of the timeline
    Nt = Timeline['nodes']
    Ft = Timeline['flows']
    
    # for all reward pairs
    for fl in Rewards.keys():
        # get reward
        rew = Rewards[fl]
        # get evID1_T and evID2_T (for timeline)
        evID1_T, evID2_T = fl
        # get also their names
        ev1T_name = Nt[evID1_T]['name']
        ev2T_name = Nt[evID2_T]['name']
        
        # search the diagrams to find the one containing the
        # corresponding events (events with the same names as evID1_T and evID2_T)
        for i in range(len(Nall)):
            # find events by name in diagram i
            evID1 = utils_process.nodeID_fromName(ev1T_name, Nall[i])
            evID2 = utils_process.nodeID_fromName(ev2T_name, Nall[i])
            
            # if both found, append the reward to the list
            if evID1 is not None and evID2 is not None:
                Rew_diag[(evID1, evID2, i)] = rew
                break
            # end if
            
            # if one event found but the other not, we have an error
            #if [evID1, evID2] != [None, None]:
                #raise NameError('Error: Duplicate event names in diagrams')
            # end if
        # end for
    # end for
    
    # return rew
    return Rew_diag
# end func


#%% function - find_parallel_path

def find_parallel_path(startID, Ndiag, Fdiag):
    # find the end node (ID) of a parallel path starting at startID
    # a parallel path is like: startID  -> nodeID1 -> ... -> nodeIDn  -> endID
    #                                  |-> nodeID2 -> ... -> nodeIDm |
    # Input:
    #    > startID:      ID of the start node
    #    > Ndiag, Fdiag: nodes and flows of th diagram (see utils_process for details)
    # Output:
    #    > endID:        ID of the end node, or None if it doens't exist
    
    
    if len( utils_process.find_forward_children(startID, Ndiag, Fdiag) ) <= 1:
        # no parallel path starts at startID: return None
        return None
    # end if
    
    nodeID = startID # the current node
    endID = None # the end node (init to None)
    # a counter that increases when we encounter a node with many children
    # and deacreases when we find a node with many parents. When fork_cnt == 0, we have 
    # found the endID
    fork_cnt = 0 
    
    while fork_cnt >= 0:
        # get children of curr node
        children_node = utils_process.find_forward_children(nodeID, Ndiag, Fdiag)
        # get also the parents
        parents_node = utils_process.get_parents(nodeID, Ndiag, Fdiag)
        
        if len(children_node) > 1 and len(parents_node) == 1:
            # one parent and many children => increase fork counter
            fork_cnt += 1
        elif len(children_node) == 1 and len(parents_node) > 1:
            # many parents and one child => decrease fork counter
            fork_cnt -= 1
        # end if
        
        # if fork counter == 0, then we have found the join node
        # that correspond to the initila fork node
        if fork_cnt == 0:
            endID = nodeID
            break
        # end if
        
        # else find next node among the children of curr node
        for child in children_node:
            # check if a child goes 'backwards', e.g. behind the current node
            # if not, then keep it and make it the current node; e.g. follow it's path
            if (nodeID, child) == utils_process.order_nodes(nodeID, child, Ndiag, Fdiag):
                # child goes forward, keep it
                nodeID = child
                break
            # end if
        # end for
    # end while
    
    return endID
# end func
    
    

#%% function - assign_rew_nodes

def assign_rew_nodes(startID, endID, rew_start_end, Ndiag, Fdiag, Rew_nodes = {}):
    # assign rewards to the nodes of a diagram
    # if the path startID -> nodeID1 -> ... -> endID is simple and doesn't contains either
    # fork / joins or parallel paths created by decision gates, then the reward for each task
    # is simply rew_start_end / number_of_tasks; non-task nodes get reward = 0.
    # But parallel paths and fork/joins need separate handling. We will do that by identifying
    # them and calling this function recursively
    # 
    # Input:
    #    > startID, endID: IDs of the start and end node where we need to assign rewards
    #    > rew_start_end:  the total reward between the start and end node (found from timeline)
    #    > Rew_nodes:      dict that will hold the rewards assigned to each node; it will have
    #                      the form [nodeID]: reward_of_node. Initially empty
    #    > Ndiag, Fdiag:   nodes and flows of th diagram (see utils_process for details)
    # Output:
    #    > Rew_nodes: the reward for each node between startID and endID (included)
    
    
    # init
    all_nodes = [] # all nodes (IDs) betw start and end
    to_recur = [] # nodes where we need to recur at
    all_tasks = [] # all task nodes between start and end
    #Rew_nodes = {}
    
    # check if the path startID -> endID exists
    if utils_process.path_len(startID, endID, Ndiag, Fdiag) == -1:
        # path doesn't exist, return empty dict
        return {}
    # end if
    
    # count the number of tasks and parallel paths between startID and endID
    curr_node = startID
    while curr_node != endID:
        all_nodes.append(curr_node)
        # if curr_node is a task, record it
        if Ndiag[curr_node]['type'] == 'task':
            all_tasks.append(curr_node)
            # find the task's child and continue
            childID = utils_process.get_children(curr_node, Ndiag, Fdiag)[0]
            curr_node = childID
        elif Ndiag[curr_node]['type'] in ['start', 'end', 'event', 'join']:
            # event nodes and joins have reward 0, get child and continue
            childID = utils_process.get_children(curr_node, Ndiag, Fdiag)[0]
            curr_node = childID
        elif Ndiag[curr_node]['type'] == 'fork':
            # a parallel path begins at the fork node; find the corresponding join
            # also, mark the node to be recured at
            to_recur.append(curr_node)
            # the "child" is now the corresponding join node; this is where we 
            # need to continue
            next_node = find_parallel_path(curr_node, Ndiag, Fdiag)
            curr_node = next_node
        elif Ndiag[curr_node]['type'] == 'decision':
            # in decision gates, we might have a parallel path or not
            # check if we do
            next_node = find_parallel_path(curr_node, Ndiag, Fdiag)
            if next_node is None:
                # no parallel path from this decision gate; find it's forward child
                # and continue. The forward child must be only one! - otherwise, we 
                # would have parallel paths
                next_node = utils_process.find_forward_children(curr_node, Ndiag, Fdiag)[0]
                curr_node = next_node
            else:
                # otherwise, we have parallel paths, and next_node is the end of the parallel
                # in this case, add the decision gate to recur at
                to_recur.append(curr_node)
                curr_node = next_node
            # end if
        # end if
    # end while
    
    # now, we have identified all nodes in the path startID -> endID,
    # and all parallel paths where we need to recur at
    
    # first, assign rewards to the tasks we found (that do not lie in parallel paths)
    # the total reward (rew_start_end) is equally divided among all tasks, as well along
    # all parallel paths: for example a fork-join pair gets equal reward as a task - this
    # is our convention
    if len(all_tasks) + len(to_recur) > 0:
        rew_task = rew_start_end / (len(all_tasks) + len(to_recur))
    else:
        rew_task = 0
    # end if
    
    # assing the rewards to the discovered tasks
    for taskID in all_tasks:
        Rew_nodes[taskID] = rew_task
    # end for
    
    # now, for all parallel paths, call this functions recursively at the nodes
    # where we need to recur. The reward for a parallel path is also equal to rew_task
    for recur_startID in to_recur:
        # find the end for the parallel path
        recur_endID = find_parallel_path(recur_startID, Ndiag, Fdiag)
        # call the function for each one of the paths between recur_startID -> recur_endID
        chidlren_startrec = utils_process.get_children(recur_startID, Ndiag, Fdiag)
        # the reward for each parallel path is the total divided by the number of paths
        rew_parallel = rew_task / len(chidlren_startrec)
        for childID in chidlren_startrec:
            assign_rew_nodes(childID, recur_endID, rew_parallel, Ndiag, Fdiag, Rew_nodes)  
        # end for
    # end for

    # all rewards assigned, return
    # nothing to return, it's the Rew_nodes that gets modified             
    pass        

# end func


#%% function - assign_rew_process

def assign_rew_process(Timeline, Nall, Fall):
    # assign rewards to an event-based process
    # Input:
    #    > Timeline: the timeline of the process; see previous for details
    #    > Nall, Fall: the nodes and flows for all diagrams; see utils_read
    # Output:
    #    > rewards_all: list with length equal to the number of diagrams; 
    #                   rewards_all[i] is a dict of the form [nodeID] -> rew,
    #                   containing all rewards of the diagram i 
    
    # init
    rewards_all = [{} for _ in range(len(Nall))]
    
    # step 1: find the events in timeline, and get the "reward segments" ev1 -> ev2
    # Rewards contain tuples of the type (evID1, evID2): these are paths in the timeline
    # where in each path evID1 -> evID2, timeline assigns a reward
    # we use the function get_reward_paths to do this
    Rewards = get_reward_paths(Timeline)
    
    # step 2: assign the rewards found in the timeline to the diagrams
    # for each tuple (evID1, evID2), find the diagram of the path evID1 -> evID2
    # and also the total reward of that path
    # store them in Rew_diag, a dict of type (evID1, evID2, diag_i): reward
    # use function assign_rew_diags for this
    Rew_diag = assign_rew_diags(Rewards, Timeline, Nall, Fall)
    
    # step 3: for each tuple of the form (evID1, evID2, diag_i): reward, go to
    # diagram i and assign the reward to the tasks between evID1 and evID2
    # use function assign_rew_nodes for this
    
    for key in Rew_diag:
        # get events and diagram number
        evID1, evID2, diag_i = key
        # get also the reward of the path evID1 -> evID2
        reward = Rew_diag[key]
        # apply function assign_rew_nodes to get the reward of the nodes between
        assign_rew_nodes(evID1, evID2, reward, Nall[diag_i], Fall[diag_i], rewards_all[diag_i])
    # end for
    
    # finally, if some nodes do not have a reward, assign them rew = 0
    for i in range(len(Nall)):
        Ndiag = Nall[i]
        Fdiag = Fall[i]
        
        for nID in Ndiag:
            if nID not in rewards_all[i]:
                # append the node with reward 0
                rewards_all[i][nID] = 0
            # end if
        # end for
    # end for
    
    # ready, return
    return rewards_all
# end func


#%% function - get_all_names

def get_all_names(Ndiag, Fdiag):
    # get all names of a diagram's nodes
    # Input:
    #    > Ndiag, Fdiag: nodes and flows of a diagram (see utils_process for details)
    # Output:
    #    > Nnames: list of node names of diagram Ndiag
    
    Nnames = []
    
    for nID in Ndiag:
        Nnames.append(Ndiag[nID]['name'])
    # end for
    
    return Nnames
# end func


#%% function - assign_rew_diags2

def assign_rew_diags2(Rewards, Timeline, Nall, Fall):
    # assign the rewards found in the timeline to the diagrams
    # that is, from the timeline we have (evID1_T, ev_ID2_T) -> rew,
    # where evID1_T, evID2_T are th event IDs of the timeline
    # find the diagram that contains the corresponding events (evID1, evID2)
    # and assign the reward (evID1, evID2, diag_i) -> rew to that diagram
    # collect th rewards in a dict
    # Input:
    #    > Rewards: dict of type (ev1_T, ev2_T): reward for the timeline events 
    #               (found by the function 'get_reward_paths')
    #    > Timeline: dict of 'nodes' and 'flows' of th timeline diagram
    #                (for the description of nodes and flows, see f.e. utils_process)
    #    > Nall, Fall: nodes and flows of diagram (see utils_read for details)
    # Output:
    #    > Rew_diag: dict of type (evID1, evID2, diag_i): reward, one for each diag
    
    Rew_diag = {}
    
    # for each diagram in the timeline, find the corresponding diagram in the process (Nall)
    # we find the event names from a timeline diagram, and find the diagram in Nall that contains
    # them all
    
    # get the nodes and flows of the timeline
    Nt = Timeline['nodes']
    Ft = Timeline['flows']
    
    event_names = [[] for _ in range(len(Nall))]
    for i in range(len(Rewards)):
        # collect all event names in the rewards of that timeline diagram (i)
        cnt = -1
        for fl in Rewards[i]:
            cnt += 1
            evID1, evID2 = fl
            _, ev_name1, _ = utils_process.get_diag_name_type(evID1, [Nt])
            _, ev_name2, _ = utils_process.get_diag_name_type(evID2, [Nt])
            
            # the timeline is like: start -> ev1 -> ev2 -> ... -> ev_n
            # the reward tuples are like: (sart, ev1), (ev1, ev2), ..., (ev_[n-1], ev_n)
            # to append them, we append in the begining both start and ev1, but afterwards
            # wenn cnt > 0 we append only the 2nd event, eg. only ev2 from (ev1, ev2)
            # only ev3 from (ev2, ev3), etc.
            if cnt == 0:
                event_names[i].append(ev_name1)
                event_names[i].append(ev_name2)
            else:
                event_names[i].append(ev_name2)
            # end if
        # end for
    # end for
    
    # for each diagram in the timeline, find the corrsponding diagram in the 
    # process that contains all names
    
    corresp = [] # list that holds the corresponding diagrams
    # corresp[i] = j means that diagram j in Nall corresponds to diag i in Timeline
    
    for i in range(len(event_names)):
        for j in range(len(Nall)):
            # get names of Nall[j]
            Nj_names = get_all_names(Nall[j], Fall[j])
            # if all timeline diagram names (events) are contained in this diagram
            # then they match
            if set(event_names[i]).issubset(Nj_names):
                corresp.append(j)
                break
            # end if
        # end for
    # end for
    
    # now the final step: for each timeline diagram, start scanning the
    # corresponding diagram in Nall, Ndiag. While scanning, get one reward
    # pair (evID1, evID2) from Rewards. When we find the two names of the events
    # in Ndiag, assign the tuple, remove it and get the next one
    
    # list of lists holding th corresponding event IDs in Nall
    event_IDs = [[] for _ in range(len(event_names))]
    
    for i in range(len(Rewards)):
        # get the corresponding process diagram
        Ndiag = Nall[corresp[i]]
        Fdiag = Fall[corresp[i]]
        
        # find th start of Ndiag
        startID = utils_process.find_start(Ndiag)
        # def BFS Q and visited list V
        Q = [startID]
        V = []
        # a counter to indicate the current event name we are searching
        ev_cnt = 0
        
        # start BFS on Ndiag
        while Q != []:
            currID = Q.pop(0)
            if currID not in V:
                V.append(currID)
            # end if
            curr_name = Ndiag[currID]['name']
            if ev_cnt >= len(event_names[i]):
                # we found all events, break
                break
            # end if
            if curr_name == event_names[i][ev_cnt]:
                # we found the next event ID
                event_IDs[i].append(currID)
                ev_cnt += 1
            # end if
            
            # continue BFS
            children = utils_process.get_children(currID, Ndiag, Fdiag)
            for chID in children:
                if chID not in V:
                    Q.append(chID)
                # end if
            # end for
        # end while
    # end for
    
    # finally, create Rew_diag
    for i in range(len(event_IDs)):
        diag_i = corresp[i]
        rewards_i = list(Rewards[i].values())
        
        for j in range(len(event_IDs[i]) - 1):
            evID1 = event_IDs[i][j]
            evID2 = event_IDs[i][j + 1]
            rew = rewards_i[j]
            
            Rew_diag[(evID1, evID2, diag_i)] = rew
        # end for
    # end for
    
    # ready
    return Rew_diag
# end func
                
            
#%% function - assign_rew_process2

def assign_rew_process2(Timeline, Nall, Fall):
    # assign rewards to an event-based process
    # Input:
    #    > Timeline: the timeline of the process; see previous for details
    #    > Nall, Fall: the nodes and flows for all diagrams; see utils_read
    # Output:
    #    > rewards_all: list with length equal to the number of diagrams; 
    #                   rewards_all[i] is a dict of the form [nodeID] -> rew,
    #                   containing all rewards of the diagram i 
    
    # init
    rewards_all = [{} for _ in range(len(Nall))]
    
    # step 1: find the events in timeline, and get the "reward segments" ev1 -> ev2
    # Rewards contain tuples of the type (evID1, evID2): these are paths in the timeline
    # where in each path evID1 -> evID2, timeline assigns a reward
    # we use the function get_reward_paths to do this
    Rewards = get_reward_paths2(Timeline)
    
    # step 2: assign the rewards found in the timeline to the diagrams
    # for each tuple (evID1, evID2), find the diagram of the path evID1 -> evID2
    # and also the total reward of that path
    # store them in Rew_diag, a dict of type (evID1, evID2, diag_i): reward
    # use function assign_rew_diags for this
    Rew_diag = assign_rew_diags2(Rewards, Timeline, Nall, Fall)
    
    # step 3: for each tuple of the form (evID1, evID2, diag_i): reward, go to
    # diagram i and assign the reward to the tasks between evID1 and evID2
    # use function assign_rew_nodes for this
    
    for key in Rew_diag:
        # get events and diagram number
        evID1, evID2, diag_i = key
        # get also the reward of the path evID1 -> evID2
        reward = Rew_diag[key]
        # apply function assign_rew_nodes to get the reward of the nodes between
        assign_rew_nodes(evID1, evID2, reward, Nall[diag_i], Fall[diag_i], rewards_all[diag_i])
    # end for
    
    # finally, if some nodes do not have a reward, assign them rew = 0
    for i in range(len(Nall)):
        Ndiag = Nall[i]
        Fdiag = Fall[i]
        
        for nID in Ndiag:
            if nID not in rewards_all[i]:
                # append the node with reward 0
                rewards_all[i][nID] = 0
            # end if
        # end for
    # end for
    
    # ready, return
    return rewards_all
# end func

    
    
