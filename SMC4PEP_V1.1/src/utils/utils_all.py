# -*- coding: utf-8 -*-
"""
combine all utils to convert a process (either event or pool-based)
"""

#%% imports

import sys
# add parent dir to sys, so that we can import from it
#sys.path.append('..')

# own modules
import utils_read
import rem_redundancy
import utils_process
import utils_convert
import utils_rewards


#%% function differentiator

def differentiator(xml_file_process):
    # checks if a process is pool- or event-based
    # Input:
    #    > xml_file_process: the xml file describing the BPMN model (str)
    # Output:
    #    > process_type: either 'pool_based' or 'event_based' (str)
    
    # check if there exists a timeline
    try:
        _, _, Timeline = utils_read.read_process_events(xml_file_process)
        Fmsg = None
    except:
        Timeline = None
    # check also if there exist message flows
    try:
        _, _, Fmsg = utils_read.read_process_pools(xml_file_process)
        Timeline = None
    except:
        Fmsg = None
    # end try
    
    # if we have a timeline and no message flows, then it's event based
    if Timeline is not None and Fmsg is None:
        return 'event_based'
    else:
        # otherwise it's pool-based
        return 'pool_based'
    # end if
    
# end func


#%% function converter

def converter(Nall, Fall, Fmsg):
    # in a pool-based process, remove the redundancy, and find the
    # resulting new message flows (as a list of matching nodes, similar to the
    # event-based)
    # Input:
    #    > Nall, Fall, Fmsg: nodes and flows of the process (see utils_read for specification)
    # Output:
    #    > Nall_new, Fall_new, Fmsg_new: the mew process, with redundancy removed
    
    Nall_new, Fall_new, Emsg = rem_redundancy.remove_redundancy(Nall, Fall, Fmsg)
    return Nall_new, Fall_new, Emsg
# end func


#%% function generator


def generator(Nall, Fall, Fmsg, Timeline, process_type):
    # generate a prism DAT file for the given bpmn process
    # Input:
    #    > Nall, Fall: nodes and flows of the process (s. utils_read for details)
    #    > Fmsg, Timeline: message flows (or matching events) and timeline, depending
    #                      on the case; e.g. if pool-based, we have Fmsg, and Timeline is None
    #    > process_type: either 'pool_based' or 'event_based' (str)
    # Output:
    #    > prism_process_str: string describing the prism model
    
    process_str = None
    
    if process_type == 'pool_based':
        process_str = utils_convert.convert_process(Nall, Fall, Fmsg, None)
    elif process_type == 'event_based':
        # get matching events
        _, _, Fmsg = rem_redundancy.events_to_flows3(Nall, Fall)
        # get the rewards
        rewards_all = utils_rewards.assign_rew_process2(Timeline, Nall, Fall)
        # convert 
        process_str = utils_convert.convert_process(Nall, Fall, Fmsg, rewards_all)
    # end if

    return process_str
# end func

#%% function bpmn2prism

def bpmn2prism(xml_file_process, remove_redund = True):
    # the main function to convert a process from BPMN into a PRISM file
    # Input:
    #    > xml_file_process: the xml file describing the BPMN model (str)
    #    > remove_redund: if True, the method will try to remove redundancy in case of a
    #                     pool-based process
    # Output:
    #    > prism_data: the prism model description, to be dumped into a file (str)
    #    > nodes_states: data frame mapping bpmn nodes to prism states
    
    # get process type (pools or events)
    process_type = differentiator(xml_file_process)
    
    # read the process from xml
    if process_type == 'pool_based':
        Nall, Fall, Fmsg = utils_read.read_process_pools(xml_file_process)
        Timeline = None
        if remove_redund:
            Nall, Fall, Fmsg = converter(Nall, Fall, Fmsg)
        # end if
    else:
        Nall, Fall, Timeline = utils_read.read_process_events(xml_file_process)
        Fmsg = None
    # end if
    
    # generate prism description
    prism_data = generator(Nall, Fall, Fmsg, Timeline, process_type) 
    
    # finally, generate also table nodes_states that maps the BPMN diagram nodes
    # into their corresponding prism modules and states. This is very useful for
    # defining additional properties in prism
    nodes_states = utils_convert.nodes_to_states_map(Nall, Fall, Fmsg)

    # ready
    return prism_data, nodes_states
# end func