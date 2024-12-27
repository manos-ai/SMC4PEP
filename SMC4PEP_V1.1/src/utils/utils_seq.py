# -*- coding: utf-8 -*-
"""
utils to check semantic equivalence between pool and event based diagrams
"""

#%% imports

import numpy as np
import matplotlib.pyplot as plt

# own modules
import utils_read
import utils_process


#%% remove event

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


#%% add msg flow "behind" corresponding events

def get_msg_flow_events(ev_source, ev_target, diag_source, diag_target, N, F):
    # add a msg flow from the parent task of ev_source to the parent of ev_target
    # that is, we have: task1 -> ev_source in diag1 and task2 -> ev_target in diag2
    # now we connect task1 and task2 with the messag flow task1 ---> task2
    # Input:
    #    > ev_source, ev_target: the source and target events (IDs)
    #    > diag_source, diag_target: the source and target diagrams
    #    > N, F: nodes and flow of the (event- based) process
    
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
    
    # return messag flow between task1 and task2
    flow = (task1, task2)
    return flow
# end func


    
    
    
    



