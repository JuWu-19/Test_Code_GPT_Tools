# -*- coding: utf-8 -*-
"""
Created on Wed Jan  6 07:52:04 2021

@author: Foivos_Surface
"""
import kpi_calculation
import data_loading as dl
import random
import copy
import uuid 
import numpy as np
import data_results_integrity as dri

# ######################################################################################################
# events class
class event_class:
    def __init__(self, event_type,event_time,event_object,responce_time,responce_delay,settings):
        self.event_type=event_type
        self.event_time=event_time
        self.event_object=event_object
        self.responce_time=None
        self.responce_delay=None
        self.processed=False
        self.actions_assigned=[]
    
        # def responce_time_correction(self,event_time,responce_time,settings):
        event_responce_time=event_time+responce_time
        day=int(event_time/settings.minutes_per_day) # 1440 is the nuber of minutes per day
        upper_limit=(day*settings.minutes_per_day)+(settings.number_of_shifts*60)
        dif=upper_limit - event_responce_time
        if dif>0: # this means that the event action is ready before the end of the current working day
            self.responce_time=event_responce_time
        else:
            if event_time>=upper_limit: # if the event time is greater than the working hours of the current day
                self.responce_time=(day+1)*settings.minutes_per_day+responce_time # set the responce time next day + the responce time
            else:
                self.responce_time=(day+1)*settings.minutes_per_day+responce_time-(upper_limit-event_time) # calculate the remaining responce time the corresponds to the next working day

                
        # def delay_responce_time_correction(self,responce_delay,settings):
        event_delay_responce_time=self.responce_time+responce_delay
        day=int(self.responce_time/settings.minutes_per_day) # 1440 is the nuber of minutes per day
        upper_limit=(day*settings.minutes_per_day)+(settings.number_of_shifts*60)
        dif=upper_limit-(event_delay_responce_time)
        if dif>0: # this means that the event action is ready before the end of the current working day
            self.responce_delay=event_delay_responce_time
        else:
            if self.responce_time>=upper_limit: # if the event time is greater than the working hours of the current day
                self.responce_delay=(day+1)*settings.minutes_per_day+responce_delay # set the responce time next day + the responce time
            else:
                self.responce_delay=(day+1)*settings.minutes_per_day+responce_delay-(upper_limit-self.responce_time) # calculate the remaining responce time the corresponds to the next working day
# ############################################################################################## 
class maintenance_class:
    def __init__(self,maintenance_id,task_type,machine_pt,processing_time,prevention_sucessful,machine_improovment,maintenace_reason):
        id = uuid.uuid1()
        self.unique_id=id.int # a unique identifier for the specific task only, not the task_id which is for the product instance
        self.maintenance_id=maintenance_id
        self.task_type=task_type
        self.machine_pt=machine_pt          #is the time that required for performing the needed maintenance
        self.makespan=0
        self.processing_time=processing_time
        self.setup_time=0                   #setup time is set to 0 because maintenance does not requires setup time, but a problem will created in the makespan calculation,  if not error will occur
        self.prevention_sucessful=prevention_sucessful
        self.machine_improovment=machine_improovment
        self.starting_time=0
        self.assigned=False 
        self.defect_once=True #this is set like this in order to avoid the quality assignment function
        self.quality=True       #this is also set like this in order to avoid errors, maintenance cannot have bad quality
        self.unlock_makespan=0  #this is also set like this in order to avoid errors during the makespan calculation
        self.maintenace_reason=maintenace_reason


# ############################################################################################## 
### events managment algorithm

def events_managment(dt):
    dt=new_order_release(dt)            #investigate if to assign a new order
    
    if dt.new_event_occured==True:      # because of the if always there will be at least one event in the list
        dt=events_managment_algorithm(dt)
    
    if len(dt.events_to_assign_list)>0: #this is entered in order to filter the cases where "if dt.current_time>=dt.temp_rescheduling_time" is true but there are no events to schedule, to avoid the comparison with an old temp_scheduling value
        if dt.current_time>=dt.temp_rescheduling_time:  # if true then recheduling will be perfomred at rescheduling_time
            dt.rescheduling_time=dt.temp_rescheduling_time
            dt=events_actions(dt)       #assign the actions for each of the events to assign
            dt.past_events_with_the_rescheduling_time.append([dt.rescheduling_time,copy.deepcopy(dt.events_to_assign_list)])
            dt.events_to_assign_list.clear()  # empty the list because they have been assigned
    if len(dt.unassigned_events)>0:
        dt=events_managment_algorithm(dt)  #re run the events managment algorithm in order to calculate the remporary rescheduling time for the remaining unassinged events        

    return dt

def events_managment_algorithm(dt):
    dt.unassigned_events.extend(dt.events_to_assign_list) #if there are events in the unassigned_events, left, then some of them are placed in the events to assign, if a new event comes they need to be reconcidered
    dt.events_to_assign_list=[]
    drt_old=dt.unassigned_events[0].responce_delay      # initialize the variable with the DRT value of the first event, if zero at the begining it the min DRT value and no rescheduling is happening
    for event in dt.unassigned_events:                  # find the minimum event DRT 
        drt_new=event.responce_delay
        if drt_new<=drt_old:
            drt_old=drt_new                             # drt_old is the minimum DRT
    for event in dt.unassigned_events:                  #compare the minimum event DRT with the event's responce time
        if event.responce_time<=drt_old:                # if true then add the event to the list with events to assign
            dt.events_to_assign_list.append(event)
    for event_to_delete in  dt.events_to_assign_list:   #delete the events to assign from the unassigned_events list
        dt.unassigned_events.remove(event_to_delete)
    rt_old=0
    for event in dt.events_to_assign_list:      #from the events to assign find the max event responce time
        rt_new=event.responce_time
        if rt_new>=rt_old:
           rt_old= rt_new
    dt.temp_rescheduling_time=rt_old+dt.rescheduling_preparation_time   # set the temporary rescheduling time
    dt.new_event_occured=False # set the value to false until a new event occurs
    
    return dt

# ############################################################################################## 
### events actions allocation, for scheduling the new events from the vents managment algorithm
def events_actions(dt):
    for event in dt.events_to_assign_list:
        if event.event_type=='order':
            dt=order_assignment(dt,event.event_object[0])
        elif event.event_type=='defect' and event.processed==False: #dd= defect detection
            dt=defect_actions(dt,event)
        elif event.event_type=='prediction': #dp = defect prediction
            dt=defect_prediction_action(dt, event)
        elif event.event_type=='corrective_maintenance':
            dt=corrective_maintenance_action(dt, event)
        elif event.event_type=='defect_detection':
            dt=detection_prevention_action(dt,event)
            
            
    return dt


# ############################################################################################## 
### main scheduling events initialization
# select the first order 
def events_initialization(dt):
    dt=order_assignment(dt,dt.orders_list[0])
    order=dt.orders_list[0]
    dt.orders_list.remove(order)                # remove the order from the orders_list 
    dt.rescheduling_time=dt.assigned_orders[0].responce_time + dt.rescheduling_preparation_time

    return dt


# ##############################################################################################
# function for releasing new orders
def new_order_release(dt):
    for order in dt.orders_list:
        if dt.current_time>=order.arrival_date:
            tmp=event_class('order',
                        order.arrival_date,
                        [order],
                        order.responce_time,
                        140,
                        dt.settings)
            dt.unassigned_events.append(tmp)
            dt.new_event_occured=True
            dt.orders_list.remove(order)                # remove the order from the orders_list 
        else:
            break # break the for loop in the case of not compling becuse for sure next order will not comply as well
            
    return dt
            
    
# ##############################################################################################
### function for performing all the steps for assigning an order    
def order_assignment(dt,order):                 # order is the order object
    dt.assigned_orders.append(order)            # add the order to the assigned_orders list
    dt.orders.extend(order.tasks_to_make)
    
    
    orders_kpi_list=kpi_calculation.kpi_order_instance_creation(order.tasks_to_make)
    dt.orders_kpi_list.append(orders_kpi_list[0])
    
    dt.batch_data=dl.batch_tasks_number(order.tasks_to_make[0],dt.batch_data)
    
    temp=dl.bottom_tasks_group(order.tasks_to_make)
    order.tasks_to_make=temp[0]
    dt.assignable_tasks_total.extend(temp[1])
    tasks_allocation_to_machines(dt.machines,temp[1][0])          #assign the bottom tasks to the corresponding machines
    return dt
    
# ##############################################################################################
### function for creating the defect event for the events managment algorithm, in the event of a defected part
def defect_scheduling_event_generation(dt):
    if dt.task_to_assign.defect_detected==True: # at this stage task_to_assign is the inspection task
        if dt.task_to_assign.defect_once==False:
            dt.task_to_assign.defect.defect_once=True   #the defected task 
            dt.task_to_assign.defect_once=True          #the inspection task
            tmp=event_class('defect',
                            dt.task_to_assign.makespan,
                            [dt.task_to_assign], # as object is given the task_to_assign (the inspection task) because it also contains the defected task
                            150,    #it is an arbitrary choice, late will be calculated or retrieved by the excel
                            140,
                            dt.settings)
            dt.unassigned_events.append(tmp)
            dt.new_event_occured=True
        else:
            print('error in defect_scheduling_event_generation')
    return tmp #return the event

# ##############################################################################################
### function for assigning the actions in the event of a defect, two options, assing the repairing task and adding a new product






# ##############################################################################################
### DSS for deciding whether to repair or discard the part
def defect_actions(dt,current_event):
        
    order_temp=[x for x in dt.orders if x[0]==current_event.event_object[0].order]
    current_product=[x for x in dt.product_list if x.name==current_event.event_object[0].product]
    try:
        assignable_tasks_total_current=[x for x in dt.assignable_tasks_total if x[0].order==current_event.event_object[0].order]
    except:
        assignable_tasks_total_current=[]
        
    all_task_id_instances=[x for x in order_temp[0][1] if x.task_id==current_event.event_object[0].task_id ] # and x.task_type!='repair'
    
    if current_event.event_object[0].defect.defect_can_be_repaired==True:
        repairable_task_action(current_product,current_event,all_task_id_instances,order_temp,assignable_tasks_total_current,dt)
        
    else:           # if enters the else then the part is NOT repairable
        non_repairable_task_action(current_event,all_task_id_instances,current_product,assignable_tasks_total_current,dt)
    
    unlock_on_hold_off(current_event.event_object[0],order_temp,dt)
    current_event.processed=True    
    return dt

# #######################################################################################
def repairable_task_action(current_product,current_event,all_task_id_instances,order_temp,assignable_tasks_total_current,dt):
    total_repairing_tasks=current_product[0].tasks_to_assign_repairing
    repairng_task_set=find_repairng_task_set(total_repairing_tasks,current_event) #find the correct set of reparing tasks to work with 
    current_defect_repairing_tasks_copy=copy.deepcopy(repairng_task_set)
    
    current_defect_repairing_tasks_copy=change_id_order_to_repairing_tasks(current_defect_repairing_tasks_copy,current_event)
    top_level_repairing_task=find_top_repairing_level(current_defect_repairing_tasks_copy)       
    
    top_level_repairing_task.unlock_task=copy.deepcopy(current_event.event_object[0].unlock_task)
    unlock_task=[x for x in all_task_id_instances if x.name==current_event.event_object[0].unlock_task]
    if len(unlock_task)!=0:
        unlock_task[0].task_dependencies.append(top_level_repairing_task.name)
    
        for tsk in current_event.event_object[0].unlock_dependent_tasks: # correct the unlock_dependent_tasks for all the unlock_dependent_tasks of the defected task
            obj=[x for x in all_task_id_instances if x.name==tsk]
            obj[0].unlock_dependent_tasks.append(top_level_repairing_task.name)
    
    bottom_task_objects=find_bottom_task_objects(current_event.event_object[0].defect.repairing_bottom_tasks,current_defect_repairing_tasks_copy,current_event)
    
    for bot_task in bottom_task_objects:
        bot_task.task_dependencies=None # temporary for not entering the buffers functions
    
    current_event.actions_assigned.extend(current_defect_repairing_tasks_copy)
    dt=assign_bottom_tasks(bottom_task_objects,assignable_tasks_total_current,dt)  #add the bottom tasks to the assignable total list, in order to be available to be assinged and to continue the process  
    order_temp[0][1].extend(current_defect_repairing_tasks_copy)                #add all the repairing tasks to the corresponding orders list
    tasks_allocation_to_machines(dt.machines,bottom_task_objects)          #assign the bottom tasks to the corresponding machines


# #######################################################################################

def non_repairable_task_action(current_event,all_task_id_instances,current_product,assignable_tasks_total_current,dt):
    tasks_to_replace_names=current_event.event_object[0].defect.total_tasks_to_assign_non_reparable
    all_task_id_instances=fix_task_structure_non_repairable(all_task_id_instances,current_product,tasks_to_replace_names)
    bottom_task_names=copy.deepcopy(current_event.event_object[0].defect.bottom_tasks_non_repairable)
    tasks_to_replace_object=[]
    for replacment_tasks in tasks_to_replace_names:
        task_to_check=[x for x in all_task_id_instances if x.name==replacment_tasks]
        id = uuid.uuid1()
        task_to_check[0].unique_id=id.int
        task_to_check[0].assigned=False
        task_to_check[0].unlocked=False
        task_to_check[0].makespan=None
        task_to_check[0].unlock_makespan_list=[0]
        task_to_check[0].starting_time=0
        task_to_check[0].unlock_makespan=0
        task_to_check[0].quality=True
        task_to_check[0].defect_detected=False
        task_to_check[0].defect=None
        task_to_check[0].replaced=True # this variable if for assuring that the task will be defected only once and not over and over
        
        tasks_to_replace_object.append(task_to_check[0])
    
    current_event.actions_assigned.extend(tasks_to_replace_object)
    bottom_task_objects=[]
    for bottom_tsk in bottom_task_names:
        task_to_check=[x for x in all_task_id_instances if x.name==bottom_tsk]
        task_to_check[0].unlocked=True             #it is the bottom level, threfore there is no need for unlocking
        bottom_task_objects.append(task_to_check[0])
        
    dt=assign_bottom_tasks(bottom_task_objects,assignable_tasks_total_current,dt) 
    tasks_allocation_to_machines(dt.machines,bottom_task_objects) #assign the bottom tasks to the corresponding machines
# #######################################################################################
def assign_bottom_tasks(bottom_task_objects,assignable_tasks_total_current,dt):
    if len(assignable_tasks_total_current)>0:
        assignable_tasks_total_current[0].extend(bottom_task_objects)
    else:
        dt.assignable_tasks_total.append(bottom_task_objects) # if there are no tasks left for an order but a defect occurs
    return dt

# #######################################################################################
def find_bottom_task_objects(defect_bottom_tasks,total_action_tasks,current_event):
    bottom_task_objects=[]
    for tsk in defect_bottom_tasks:                     # for each of the bottom repairing tasks
        for tsk_r in total_action_tasks:                                # for each of the total repairng tasks
            if tsk_r.name==tsk:
                tsk_r.unlocked=True
                tsk_r.unlock_makespan=current_event.event_object[0].makespan
                tsk_r.unlock_makespan_list.append(current_event.event_object[0].makespan)
                bottom_task_objects.append(tsk_r)
    return bottom_task_objects

# #######################################################################################
def find_repairng_task_set(total_repairing_tasks_copy,current_event):
    for temp_list in total_repairing_tasks_copy: # for finding which set of task are corresponding to the current defect
        for tsk_t in temp_list:
            if tsk_t.name==current_event.event_object[0].defect.repairing_bottom_tasks[0]:
                break
        else:
            continue
        break
    return temp_list


# #######################################################################################
def change_id_order_to_repairing_tasks(current_defect_repairing_tasks_copy,current_event):
    
    for tsk in current_defect_repairing_tasks_copy:          #replace the ID and the order name with the current values
        tsk.task_id=current_event.event_object[0].task_id
        tsk.order=current_event.event_object[0].order
        id = uuid.uuid1()
        tsk.unique_id=id.int
        
    return current_defect_repairing_tasks_copy


# #######################################################################################
def find_top_repairing_level(current_defect_repairing_tasks_copy):
    for tsk in current_defect_repairing_tasks_copy: 
        old_level=current_defect_repairing_tasks_copy[0].level
        new_level=tsk.level
        if new_level<=old_level:
            old_level=new_level
            top_level_repairing_task=tsk    #this is the top level of the repairing tasks, it is need it becasue we need to add the task dependencies and the unlock makespans
        
    return top_level_repairing_task


# ######################################################################################
# in the event that a product that had repaird at previous step is defected and non repairable. The task dependencies must be changed back to the original values
def fix_task_structure_non_repairable(all_task_id_instances,current_product,tasks_to_replace_names):
    fix_needed=False
    for tsk in all_task_id_instances:
        if tsk.task_type=='repair':
            fix_needed=True
            break
    
    if fix_needed==True:
        for tsk in tasks_to_replace_names:
            id_task=[x for x in all_task_id_instances if x.name==tsk]
            dummy_task=[x for x in current_product[0].dummy_scheduling_tasks if x.name==id_task[0].name]
            id_task[0].task_dependencies=copy.deepcopy(dummy_task[0].task_dependencies)
    return all_task_id_instances        
    
# ######################################################################################
#    
def defect_repairability_assignment(inspection_task,dt):    
    
    # inspection_task.defect.defect_can_be_repaired=True
    
    if inspection_task.defect.repairable==True:
    
        if dt.settings.defect_future_policy==0: # random
            rand_val=random.random()
            rand_val < inspection_task.defect.probability_to_be_reparable
            
            if rand_val < inspection_task.defect.probability_to_be_reparable: #if true then the part is repairable
                inspection_task.defect.defect_can_be_repaired=True #repairable
                inspection_task.defect_can_be_repaired=True #repairable
            else:
                inspection_task.defect.defect_can_be_repaired=False #non repairable
                inspection_task.defect_can_be_repaired=False #non repairable
       
        elif dt.settings.defect_future_policy==1: #DSS
            print('to be made')
    else: 
        inspection_task.defect.defect_can_be_repaired=False #non repairable 
        inspection_task.defect_can_be_repaired=False #non repairable  

# ######################################################################################
# #for stopping the unlocking when the defect event is released after the completion of all the initial unlock dependent tasks
def unlock_on_hold(any_unlock_dependant_task,order_task_list):
    all_id_tasks=[x for x in order_task_list[0][1] if x.task_id==any_unlock_dependant_task.task_id]
    if any_unlock_dependant_task.unlock_dependent_tasks!=None and len(any_unlock_dependant_task.unlock_dependent_tasks)>0:
        unlock_task=[x for x in all_id_tasks if x.name==any_unlock_dependant_task.unlock_task]
        
        for tsk in unlock_task[0].task_dependencies:
            temp=[x for x in all_id_tasks if x.name==tsk]
            temp[0].unlock_task_on_hold=True       
             
def unlock_on_hold_off(any_unlock_dependant_task,order_task_list,dt): #any_unlock_dependant_task=current event object
    tem_events_list=[]
    tem_events_list.extend(dt.events_to_assign_list)
    tem_events_list.extend(dt.unassigned_events)
    
    all_id_tasks=[x for x in order_task_list[0][1] if x.task_id==any_unlock_dependant_task.task_id]
    if any_unlock_dependant_task.unlock_dependent_tasks!=None and len(any_unlock_dependant_task.unlock_dependent_tasks)>0:
        unlock_task=[x for x in all_id_tasks if x.name==any_unlock_dependant_task.unlock_task]
        
        for tsk in unlock_task[0].task_dependencies:
            if tsk!=any_unlock_dependant_task.name: #this if is for skipping the current event, in order to check if there are others than the current one
                unlock_stil_off=events_check_to_correct_unlock_on_hold_off(tem_events_list,tsk,any_unlock_dependant_task.task_id) #check if there are pending events of the same unlocking process, if there are the tool will wait until all actions are released before turn of the unlock hold on
                if unlock_stil_off==True: #annother event exists
                    break
                else:
                    unlock_stil_off=False
        
        if unlock_stil_off==False:
            for tsk in unlock_task[0].task_dependencies:
                temp=[x for x in all_id_tasks if x.name==tsk]
                temp[0].unlock_task_on_hold=False  

def events_check_to_correct_unlock_on_hold_off(tem_events_list,unlock_dependent_task,task_id):
    for event in tem_events_list:
        if event.event_type=='defect':
            if event.event_object[0].name==unlock_dependent_task and event.event_object[0].task_id==task_id and event.processed==False: #in some cases where a product is defected on multiple tasks and therefore many events of the same task_id exists event.processed==False is used in order to filter the events and turn of the unlock hold on 
                unlock_stil_off=True
                break
            else:
                unlock_stil_off=False
    return unlock_stil_off
    

# ######################################################################################
# function for allocating the assigned tasks to the coresponding machine object in order to keep track on whcih tasks have been assinge dto each machine
def tasks_allocation_to_machines(machines_list,tasks): # tasks should be a list in the following form [tsk,tsk,tsk], the size of the list should be equal to the number of tasks
    for tsk in tasks:
        for m in tsk.machine_pt:
            machine_object_temp=[x for x in machines_list if x.name==m[0]] #find the machine object
            machine_object_temp[0].assigned_tasks_list.append(tsk)


# ######################################################################################
# function for deleting from all the capable machines the assinged task
def delete_assiged_task_from_machines(machines_list,task):
    try:
        for m in task.machine_pt:
            machine_object_temp=[x for x in machines_list if x.name==m[0]] #find the machine object
            machine_object_temp[0].assigned_tasks_list.remove(task)
    except:
        print("task not in machines list")
        
# ######################################################################################
# function for creating the prediction event        
def prediction_event_generation(dt,prediction_time,machine_index,predicted_time_of_the_defect,machine_object):
    prediction_DRT=predicted_time_of_the_defect-(dt.solution_list[machine_index[0][0]][2].prediction_RT*0.05)-prediction_time-dt.solution_list[machine_index[0][0]][2].prediction_RT # subtract 5% from the dt.solution_list[machine_index[0][0]][2].prediction_RT in order the event to be scheduled before the time of the defect 
    if prediction_DRT<0:
        prediction_DRT=0
    tmp=event_class('prediction',
                    prediction_time,
                    machine_object, # as object is given the machine that prediction was happned
                    dt.solution_list[machine_index[0][0]][2].prediction_RT,    #it is an arbitrary choice, late will be calculated or retrieved by the excel
                    prediction_DRT,
                    dt.settings)
    dt.unassigned_events.append(tmp)
    dt.new_event_occured=True
    return dt

# ######################################################################################
# function for creating the action for preventing the defect generation when there is prediction of a defect
def defect_prediction_action(dt, current_event):
    prob=random.random()
    machine_improovment_temp=np.random.normal(current_event.event_object.prevention_machine_impovment,current_event.event_object.prevention_machine_impovment/3,1)
    if prob<current_event.event_object.prediction_accuracy:
        prevention_success=True
        machine_improovment=machine_improovment_temp[0]
    elif prob<current_event.event_object.prediction_accuracy*0.2: #
        prevention_success=True
        machine_improovment=machine_improovment_temp[0]*0.2 #20% of the normal machine improvment, because the prediction algorith did not identified correctly the source of the problem. The small maintenanace will have some positive impact to the machine but not the total
    else:
        prevention_success=False
        machine_improovment=0

    dt.maintenance_counter+=1
    prevention_time_temp=np.random.normal(current_event.event_object.prevention_time, current_event.event_object.prevention_time/3, 1)
    temp=maintenance_class(dt.maintenance_counter,
                           'maintenance',
                           [current_event.event_object.name],
                           prevention_time_temp[0],
                           prevention_success,
                           machine_improovment,
                           'prediction')
    dt.assignable_maintenance_tasks.append(temp)
    return dt
    

# ######################################################################################
# function  for checking all the assigned and unassigned events in order to check whether there is an event for the current machine, if there is then not prediction will happen. The maintenance of the existing predciton will change the future  
def avoid_double_predictions(dt,machine_object):
    prediction_exists=False
    temp_events_list=[]
    temp_events_list.extend(dt.events_to_assign_list)
    temp_events_list.extend(dt.unassigned_events)
    for event in temp_events_list:
        if event.event_type=='prediction':
            if event.event_object.name==machine_object.name:
                prediction_exists=True
                break
    return prediction_exists
                
# ######################################################################################
# function  for assinging regular maintenance
def maintenance_assignment(dt,machine_index):           
    maintenance_DRT=60
    tmp=event_class('corrective_maintenance',
                    dt.task_to_assign.makespan,
                    dt.solution_list[machine_index[0][0]][2], # as object is given the machine that prediction was happned
                    dt.solution_list[machine_index[0][0]][2].corrective_maintenance_RT,    #it is an arbitrary choice, late will be calculated or retrieved by the excel
                    maintenance_DRT,
                    dt.settings)
    dt.unassigned_events.append(tmp)
    dt.new_event_occured=True
    return dt

# ######################################################################################
# function  for creating the correction action for corrective maintenance
def corrective_maintenance_action(dt, current_event):
    machine_improovment=2 # I put 2 in order to make sure that period_processing_time will be 0
    corrective_maintenance_time_required=np.random.normal(current_event.event_object.corrective_maintenance_time_required, current_event.event_object.corrective_maintenance_time_required/3, 1)
    temp=maintenance_class(dt.maintenance_counter,
                           'maintenance',
                           [current_event.event_object.name],
                           corrective_maintenance_time_required[0],
                           True,
                           machine_improovment,
                           'corrective_maintenance')
    dt.assignable_maintenance_tasks.append(temp)
    return dt
# ######################################################################################
def avoid_double_corrective_maintenance(dt,machine_object):
    corrective_maintenance_exists=False
    temp_events_list=[]
    temp_events_list.extend(dt.events_to_assign_list)
    temp_events_list.extend(dt.unassigned_events)
    for event in temp_events_list:
        if event.event_type=='corrective_maintenance':
            if event.event_object.name==machine_object.name:
                corrective_maintenance_exists=True
                break
    return corrective_maintenance_exists
    
    
# ###########################################################################################
# Detection - prevention, this function will generate the event that prevention is required after a detection of a defect
def detection_prevention_event(dt,task):
    machine_index=[x for x in list(enumerate(dt.solution_list)) if x[1][0]==task.defect.machine_assigned]  #find the index of the machine in the solution list, the machine that generated the defect, not the inspection machine 
    if dt.solution_list[machine_index[0][0]][2].detection_prevention_active==True:
        
        prob=random.random()+0.01*dt.solution_list[machine_index[0][0]][2].period_dedects
    
        if prob>dt.solution_list[machine_index[0][0]][2].detection_prevention_accuracy:
            tmp=event_class('defect_detection',
                    task.makespan,
                    dt.solution_list[machine_index[0][0]][2], # as object is given the machine that produced the defected part
                    dt.solution_list[machine_index[0][0]][2].detection_prevention_RT,    #it is an arbitrary choice, late will be calculated or retrieved by the excel
                    35,
                    dt.settings)
            dt.unassigned_events.append(tmp)
            dt.new_event_occured=True
    return dt
        
# ###########################################################################################
# Detection - prevention action 
def detection_prevention_action(dt,current_event):
    prob=random.random()        
    machine_improovment_temp=np.random.normal(current_event.event_object.detection_prevention_machine_impovment,current_event.event_object.detection_prevention_machine_impovment/3,1)
    if prob<current_event.event_object.detection_prevention_accuracy:
        prevention_success=True
        machine_improovment=machine_improovment_temp[0]
    elif prob<current_event.event_object.detection_prevention_accuracy*0.2:
        prevention_success=True
        machine_improovment=machine_improovment_temp[0]*0.2 #20% of the normal machine improvment, because the prediction algorith did not identified correctly the source of the problem. The small maintenanace will have some positive impact to the machine but not the total
    else:
        prevention_success=False
        machine_improovment=0
    prevention_time_temp=np.random.normal(current_event.event_object.detection_prevention_prevention_time_required, current_event.event_object.detection_prevention_prevention_time_required/3, 1)    
    temp=maintenance_class(dt.maintenance_counter,
                           'maintenance',
                           [current_event.event_object.name],
                           prevention_time_temp[0],
                           prevention_success,
                           machine_improovment,
                           'dection_prevention')
    dt.assignable_maintenance_tasks.append(temp)
    
    return dt
    
# ######################################################################################
def avoid_double_detection_prevention_maintenance(dt,machine_object):
    detection_prevention_maintenance_exists=False
    temp_events_list=[]
    temp_events_list.extend(dt.events_to_assign_list)
    temp_events_list.extend(dt.unassigned_events)
    for event in temp_events_list:
        if event.event_type=='defect_detection':
            if event.event_object.name==machine_object.name:
                detection_prevention_maintenance_exists=True
                break
    return detection_prevention_maintenance_exists    
