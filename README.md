# SMC4PEP

SMC4PEP is a tool for converting business processes expressed in the BPMN language into a Markov Decision Process (MDP) file that can be then analyzed by the PRISM model checker, to verify its properties. The BPMN process can be expressed either as a pool-based process (pBPMN), or with the event-based (eBPMN) modelling approach. 

## Getting started
First, we need to make sure that Python 3 is installed on our PC. Then, the packages described in `requirements.txt` need to be installed, for example via pip. The tool should run with all standard operating systems.

After that, we go to the web GUI, located in `SMC4PEP_v1.1/src/web_gui/app.py` and run it in Phyton. After running this script, in the Consol of Phyton the address `http://127.0.0.1:5000/`appears. Then, the user can open a browser (we prefer Google Chrome) and paste the copied address: `http://127.0.0.1:5000/` of the Control into the browser. Finally,the web GUI is displayed. Then the user can upload a BPMN process model described in a XML file with the button `Choose File` and convert the input file into an MDP described in the syntax of PRISM by selecting the button `Convert to PRISM`. Finally, the user can download the corresponding file (packed in a zip file, along with the .dat file that describes the BPMN and PRISM states correspondence).

You can also run this web GUI without installation, by going to the following address: `http://smc4pep.pythonanywhere.com/`

Finally, the program creates an additional excel file along with the mdp model described in PRISM syntax. This file contains a table that maps the BPMN process nodes (tasks, events, etc.) with their corresponding prism modules and states. In that way, the user knows the prism state that corresponds to any given BPMN node. This is useful if the user would like to define additional properties into PRISM (apart from the default ones), that can be then verified. 

Apart from the web GUI, we provide also a desktop GUI `SMC4PEP_v1.1/src/gui_smc4pep.py`. After running the file in Phyton the SMC4PEP GUI will start, and prompt the user to upload a BPMN process model described in a XML file by selecting the upper button (upload BPMN model XML). Then by selecting the second button (Convert to PRISM), the file will be converted in a PRISM '.mdp' file describing the inital process model in an MDP described in the syntax of PRISM. The user can save the output file in a folder of choice and then open it with the PRISM model checker. 


## Tool structure
The source code is located in the `src` file inside the main folder of the tool (`SMC4PEP_v1.1`). This contains the GUI, as well as the utilities needed to implement the conversion, which are stored in the `src/utils` folder. Finally, the main folder contains also some example BPMN processes (xml files), where the user can run the tool. We have also included pictures of these process diagrams, so that the user does not need an additional software (e.g. Enterprise Architect, etc.) to view them.


## License
This tool is provided under the GPL v3.0 license.


## Run an example

Some results of the paper `SMC4PEP: A Conversion Tool for an Automated Verification of Product Engineering Processes` can be reproduced based on the files located in `SMC4PEP_v1.1/examples/UC from Journal`. For a detailed instruction for reproducing the results of the UC of the paper, refer to the folder `SMC4PEP_v1.1/examples/UC from Journal`.

To run one of the examples please apply the following steps (for the web App):
1. Open a Phyton IDE

2. Open and run the file `app.py` located in `SMC4PEP_v1.1/src/web_gui/app.py`

3. Copy the address `http://127.0.0.1:5000/` displayed in the Console of Phyton

4. Paste the copied adress in a browser (e.g. Google Chrome) and press enter
    -> SMC4PEP web GUI is opend
    
5. Upload the file e.g. `UC_Abstr_level_1.xml` located in  `SMC4PEP_v1.1/examples/UC from Journal/Row 1 of Table2 Abstr. level 1/Process Model (eBPMN Design)` by using the button `Choose File` of SMC4PEP

6. Activate the enginges of SMC4PEP for converting the input fil into an MDP by selecting the green button `Convert to PRISM`
    -> a new file is generated
    
7. Save the output of SMC4PEP in a folder of choice 
    ->now the inital business process model described in BPMN is converted into an MDP. 
    
8. For verifying properties of interest: open PRISM (or another model checker which is able to read PRISM files) and upload the output of SMC4PEP

9. Now properties of interest can be verified

##Verifying properties in PRISM

We have included some standard properties in `src/properties/sample_properties.txt`. 

For example, in order to verify that a process finishes with no deadlocks, 
the user can verify in PRISM the following property: `Pmin = ? [F "end_state" = true]`. 
SMC4PEP automatically identifies the end state of the process and labels it as ` end_state`. 
Thus, the above calculates the probability of reaching the end state. This has to be equal to 1.


An another example, we can calculate the expected reward by simulating in PRISM the property: `R = ?`.

Finally, in order to allow to the user to define additional properties, SMC4PEP also outputs,
apart from the MDP model in PRISM, an excel file that maps BPMN nodes (tasks, gates, etc.) of
each diagram into their corresponding PRISM state. For example if ‘task A’ is mapped to MDP 
state ‘s0 = 14’ and ‘task B’ to the MDP state ‘s1 = 18’, then we can write the property 
“task A si always reached before task B” as `P = ? [A !s1 = 18 U s0 = 14]`. 

   
