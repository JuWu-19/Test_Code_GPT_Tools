# -*- coding: utf-8 -*-
"""
Created on Thu Dec  3 18:01:28 2020
03.12.2020 file created to write the code for the  creation of GUI

@author: foivo
"""

# file ='dataStructure_v1.0.xlsx'


import tkinter as tk                     
from tkinter import ttk 

import scheduling_main as scd
import data_loading as dl

'''
from pycallgraph import PyCallGraph
from pycallgraph.output import GraphvizOutput

with PyCallGraph(output=GraphvizOutput()):
    # your code here
'''
heuristic_method=1
file='dataStructure_v1.0.xls'
number_of_shifts=8 # it is not shifts but working hours
buffersOption=0     # 1 is the option for finite buffers, 0 is infinent
batch_ind_var=0
defect_future_in=0
defect_generation_active=True #variable for saving the prefered defect type


global results
global scheduling_results
solution=None
check=1
data=()                     #global variable for storing the loaded data
final_scheduling_results=() #global variable for storing the scheduling results
user_settings=0

# #################################################################
class settings:
    def __init__(self,file_path,method,number_of_shifts,buffers_policy,batch_individual_loading_policy,defect_generation_active,defect_future_policy):
        self.file_path=file_path
        self.method=method
        self.number_of_shifts=number_of_shifts
        self.buffers_policy=buffers_policy
        self.batch_individual_loading_policy=batch_individual_loading_policy
        self.defect_generation_active=defect_generation_active
        self.defect_generation_type_master=defect_generation_active   #its a variable for having the real selection, this is required because of the initial calculations during the data loading, where no defects are considered
        self.minutes_per_day=1440       #the amount of minutes that a day (24 hours) have
        self.defect_future_policy=defect_future_policy



# #################################################################  
root = tk.Tk() 
root.title("ZDMap") 
root.geometry('900x700')
tabControl = ttk.Notebook(root) 
  
tab1 = ttk.Frame(tabControl) 
tab2 = ttk.Frame(tabControl) 
  
tabControl.add(tab1, text ='Tab 1') 
tabControl.pack(expand = 1, fill ="both") 
tabControl.add(tab2, text ='Tab 2') 
tabControl.pack(expand = 1, fill ="both") 


def file_path():
    inputVal=textBox.get("1.0", "end-1c")
    print(inputVal)
    filePath=inputVal
    return filePath

def scheduling_method():
    global var
    method=var.get()
    return method

def numberOfShifts():
    global shifts
    num_shifts=shifts.get()
    return num_shifts

def buffers_policy():
    global buffers_option
    buffersPolicy=buffers_option.get()
    return buffersPolicy

def batch_ind_policy():
    global batch_ind_option
    batchIndPolicy=batch_ind_option.get()
    return batchIndPolicy

def defect_generation_policy():
    global defect_generation_type_option
    defect_p=defect_generation_type_option.get()
    return defect_p

def defect_future_policy():
    global defect_future
    defect_f=defect_future.get()
    return defect_f    
    
textBox=tk.Text(tab1, height=2, width=30)
textBox.grid(row=1, column=1)
textBox.insert(tk.END,file) #initialize the path file
# textBox.pack()

def btn1t1_comands():
    global data
    global user_settings
    filePath=file_path()
    sch_method=scheduling_method()
    number_of_shifts=numberOfShifts()
    buffersPolicy=buffers_policy()
    batchInd_policy=batch_ind_policy()
    defect_policy=defect_generation_policy()
    defect_future=defect_future_policy()
    
    settings_cl=settings(filePath,sch_method,number_of_shifts,buffersPolicy,batchInd_policy,defect_policy,defect_future)
    tmp=dl.data_loading(settings_cl)
    user_settings=settings_cl
    data=tmp
    results.set("success")
    label1t1.config(text=results.get())


results=tk.StringVar()
scheduling_results=tk.StringVar()

if check == 1:
    results.set("nothing loaded")
    scheduling_results.set("click Run")
    check=0
 
def btn2t1_comands():
    global solution
    solution=scd.scheduling(data)
    scheduling_results.set("Scheduling Finished") 
    label2t1.config(text=scheduling_results.get())
    
    
    
# ##########################################################################
#heuristics method radio button
tk.Label(tab1, text=" ").grid(row=3,column=1) 
tk.Label(tab1, text="Scheduling Method Selection").grid(row=4,column=1)    

var = tk.IntVar(None,heuristic_method)  
R1 = tk.Radiobutton(tab1, text="Random", justify='left', variable=var, value=1)
R1.grid(row=5, column=1 )
R2 = tk.Radiobutton(tab1, text="Option 2", variable=var, value=2)
R2.grid(row=6, column=1 )
R3 = tk.Radiobutton(tab1, text="Option 3", variable=var, value=3)
R3.grid(row=7, column=1 )
# #########################################################################

# ##########################################################################
#number of shifts radio button
tk.Label(tab1, text=" ").grid(row=8,column=1) 
tk.Label(tab1, text=" ").grid(row=9,column=1) 
tk.Label(tab1, text="Number of shifts Selection").grid(row=10,column=1)

shifts = tk.IntVar(None,number_of_shifts)  
R1 = tk.Radiobutton(tab1, text="One Shift",  variable=shifts, value=8)
R1.grid(row=11, column=1 )
R2 = tk.Radiobutton(tab1, text="Two Shifts", variable=shifts, value=16)
R2.grid(row=12, column=1 )
R3 = tk.Radiobutton(tab1, text="Three Shifts", variable=shifts, value=24)
R3.grid(row=13, column=1 )
# #########################################################################

# ##########################################################################
# buffers strategy, infinite or finite
tk.Label(tab1, text=" ").grid(row=14,column=1) 
tk.Label(tab1, text=" ").grid(row=15,column=1) 
tk.Label(tab1, text="Buffers policy").grid(row=16,column=1)

buffers_option = tk.IntVar(None,buffersOption)  
R4 = tk.Radiobutton(tab1, text="Infinite buffers capacity",  variable=buffers_option, value=0)
R4.grid(row=17, column=1 )
R5 = tk.Radiobutton(tab1, text="Finite buffers capacity", variable=buffers_option, value=1)
R5.grid(row=18, column=1 )

# #########################################################################

# ##########################################################################
# Batch individual process settign selection, two options that deferenciate the loading of the batch_ind machine, 
#option 1 load each part when it is ready and remove it from the buffer
#optin 2 keep all the parts to the buffers until the capacity of batch_ind processes reaches the capacity of the batch_ind machine and load them all together
tk.Label(tab1, text=" ").grid(row=19,column=1) 
tk.Label(tab1, text=" ").grid(row=20,column=1) 
tk.Label(tab1, text="Batch individual process policy").grid(row=21,column=1)

batch_ind_option = tk.IntVar(None,batch_ind_var)  
R6 = tk.Radiobutton(tab1, text="Load each part and remove it from buffer",  variable=batch_ind_option, value=0)
R6.grid(row=22, column=1 )
R7 = tk.Radiobutton(tab1, text="Load all the parts at the same time, keeping them in Buffer", variable=batch_ind_option, value=1)
R7.grid(row=23, column=1 )

# ##########################################################################
# Options for selecting whether there are defets or not
#option 1 No defects
#optoin 2 With defects
tk.Label(tab1, text="Batch individual process policy").grid(row=4,column=2)

defect_generation_type_option = tk.BooleanVar(None,defect_generation_active)  
R8 = tk.Radiobutton(tab1, text="No defects",  variable=defect_generation_type_option, value=False)
R8.grid(row=5, column=2 )
R9 = tk.Radiobutton(tab1, text="With defects",  variable=defect_generation_type_option, value=True)
R9.grid(row=6, column=2 )

# ##########################################################################
# Options for selecting how to decide the future of each defect, to repair or to discard
#option 1 Random
#optoin 2 With DSS
tk.Label(tab1, text=" ").grid(row=7,column=2) 
tk.Label(tab1, text=" ").grid(row=8,column=2) 
tk.Label(tab1, text="Defect future").grid(row=9,column=2)

defect_future = tk.IntVar(None,defect_future_in)  
R10 = tk.Radiobutton(tab1, text="Random",  variable=defect_future, value=0)
R10.grid(row=10, column=2 )
R11 = tk.Radiobutton(tab1, text="DSS",  variable=defect_future, value=1)
R11.grid(row=11, column=2 )



# #########################################################################
###
btn1t1=tk.Button(tab1, text='Load Data', command=lambda: btn1t1_comands())
btn1t1.grid(row=1, column=2)

btn2t1=tk.Button(tab1, text='run button', command=lambda: btn2t1_comands())
btn2t1.grid(row=2, column=2)

label1t1=tk.Label(tab1, text=results.get())
label1t1.grid(row=1, column=3) 

label2t1=tk.Label(tab1, text=scheduling_results.get())
label2t1.grid(row=2, column=3) 
  
root.mainloop()  