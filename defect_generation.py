# -*- coding: utf-8 -*-
"""
Created on Wed Jan 20 19:29:50 2021

@author: foivo
"""
import math
import random
import copy
import events_managment as evm


def coeficients_calculation(defect_profile,avg_pt,MTBT,defect_rate):
    estimated_tasks=MTBT/avg_pt
    total_defects_per_period=estimated_tasks*defect_rate
    
    if defect_profile==0:       # for exponential defects generation
        coef=10-math.log(total_defects_per_period)        #10 is defined by me for moving the graph to the right
    elif defect_profile==1:     # for linear defects generation
        coef=total_defects_per_period/MTBT          #linear function with y(0)=0, of the for y=a*x
    elif defect_profile==2:     # for random defects generation
        coef=None

    return int(total_defects_per_period),coef
    
# ###########################################################################################
def quality_assignment(dt,machine_index): # @ sol_assign_lists
    if dt.settings.defect_generation_active==True:
        # #Exponential ##########################################################################################
        if dt.solution_list[machine_index[0][0]][2].defect_profile==0: # for exponential defects generation
            defect_n=exponential_defect(dt,machine_index)
            dt=defect_assignment(dt,defect_n,machine_index)
            
        # #Linear ##########################################################################################    
        elif dt.solution_list[machine_index[0][0]][2].defect_profile==1: # for linear defects generation
            defect_n=linear_defect(dt,machine_index)
            dt=defect_assignment(dt,defect_n,machine_index)
            
        # #Random ##########################################################################################    
        elif dt.solution_list[machine_index[0][0]][2].defect_profile==2:# for random defects generation, without machine deterioration
            prob=random.random()
            if prob>dt.solution_list[machine_index[0][0]][2].defectRate:
                dt.task_to_assign.quality=True     # True means that NO defect
            else:
                 dt.task_to_assign.quality=False    # False means Defect
        # ###########################################################################################         
        if dt.task_to_assign.quality==False: # if it is a defect then increase the count by one, to keep track of the total defects at this machine
            dt.solution_list[machine_index[0][0]][2].defects_count+=1       #total
            dt.solution_list[machine_index[0][0]][2].period_dedects+=1      # preriod, this will be used for the detection prevention strategy
        
        dt=allowed_defect_check(dt,machine_index)
    
    return dt

# ###########################################################################################

def exponential_defect(dt,machine_index):
    cof=defect_distribution_data(dt,machine_index)
    defect_n=math.exp((10*cof[2]/cof[1])-cof[0])
    return defect_n

def linear_defect(dt,machine_index):
    cof=defect_distribution_data(dt,machine_index)
    defect_n=cof[0]*cof[2]
    return defect_n

# ###########################################################################################
def defect_assignment(dt,defect_n,machine_index):
    if dt.task_to_assign.defect_once==False:
        if dt.task_to_assign.task_type=='normal' or dt.task_to_assign.task_type=='inspection':
            if int(defect_n-dt.solution_list[machine_index[0][0]][2].previous_defect_n)>1:
                dt.task_to_assign.quality=False
                # previous_defect_n correction/ update/ if it is not a defect then no correction is required
                if int(defect_n-dt.solution_list[machine_index[0][0]][2].previous_defect_n)>2: #if the difference from the previous corresponds to more than one defect assign the value of the previous +1
                   dt.solution_list[machine_index[0][0]][2].previous_defect_n+=1
                else:
                    dt.solution_list[machine_index[0][0]][2].previous_defect_n=defect_n
            else:
                dt.task_to_assign.quality=True
        elif dt.task_to_assign.task_type=='batch_all' or dt.task_to_assign.task_type=='batch_ind': # in the event of batch processes
            for b_t in dt.batch_task_to_assign.included_tasks:
                b_t.quality=True
        elif dt.task_to_assign.task_type=='repair':
            dt.task_to_assign.quality=True
    else:
        dt.task_to_assign.quality=True # in order not to get defected the replaced task

    return dt
        


# ###########################################################################################
def defect_distribution_data(dt,machine_index):
    coef=dt.solution_list[machine_index[0][0]][2].defect_generation_coefficient
    MTBT=dt.solution_list[machine_index[0][0]][2].MTBT
    period_pt=dt.solution_list[machine_index[0][0]][2].period_processing_time
    return   coef, MTBT ,period_pt 
       
# ###########################################################################################
def allowed_defect_check(dt,machine_index):
    actual_defect_ratio=dt.solution_list[machine_index[0][0]][2].defects_count/dt.solution_list[machine_index[0][0]][2].total_tasks_assigned
    if actual_defect_ratio>0.8*dt.solution_list[machine_index[0][0]][2].defectRate:
        dt.task_to_assign.quality=True     #if enters, means that the max number of defects has been reached (defined by the desired defect rate)
        
        # ############ maintenance action #######################
        # simply set period_processing_time to zero #######################
        if dt.solution_list[machine_index[0][0]][2].corrective_maintenance_active==True:
            corrective_maintenance_exists=evm.avoid_double_corrective_maintenance(dt,dt.solution_list[machine_index[0][0]][2])
            if corrective_maintenance_exists==False:
                if dt.solution_list[machine_index[0][0]][2].period_processing_time>dt.solution_list[machine_index[0][0]][2].MTBT:
                    dt=evm.maintenance_assignment(dt,machine_index)
            
    dt.solution_list[machine_index[0][0]][2].actual_defect_ratio=actual_defect_ratio
        
    return dt

# ###########################################################################################
def save_normal_task_defect(dt):
    if dt.task_to_assign.task_type=='normal' and dt.task_to_assign.quality==False:
        if dt.task_to_assign.inspection_after==True:
            dt.detected_defects_Master.append(copy.deepcopy(dt.task_to_assign))
            dt.detected_defects.append(copy.deepcopy(dt.task_to_assign))
        else:
            dt.non_detected_defects.append(copy.deepcopy(dt.task_to_assign))
            
    return dt


# ###########################################################################################
# defect prediction method. THis method will work as follows:
    # run the same code as the defects generation. If there are left tasks to assign to the current machine
    # then it calculates the defect_n and if it is >1 then a defect will occure at the near future
def defect_prediction(dt,machine_index):
    if dt.solution_list[machine_index[0][0]][2].prediction_active==True:   #if true prediction is happening
        prediction_exesits=evm.avoid_double_predictions(dt,dt.solution_list[machine_index[0][0]][2])
        if prediction_exesits==False: #this if will make sure that there is only one prediction at each time for each machine
            pt_sum=0    
            for tsk in dt.solution_list[machine_index[0][0]][2].assigned_tasks_list:
                m_pt=[x for x in tsk.machine_pt if x[0]==dt.solution_list[machine_index[0][0]][2].name]
                pt_sum+=m_pt[0][2]
                if pt_sum<dt.solution_list[machine_index[0][0]][2].prediction_horizon: #if a defect is generated after the prediction horizon then do not enter, because it is out of the prediciton method capabilities
                    if dt.solution_list[machine_index[0][0]][2].defect_profile==0: # for exponential defects generation
                        cof=defect_distribution_data(dt,machine_index)
                        defect_n=math.exp((10*(pt_sum+cof[2])/cof[1])-cof[0])
                    
                    elif dt.solution_list[machine_index[0][0]][2].defect_profile==1: # for linear defects generation
                         cof=defect_distribution_data(dt,machine_index)
                         defect_n=cof[0]*(pt_sum+cof[2])
                     
                    if int(defect_n-dt.solution_list[machine_index[0][0]][2].previous_defect_n)>1:
                        prob=random.random() #probability for accurate defect prediction
                        if prob<dt.solution_list[machine_index[0][0]][2].prediction_repetability: #if true the defect prediction is successful
                            prediction_time= dt.task_to_assign.makespan-(dt.solution_list[machine_index[0][0]][2].prediction_horizon-pt_sum)
                            predicted_time_of_the_defect=prediction_time+dt.solution_list[machine_index[0][0]][2].prediction_horizon
                            
                            dt=evm.prediction_event_generation(dt,prediction_time,machine_index,predicted_time_of_the_defect,dt.solution_list[machine_index[0][0]][2])
                            break
                else:
                    break
                    
    return dt

  






