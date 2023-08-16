# -*- coding: utf-8 -*-
"""
Created on Thu Dec  3 14:22:46 2020

@author: foivo

"""
import core_scheduling as cs
import events_managment as evm
import data_results_integrity as dri
import copy
import kpi_calculation as kpi


def scheduling(dt):
    #this variable controls whether the algorithm will enter the events managment script or not. 
    #This is required in order to differenciate from initial running for the 
    #calculation of the estimated order makespans during the data loading
    
    dt=evm.events_initialization(dt)
    temp_list=[]
    for i in range(10):
        
        test=cs.core(copy.deepcopy(dt))
        test=kpi.production_cost_calculation(test)      #calculate operational and raw materials cost
        test=kpi.tardiness_calculation(test)                #calculate the tardiness for each order
        
        
        check=dri.check_if_all_tasks_were_assigned(test)
        temp_list.append([copy.deepcopy(check)])
        print(i)
    return dt
    
