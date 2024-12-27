# -*- coding: utf-8 -*-
"""
web GUI for SMC4PEP
"""

#%% imports

import time
import os
import sys
from zipfile import ZipFile
import pandas as pd

from flask import Flask, flash, render_template, request, redirect, url_for, send_from_directory, session
from werkzeug.utils import secure_filename
#app = Flask(__name__)
app = Flask(__name__, static_url_path='/static')
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

# own modules
sys.path.append('../utils')
import utils_all


#%% app params

ALLOWED_EXTENSIONS = {'xml'}

app.config['UPLOAD_FOLDER'] = os.path.abspath('upload')
app.config['DOWNLOAD_FOLDER'] = os.path.abspath('download')


#%% functions

def allowed_file(filename):
    # take the file ending
    # e.g. 'example.xml' -> 'xml
    ftype = filename[-3:]
    # check if included in allowed file types
    # return True if OK, False otherwise
    return (ftype in ALLOWED_EXTENSIONS)

def clear_files(fpath):
    # clear all files in a folder
    # get files
    fnames = os.listdir(fpath)
    # remove them
    for fn in fnames:
        fn_path = os.path.join(fpath, fn)
        os.remove(fn_path)
    return

def save_prism_excel(filename, prism_data, nodes_states, save_path):
    # save the generated prism and excel files and zip them
    # Input:
    #    > filename: the name of the BPMN file (str)
    #    > prism_data: data for the prism file (str)
    #    > nodes_states: data for the excel file (DataFrame)
    #    > save_path: path to save the zip generated file
    # Output:
    #    > zip_name: name of the generated zip file (str)
    
    # file 1 is the prism file, it has the same name as the original file
    # but ends in 'mdp'.
    # remove the '.xml' part and replace by '_prism.mdp' 
    default_name = filename[:-4] + '_prism.mdp'
    # save files in download folder
    f_path1 = os.path.join(save_path, default_name)
    with open(f_path1, 'w') as fp:
        fp.write(prism_data)
    # set name for the excel file
    excel_name = filename[:-4] + '_bpmn_nodes_to_states.xlsx' 
    # save files in download folder
    f_path2 = os.path.join(save_path, excel_name)
    nodes_states.to_excel(f_path2)
    
    # zip the 2 files
    zip_name = filename[:-4] + '_converted.zip'
    zip_path = os.path.join(save_path, zip_name)
    with ZipFile(zip_path,'w') as Zip:
        # writing each file one by one
        Zip.write(f_path1, os.path.basename(f_path1))
        Zip.write(f_path2, os.path.basename(f_path2))
    # end with
    
    # delete the files
    os.remove(f_path1) 
    os.remove(f_path2) 
    
    # return the zip name
    return zip_name


#%% flask urls

@app.route('/', methods = ['GET', 'POST'])
def index():
    if request.method == 'POST':
        # clear all previous files
        clear_files(app.config['UPLOAD_FOLDER'])
        clear_files(app.config['DOWNLOAD_FOLDER'])
        # sanity checks
        if 'file' not in request.files:
            flash('Error: No file attached in request!')
            return redirect(request.url)
        fp = request.files['file']
        if fp.filename == '':
            flash('Error: No file selected!')
            return redirect(request.url)
        if not allowed_file(fp.filename):
            flash('Error: Your process must be expressed as an xml file!')
            return redirect(request.url)
        # make secure file name
        file = request.files['file']
        filename = secure_filename(file.filename)
        # save file in upload folder
        f_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(f_path)
        
        # try to process file
        no_errors = False
        try:
            # convert to prism
            prism_data, nodes_states = utils_all.bpmn2prism(f_path, remove_redund = True)
            no_errors = True
        except:
            no_errors = False 
        # end try
        # clear input file
        #os.remove(f_path) 
        # if errors, throw error
        if not no_errors:
            flash('Error: your xml file contains errors, please check the specifications!')
            return redirect(request.url)
        
        # else, save output files in a zip in downloads folder
        zip_name = save_prism_excel(filename, prism_data, nodes_states, app.config['DOWNLOAD_FOLDER'])

        # send the zip for download
        session.pop('_flashes', None)
        return redirect(url_for('uploaded_file', filename = zip_name))
    return render_template('index.html')


@app.route('/upload/<filename>')
def uploaded_file(filename):
    session.pop('_flashes', None)
    return send_from_directory(app.config['DOWNLOAD_FOLDER'], filename, as_attachment=True)




 
    
#%% main

if __name__ == '__main__':
   app.run(debug = False)




