# -*- coding: utf-8 -*-
"""
Created on Sun Dec  6 15:46:49 2020
 
Module for createing the task objects for each new order.

An order contains which products has and at what qualtity

Also the scheduling class will be defined here

@author: foivo
"""
import random
import kpi_calculation
import events_managment as evm
import defect_generation as defe
import copy
import uuid 
import heuristic_rules as hr




class scheduling_task:
    def __init__(self, task_id, task_type, name, level, order, unlock_task,unlock_dependent_tasks,task_dependencies,product,machine_pt,capable_machine_objects,raw_material,scrap_cost,repairable,batch_spaces,buffer_spaces,inspection_after,bottom_tasks_non_repairable,repairing_bottom_tasks,probability_to_be_reparable,total_tasks_to_assign_non_reparable):
        id = uuid.uuid1()
        self.unique_id=id.int # a unique identifier for the specific task only, not the task_id which is for the product instance
        self.task_id=task_id                                #unique number showing the product ID that is also task ID. All the tasks of the same product have the same ID
        self.task_type=task_type                            #type, "normal", "repairing", "inspection"
        self.name=name                                      #task name
        self.level=level
        self.order=order
        self.assigned=False                                    #bolean value true=is assiged, false=not assigned
        self.unlocked=False
        self.unlock_task=unlock_task                        #the name of the task to be unlocked if preconditions are met
        self.unlock_dependent_tasks=unlock_dependent_tasks  # the tasks that are required for unlocking the "unlock_task"
        self.task_dependencies=task_dependencies
        self.product=product
        self.machine_pt=machine_pt
        self.capable_machine_objects=capable_machine_objects                    #this list will hold the machine objects that can perform the current task
        self.raw_material=raw_material
        self.scrap_cost=scrap_cost
        self.repairable=repairable
        self.machine_assigned=None
        self.machine_assigned_object=None
        self.processing_time=None
        self.setup_time=0
        self.makespan=None
        self.starting_time=0
        self.unlock_makespan=0 #is the makespan that the last dependant task was finished
        self.unlock_makespan_list=[0]
        self.batch_spaces=batch_spaces
        self.buffer_spaces=buffer_spaces
        self.quality=True
        self.defect_detected=False
        self.defect=None
        self.inspection_after=inspection_after
        self.bottom_tasks_non_repairable=bottom_tasks_non_repairable
        self.total_tasks_to_assign_non_reparable=total_tasks_to_assign_non_reparable
        self.repairing_bottom_tasks=repairing_bottom_tasks
        self.probability_to_be_reparable=probability_to_be_reparable
        self.replaced=False
        self.defect_can_be_repaired=None
        self.defect_once=False 
        self.unlock_task_on_hold=False #for stopping the unlocking when the defect event is released after the completion of all the initial unlock dependent tasks
        self.event=None
        
        
# ######################################################################################################
#class for describing batch process
class scheduling_task_batch:
    def __init__(self,task_type,task_id_batch,machine_pt,included_tasks,ready=False):
        self.task_type=task_type
        self.task_id_batch=task_id_batch
        self.machine_pt=machine_pt
        self.included_tasks=included_tasks
        self.ready=ready #this is an attribute for checking whether the batch task is ready for assignment
        self.machine_assigned=None
        self.processing_time=None
        self.setup_time=0
        self.makespan=None
        self.starting_time=0
        self.unlock_makespan=None #is the makespan that the last dependant task was finished
        self.remaining_batch_ind_tasks=None #this value shows how many spaces left at the current batch_ind process
        


        
    
# ######################################################################################################
#formalise the tasks dependencies for each task, extract the information from the task_dependencies_list
def find_dependencies(task,task_dependences):
    
    
    topLevel=None
    for check_list in task_dependences:
        if task in check_list[1]:
            unlock_task=check_list[0]
            check_list[1].remove(task)
            udt=check_list[1].copy()
            unlock_dependent_tasks= udt
            check_list[1].append(task)
            topLevel=False
            break
        else:
            topLevel=True
            
        
    temp_list=[x for x in task_dependences if x[0]==task]

    if temp_list[0][1][0]!='-' and topLevel==False: #midle level
        task_dependencies=temp_list[0][1]
        
    elif temp_list[0][1][0]=='-' and topLevel==False: #bottom level
        task_dependencies=None
        
    elif topLevel==True:
        unlock_task=None            # for top levels
        unlock_dependent_tasks=None
        task_dependencies=temp_list[0][1]
        
        
    return unlock_task,unlock_dependent_tasks,task_dependencies
            
# ####################################################################################################################
# extracting the tasks from order
def task_extraction_from_order(order_spec,task_dependences,product_counter,tasks_list):
    tasks_to_schedule=[]
    for prod in range(len(order_spec.products_involved)):
        quantity=order_spec.products_involved[prod][1]
        tasks=[x[0:4] for x in order_spec.products_involved[prod][0].tasks if x[3]!="repair"]
        for i in range(quantity):
            product_counter+=1
            for task in tasks:
                task_machines= [x for x in tasks_list if x.name==task[1]]
                task_dep_temp=find_dependencies(task[1],task_dependences)
                temp=scheduling_task(copy.deepcopy(product_counter),       #id
                                     copy.deepcopy(task[3]),               #type
                                     copy.deepcopy(task[1]),               #name
                                     copy.deepcopy(task[2]),               #level
                                     copy.deepcopy(order_spec.name),       #order
                                     copy.deepcopy(task_dep_temp[0]),      #unlock_task
                                     copy.deepcopy(task_dep_temp[1]),      #unlock_dependent_tasks
                                     copy.deepcopy(task_dep_temp[2]),      #task_dependencies
                                     task[0],               #product name
                                     task_machines[0].processingTime,
                                     task_machines[0].capable_machines_objects,
                                     task_machines[0].rawMaterial,
                                     task_machines[0].scrapCost,
                                     task_machines[0].reparable,
                                     task_machines[0].batch_spaces,
                                     task_machines[0].buffer_spaces,
                                     task_machines[0].inspection_after,
                                     copy.deepcopy(task_machines[0].bottom_tasks_non_repairable),
                                     copy.deepcopy(task_machines[0].repairing_bottom_tasks),
                                     copy.deepcopy(task_machines[0].probability_to_be_reparable),
                                     copy.deepcopy(task_machines[0].total_tasks_to_assign_non_reparable))
                tasks_to_schedule.append(temp)
    batch_tasks_to_schedule=[]
    for task in tasks_to_schedule:
        if task.task_type=="batch_all" or task.task_type=="batch_ind":
            # tasks_to_schedule.remove(task)
            batch_tasks_to_schedule.append(task)
    
    return tasks_to_schedule,batch_tasks_to_schedule, product_counter
    
# ######################################################################################################################
# function for scheduling, heuristic rules

    # function for finding the bottom tasks in order to assign them first
def find_bottom_tasks(orders,task_type_num):              # orders should be at ['Ox',[scheduling tasks]] format
    init_scheduling_task_list=[]
    for order in orders:
        temp=[x for x in order[task_type_num] if x.task_dependencies is None]
        init_scheduling_task_list.append(temp)
    for task_adj in init_scheduling_task_list[0]:      #for loop for adjusting the values in the bottom level tasks
        temp= [x for x in list(enumerate(orders[0][task_type_num])) if x[1].name==task_adj.name and x[1].task_id==task_adj.task_id] #find the index of the current task
        order_index=[x for x in list(enumerate(orders)) if x[1][0]==task_adj.order]                                     #find the index of the current order
        orders[order_index[0][0]][task_type_num][temp[0][0]].unlocked=True
        
            
    return init_scheduling_task_list,orders

# ###################################################################################################################
# function for finding and assgning the unlocked task or to edit the "unlock_dependent_tasks"
def unlock_tasks(task,dt):      # it is task and not dt...... because of batch processes
    current_order=[x for x in dt.orders if x[0]==task.order]                    #find the order list that the current task is 
    all_id_tasks=[x for x in current_order[0][1] if x.task_id==task.task_id]    #find all the tasks that have the same id with the current task
    unlock=True
    if task.unlock_task!=None and task.unlock_task_on_hold==False:                                       #this means that if true there is task to unlock
        unlock_task_object=[x for x in all_id_tasks if x.name== task.unlock_task] # find the object of the unlocking tasks
        
        for unlock_dep_task in unlock_task_object[0].task_dependencies:          #the lists holds only the names not the objects
            temp_task_to_check=[x for x in all_id_tasks if x.name== unlock_dep_task] # in the for loop, iterate among all the dependenta task to unlock in order to check if at least one is not assigned, ONLY if all assigned then the task can be unlocked
            if temp_task_to_check[0].assigned==False:
                dt.unlocked_task=None
                unlock=False
            elif temp_task_to_check[0].unlock_task_on_hold==True: # if statment True then this means that there is a pending repairing tasks that has not yet assigned
                dt.unlocked_task=None
                unlock=False
                break
            
        if unlock==True:
            for dep_task in unlock_task_object[0].task_dependencies:
                temp_task_to_check=[x for x in all_id_tasks if x.name== dep_task]
                unlock_task_object[0].unlock_makespan_list.append(temp_task_to_check[0].makespan)
            dt.unlocked_task=unlock_task_object[0]
            dt.unlocked_task.unlocked=True
            dt.unlocked_task.unlock_makespan=max(dt.unlocked_task.unlock_makespan_list)
    else:
        dt.unlocked_task=None # for top levels
    
    return dt

# #################################################################################################################
# function for removing from the assignable_tasks list the assigned task and checking if there is a task to be unlocked
def sol_assign_lists(task_to_assign,dt):
    
    task_to_assign.machine_assigned=dt.machine_to_assign[0]                 #save the selected machine
    task_to_assign.machine_assigned_object=dt.machine_to_assign_object      #save the object of the selected machine
    
    evm.delete_assiged_task_from_machines(dt.machines,task_to_assign)
    
    task_to_assign.processing_time=dt.machine_to_assign[2]  
    machine_index=[x for x in list(enumerate(dt.solution_list)) if x[1][0]==dt.machine_to_assign[0]]  #find the index of the machine in the solution list

    # #####################################################################################
    #KPIs calculation
   
    dt=kpi_calculation.makespan_calculation(dt,machine_index,task_to_assign) #makespan value is the measured makespan for the process just assigned and it is needed in saving it at the unlocked task, for faster calculations
    
      
    dt=kpi_calculation.resource_utilization(dt,machine_index,task_to_assign)
    # #####################################################################################
    
    dt.solution_list[machine_index[0][0]][1].append(copy.deepcopy(task_to_assign))
    dt.solution_list[machine_index[0][0]][2].total_tasks_assigned+=1 #increase the count by one in order to keep track of the total tasks assigned to that machine
    
    # defects prediction, it happens before the quality assignment in order to use the old previous_defect_n number, because if a defect happens then this is changing and the defect will never be defected
    dt=defe.defect_prediction(dt,machine_index) 
    
    # ### Defect generation
    dt=defe.quality_assignment(dt,machine_index)
    
        
    # #####################################################################################
   
    return dt

#   function for adding the unloacked tasks and updating the orders list with the unlocked tasks and assinged tasks concequences  
def add_unlocked_tasks(task,dt):    
    if task.defect_detected==False:
        dt=unlock_tasks(task,dt)
        
    if dt.unlocked_task!=None:
        if task.quality==False and task.inspection_after==True: # if it is defect pass to the inspection unlocked task the defect information, for saving time later
            dt.unlocked_task.defect_detected=True
            dt.unlocked_task.defect=task
        dt.assignable_tasks[0].append(dt.unlocked_task)
        evm.tasks_allocation_to_machines(dt.machines,[dt.unlocked_task])
        
        
        
    if task.defect_detected==True and task.defect_once==False:
        order_tem=[x for x in dt.orders if x[0]==task.order]
        evm.unlock_on_hold(task,order_tem) # put the corresponding tasks unlock on hold until the defect event is released to the shop floor
        evm.defect_repairability_assignment(task,dt)
        current_event=evm.defect_scheduling_event_generation(dt)                  #generate the defect event
        task.event=current_event
        detect_prevent_event_exists=evm.avoid_double_detection_prevention_maintenance(dt,task.defect.machine_assigned_object)
        if detect_prevent_event_exists==False:
            dt=evm.detection_prevention_event(dt,task) #create the event of prevention in case of defect detection

    return dt
# ##################################################################################################################
# find the max unlock makespan and apply it to all the batch processes
def find_max_unlock_makespan(group_list):
    check=0
    for tsk in group_list: # for loop for assuring that all the batch_all tasks have the same unlocking time, if not the maximum will replace it
        if tsk.unlock_makespan>check:
            check=tsk.unlock_makespan
    for tsk in group_list:
        tsk.unlock_makespan=check #replace all the values with the maximum value found
        
    return group_list,check

# ##################################################################################################################
# for batch processes set the batch process makespan as makespan for the individual tasks which are included 
def set_makespan_to_batch_included_tasks(task):
    for tsk in task.included_tasks:
        tsk.makespan=task.makespan
        tsk.starting_time=task.starting_time
    
    return task.included_tasks

# ##################################################################################################################
# function for groupping the batch processes into single scheduling_task_batch objects
#if different tasks can be performed in one batch task they must have the same processing time
def batch_process_all_group(dt):
    # dt.batch_task_to_assign=None
    
    machine_current=[x for x in dt.machines if x.name==dt.machine_to_assign[0]]
    batchSet=[x for x in machine_current[0].capacity if x[0]==machine_current[0].batch_set]
    group_list=[]
    for sub_set in batchSet[0][1]:
        batch_all_tasks=[x for x in dt.assignable_tasks[0] if x.task_type=='batch_all' and x.name==sub_set[0]]
        capacity_temp=sub_set[1]
        if len(batch_all_tasks)>capacity_temp:  #if there are more available tasks in the list than the capacity
            exit_v=0                            #variable to control the stopping point of the for
            for tsk in batch_all_tasks:
                tsk.assigned=True
                group_list.append(tsk)
                dt.assignable_tasks[0].remove(tsk)
                exit_v+=1
                dt.batch_data=correct_batch_all_count(tsk,dt.batch_data)
                if exit_v==capacity_temp: #if capacity is reached
                    break
        else:
            exit_v=0
            for tsk in batch_all_tasks:
                tsk.assigned=True
                group_list.append(tsk)
                dt.assignable_tasks[0].remove(tsk)
                exit_v+=1
                dt.batch_data=correct_batch_all_count(tsk,dt.batch_data)
            remaining=capacity_temp-exit_v
            extra_tasks=[x for x in dt.batch_data.dummy_sch_tasks if x.name==sub_set[0]]
            
            for i in range(remaining): # generate as many as the "remaining" denotes tasks for completing the capacity, they will go to the inventory later
                reamin_task=scheduling_task(None,
                                            copy.deepcopy(extra_tasks[0]).task_type,
                                            copy.deepcopy(extra_tasks[0]).name,
                                            copy.deepcopy(extra_tasks[0]).level,
                                            None,
                                            copy.deepcopy(extra_tasks[0].unlock_task),
                                            copy.deepcopy(extra_tasks[0].unlock_dependent_tasks),
                                            copy.deepcopy(extra_tasks[0].task_dependencies),
                                            extra_tasks[0].product,
                                            extra_tasks[0].machine_pt,
                                            extra_tasks[0].capable_machines_objects,
                                            extra_tasks[0].raw_material,
                                            extra_tasks[0].scrap_cost,
                                            extra_tasks[0].repairable,
                                            extra_tasks[0].batch_spaces,
                                            extra_tasks[0].buffer_spaces,
                                            extra_tasks[0].inspection_after,
                                            copy.deepcopy(extra_tasks[0].bottom_tasks_non_repairable),
                                            copy.deepcopy(extra_tasks[0].repairing_bottom_tasks),
                                            copy.deepcopy(extra_tasks[0].probability_to_be_reparable),
                                            copy.deepcopy(extra_tasks[0].total_tasks_to_assign_non_reparable))
                group_list.append(reamin_task)
        
    dt.batch_data.batch_counter+=1
    
    temp_b=find_max_unlock_makespan(group_list)
    group_list=temp_b[0]
    max_unlock_makespan=temp_b[1]
            
    dt.batch_task_to_assign=scheduling_task_batch('batch_all',
                                             dt.batch_data.batch_counter,
                                             dt.task_to_assign.machine_pt[0],
                                             group_list,
                                             True)
    dt.batch_task_to_assign.unlock_makespan=max_unlock_makespan
    return dt

# function for correcting the count for the batch tasks
def correct_batch_all_count(task,batch_data):
    batch_list=[x for x in batch_data.batch_tasks_count if x[0]==task.name]
    batch_list[0][1]-=1
    return batch_data
    
# ##############
#function for elaborating the inventory for the batch_all tasks. 
def inventory_check_batch_all(dt):
    
    assignable_batch_all_tasks=[x for x in dt.assignable_tasks if x[0].task_type=='batch_all']
    if len(dt.batch_data.inventory_batch_all_list)>0 and len(assignable_batch_all_tasks)>0:
        tasksToRemove=[]
        for task in dt.batch_data.inventory_batch_all_list:
            task_to_replace=[x for x in assignable_batch_all_tasks[0] if x.name==task.name]
            if len(task_to_replace)>0:
                task.task_id=task_to_replace[0].task_id
                task.order=task_to_replace[0].order
                tasksToRemove.append(task)
                
                dt.assignable_tasks.remove(task_to_replace[0])
                dt=add_unlocked_tasks(task,dt)
            for t in tasksToRemove:
                dt.batch_data.inventory_batch_all_list.remove(t)
                
    return dt
                
                
                
    
# ##################################################################################################################
#function for elaborating the batch_ind tasks,
#the process would be to add the tasks to a batch_ind task and when it is full then it can be assigned
#if different tasks can be performed in one batch task they must have the same processing time
def batch_process_ind_group(dt):
    dt.batch_task_to_assign=None
    check2=[x for x in dt.batch_data.batch_tasks_count if x[0]==dt.task_to_assign.name] # returns the record of how many tasks of the current type, if 1 then the current one is the last one and therfore it must enter the if and assign the batch task
    check2[0][1]=check2[0][1]-1 # adjust the count for keeping track of the tasks
    
    machine_current=[x for x in dt.machines if x.name==dt.machine_to_assign[0]]
    capacity_temp=machine_current[0].capacity
   
    if len(dt.batch_data.pending_batch_ind_tasks)>0 or check2==1:   #if there is at least one pending batch_ind task
        batch_task=[x for x in dt.batch_data.pending_batch_ind_tasks if x.machine_pt[0][0]==machine_current[0].name] #search based on the machine name
        check=batch_task[0].remaining_batch_ind_tasks-dt.task_to_assign.batch_spaces       # or check2==1 added as an exit rule, if there are no more tasks for the completion of the batch task then do it will less tasks
        batch_task[0].included_tasks.append(dt.task_to_assign)
        if check <=0 or check2[0][1]==0:                               # if the required places are filled with parts
            batch_task[0].ready=True
            batch_task[0].remaining_batch_ind_tasks=check
            dt.batch_task_to_assign=batch_task[0]
            dt.batch_data.past_batch_ind_tasks.append(batch_task[0])   #save the batch ind tasks in order to count the number of tasks and copare with the total tasks ordered in order to use it as exit point in the event that there are no enough tasks to complete all the spaces
            dt.batch_data.pending_batch_ind_tasks.remove(batch_task[0])
        else:
            batch_task[0].remaining_batch_ind_tasks=check
    else:                                           #if there is NOT at least one pending batch_ind task
        dt.batch_data.batch_counter+=1
        temp=scheduling_task_batch('batch_ind',
                                   dt.batch_data.batch_counter,
                                   dt.task_to_assign.machine_pt,
                                   [dt.task_to_assign])
        temp.remaining_batch_ind_tasks=capacity_temp-dt.task_to_assign.batch_spaces #calculate the remaing spaces
        dt.batch_data.pending_batch_ind_tasks.append(temp)
    dt.task_to_assign.assigned=True
    dt.assignable_tasks[0].remove(dt.task_to_assign)
    return dt
 
# ##################################################################################################################
# function for checking buffers current capacity and if it is maxed then do not assing the task
def buffers_capacity_check(tasks_list,dt):
    machine=[x for x in dt.machines if x.name==dt.machine_to_assign[0]]
    current_buffer=[x for x in dt.buffers_list if x.name==machine[0].output_buffer] #find the capacity of the buffer that the curremt machine 
    number_of_buffer_spaces=0
    for task in [dt.task_to_assign]:     # for is used because the function is used by the batch processes        #calculate the number of spaces that the tasks in the list will occupy to the buffer. List because of the bach processes 
        number_of_buffer_spaces+=task.buffer_spaces
        
    new_capacity=number_of_buffer_spaces+current_buffer[0].current_spaces_occupancy
    
    if new_capacity<=current_buffer[0].capacity:
        dt.buffer_full_status=False # if false the task will be assigned and therefore when the process on the machine finishes then it will be added to the selected buffer
        current_buffer[0].current_spaces_occupancy=new_capacity #set the new capacity occupancy
        current_buffer[0].current_tasks_in.extend([dt.task_to_assign])
        if current_buffer[0].max_number<new_capacity: # for keeping track of the maximum number of spaces ocupied, for desing purposes
            current_buffer[0].max_number=new_capacity
            
        if new_capacity==current_buffer[0].capacity:        #in the event that the tasks to be done makes the buffer full
            current_buffer[0].status_full=True
    else:
        dt.buffer_full_status=True
        
    return dt

# ##################################################################################################################
# function for removing the dependent tasks from the corresponding buffers
def remove_task_dependancies_from_buffers(task_list,dt):
   for task in task_list:
       if task.assigned==True:
            if task.task_dependencies!=None:    # if the task has dependencies (pre conditions)
                for dependant_task in task.task_dependencies:     # for each of dependent tasks remove it from its buffer
                    for buffer in dt.buffers_list:
                        check=[x for x in buffer.current_tasks_in if x.name==dependant_task and x.task_id==task.task_id]
                        if len(check)>0:
                            buffer.current_spaces_occupancy=buffer.current_spaces_occupancy-check[0].buffer_spaces #agjust the current occupied spaces at the corresponding buffer
                            buffer.current_tasks_in.remove(check[0])                # remove the dependant task from the buffer
                            if  buffer.current_spaces_occupancy<buffer.capacity:    # if there are spaces unocupied change the status of the buffer
                                buffer.status_full=False
                            break
   return dt

# ##################################################################################################################
def task_assignment(dt):
        # task_to_assign,machine_to_assign,machines,buffers_list,settings,solution_list,orders_kpi_list,assignable_tasks,batch_data,orders):
    if dt.task_to_assign.task_type=='normal' or dt.task_to_assign.task_type=='inspection' or dt.task_to_assign.task_type=='repair': # for normal and inspection
            # dt=buffers_capacity_check([dt.task_to_assign],dt) #check if buffer is full or not and add the new task
            # if dt.buffer_full_status==False:                  #if the buffer is not full we can assign the task to the machine and start the process
        dt.task_to_assign.assigned=True
       
        # dt=remove_task_dependancies_from_buffers([dt.task_to_assign],dt)   #remove the task dependent tasks from their corresponding buffers
        dt.assignable_tasks[0].remove(dt.task_to_assign)          #delete the selected task from the assignable_tasks list. "assignable_tasks" is a list with all the tasks that can be assinged, in other words the unlocked tasks
        
        dt=sol_assign_lists(dt.task_to_assign,dt)
        
        dt=kpi_calculation.overall_order_makespan(dt,dt.task_to_assign) #calculate the overall makespan of the order
        dt=add_unlocked_tasks(dt.task_to_assign,dt)

    # ###################################################################################################
    elif dt.task_to_assign.task_type=='batch_all':
        
        if hasattr(dt.task_to_assign, 'task_id'): # in the event of the batch process cannot be assinged at first attempt. If yes the process creates the batch process and if the buffer is not full the task is assinged
            dt=batch_process_all_group(dt)
            first_attempt=True
        else:                                   #if the buffer was full the first time then the batch process is added to the "assignable_tasks" list for future assignement
            dt.batch_task_to_assign=dt.task_to_assign
            first_attempt=False
        
        dt=buffers_capacity_check(dt.batch_task_to_assign.included_tasks,dt)   #check if buffer is full or not and add the new task

        if dt.buffer_full_status==False:                  #if the buffer is not full we can assign the task to the machine and start the process
            dt=sol_assign_lists(dt.batch_task_to_assign,dt)
            dt.batch_task_to_assign.included_tasks=set_makespan_to_batch_included_tasks(dt.batch_task_to_assign)
            if first_attempt==False:
                dt.assignable_tasks.remove(dt.batch_task_to_assign) #remove the batch task from the list in te event that it was postponed because of a full buffer
            for task_b in dt.batch_task_to_assign.included_tasks:
                if task_b.task_id != None:
                    dt=remove_task_dependancies_from_buffers(dt.batch_task_to_assign.included_tasks,dt)              #remove the task dependent tasks from their corresponding buffers
                    dt=add_unlocked_tasks(task_b,dt)
                    dt=kpi_calculation.overall_order_makespan(dt,task_b) #calculate the overall makespan of the order
                else:
                    dt.batch_data.inventory_batch_all_list.append(task_b)
        else:
            dt.assignable_tasks.append(dt.batch_task_to_assign)
     # ##############################################################################################       
    elif dt.task_to_assign.task_type=='batch_ind':
        if hasattr(dt.task_to_assign, 'task_id'): # in the event of the batch process cannot be assinged at first attempt. If yes the process creates the batch process and if the buffer is not full the task is assinged
            dt=batch_process_ind_group(dt)
            first_attempt=True
        else:
            dt.batch_task_to_assign=dt.task_to_assign
            first_attempt=False
            
        if dt.settings.batch_individual_loading_policy==0: #if the option to load each individual task when it is ready to the batch_ind machine
            dt=remove_task_dependancies_from_buffers([dt.task_to_assign],dt) 
        
        if dt.batch_task_to_assign != None:
            dt=buffers_capacity_check(dt.batch_task_to_assign.included_tasks,dt)   #check if buffer is full or not and add the new task
            
            if dt.buffer_full_status==False:
                temp_b=find_max_unlock_makespan(dt.batch_task_to_assign.included_tasks)
                dt.batch_task_to_assign.included_tasks=temp_b[0]
                max_unlock_makespan=temp_b[1]
                dt.batch_task_to_assign.unlock_makespan=max_unlock_makespan
                
                dt=sol_assign_lists(dt.batch_task_to_assign,dt)
                dt.batch_task_to_assign.included_tasks=set_makespan_to_batch_included_tasks(dt.batch_task_to_assign)
                for task_b in dt.batch_task_to_assign.included_tasks:
                    dt=add_unlocked_tasks(task_b,dt)
                    dt=kpi_calculation.overall_order_makespan(dt,task_b) #calculate the overall makespan of the order
                    if dt.settings.batch_individual_loading_policy==1: #if the option for loading all together is selelcted then, all the tasks will be removed from the correcponding buffers at once, when the batch_ind task is assigned
                        dt=remove_task_dependancies_from_buffers(dt.batch_task_to_assign.included_tasks,dt)   
            else:
                dt.assignable_tasks.append(dt.batch_task_to_assign)
        # ##############################################################################################           
    elif dt.task_to_assign.task_type=='maintenance':
        machine_index=[x for x in list(enumerate(dt.solution_list)) if x[1][0]==dt.machine_to_assign]  #find the index of the machine in the solution list
        dt=kpi_calculation.makespan_calculation(dt,machine_index,dt.task_to_assign) #makespan value is the measured makespan for the process just assigned and it is needed in saving it at the unlocked task, for faster calculations
        dt.solution_list[machine_index[0][0]][1].append(copy.deepcopy(dt.task_to_assign))
        
        #maintenance assignment to the corresponding machine
        if dt.task_to_assign.prevention_sucessful==True:
            temp=dt.solution_list[machine_index[0][0]][2].period_processing_time
            temp_new=temp-dt.task_to_assign.machine_improovment*dt.solution_list[machine_index[0][0]][2].MTBT
            if temp_new<0:
                temp_new=0
            dt.solution_list[machine_index[0][0]][2].period_processing_time=temp_new
        
        
        dt.assignable_maintenance_tasks.remove(dt.task_to_assign) #remove it from the list
        dt.maintenance_past_tasks.append(dt.task_to_assign)         #have all the maintenance tasks in one list for future use
    return dt
    
    
# ##################################################################################################################
# heuristics rules master function 
def core(dt):
    exit_cond=False       
    while exit_cond==False:
        dt.task_to_assign=None
        
        # maintenance tasks must be assinged first, so first the method checks if therer are maintenance tasks if yes it assignes them, if not continues witht he manufacturing tasks asssignemtn
        if len(dt.assignable_maintenance_tasks)>0: # if there are maintenance task to assign
                dt.task_to_assign=random.choice(dt.assignable_maintenance_tasks)
                dt.machine_to_assign=random.choice(dt.task_to_assign.machine_pt)  #select randomly a capable machine for the current task
        else:
            #Random Tasks assignemnt, also random orders assignemtn
            if dt.settings.method==1: #random selection of tasks and machines
                dt=hr.random_task_assignment(dt)
                    
                
            elif dt.settings.method==2:
                dt=hr.ru_tardines_task_assignment(dt)
                
            
            elif dt.settings.method==3:
                print("method 3")
            
        # ################################################
        
        dt=task_assignment(dt)          #assign task
        
        dt=remove_completed_orders(dt)  # check if the current order is empty of tasks and must be removed by the dt.assignable_tasks_total list 
        
        dt= time_measuring(dt)          #measure time
        exit_cond=exit_while(dt,exit_cond)
        dt=evm.events_managment(dt)#examine new events
        dt=defe.save_normal_task_defect(dt)
        dt.task_to_assign=None
        dt.unlocked_task=None
    dt.solution_list=kpi_calculation.final_resource_utilization(dt.solution_list,dt.settings)
    return dt

# ############################################################################################## 
### while exit function
def exit_while(dt,exit_cond):
    if len(dt.assignable_tasks_total)==0 and len(dt.orders_list)==0:
        if len(dt.events_to_assign_list)==0:
            exit_cond=True
        else:
            dt.current_time=dt.temp_rescheduling_time
            dt.rescheduling_time=dt.temp_rescheduling_time
            dt=evm.events_actions(dt)       #assign the actions for each of the events to assign
            dt.past_events_with_the_rescheduling_time.append([dt.rescheduling_time,copy.deepcopy(dt.events_to_assign_list)])
            dt.events_to_assign_list.clear()
            
    return exit_cond

# ############################################################################################## 
### time measuring algorithm
def time_measuring(dt):
    if dt.current_time<dt.task_to_assign.starting_time:
        dt.current_time=dt.task_to_assign.starting_time
    return dt

# ############################################################################################## 
### remove empty orders from the dt.assignable_tasks_total
def remove_completed_orders(dt):
    if len(dt.assignable_tasks[0])==0:
        dt.assignable_tasks_total=list(filter(None, dt.assignable_tasks_total))
        
    return dt





        
            
        
    
        
        


    