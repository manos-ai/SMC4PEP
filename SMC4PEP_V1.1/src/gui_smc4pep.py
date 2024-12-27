# -*- coding: utf-8 -*-
"""
converter gui
"""

#%% imports

import sys
sys.path.append('utils')

import tkinter as tk
from tkinter import filedialog
#from tkinter import ttk

# own modules
import utils_all


#%% funcs

def UploadAction(event=None):
    filename = filedialog.askopenfilename()
    myfiles.append(filename)
    print('Selected:', filename)
    
def ConvertDiagrams(event=None):
    # get bpmn file name
    bmpn_file = myfiles[-1]
    # default file name to display; it's same as input xml file, but without the
    # xml ending, and with _prism.mdp instead
    # example: input file = 'myprocess.xml' -> output name = myprocess_prism.mdp
    # remove the ending '.xlm', and append '_prism.mpd'
    default_name = bmpn_file[:-4] + '_prism'
    
    # convert to prism
    prism_data, nodes_states = utils_all.bpmn2prism(bmpn_file, remove_redund = True)
    
    # save prism model into file
    f = filedialog.asksaveasfile(mode='w', initialfile = default_name, defaultextension='.mdp')
    if f is None: # asksaveasfile return `None` if dialog closed with "cancel".
        return
    text2save = prism_data
    f.write(text2save)
    f.close()
    
    # save also the node to prism states table (in excel)
    # the excel name will be the same with the prism name, but without the endian
    # and with the extension '_bpmn_nodes_to_states.xlsx'
    # for example: prism file = 'myprocess.mdp' -> excel = 'myprocess_bpmn_nodes_to_states.xlsx' 
    save_name = f.name
    excel_name = save_name[:-4] + '_bpmn_nodes_to_states.xlsx' 
    nodes_states.to_excel(excel_name)  
    

#%% main

myfiles = []

# def a tkinter window
root = tk.Tk()
root.geometry('300x200')
root.configure(background='gray')
# set window title
root.title('SMC4PEP')


button1 = tk.Button(root, text='upload bpmn model (xml)', command=UploadAction, bg='black', fg='white')
button1.pack(side=tk.LEFT, padx = 5)

#c = tk.Checkbutton(root, text = 'Python')
#c.pack(side=tk.RIGHT, padx = 5)

button2 = tk.Button(root, text='convert to PRISM', command = ConvertDiagrams, bg='red', fg='white')
button2.pack(side=tk.BOTTOM, padx = 5)


root.mainloop()

