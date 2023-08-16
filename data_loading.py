# -*- coding: utf-8 -*-
"""
Created on Wed Dec  2 15:18:26 2020
Module for loading the data from an excel file and 
structuring it into the defined variables and classes
@author: foivos

"""
# ssection for importing the required modules
from kpi_calculation import kpi_order_instance_creation
import copy
import pandas as pd
import main_classes as mc
import core_scheduling as cs
import events_managment as evm
import kpi_calculation as kpi


def batch_tasks_number(order,batch_data):
    unique_b_tasks = []
    for tsk in order[2]:        #find the unique batch tasks
        if tsk.name not in unique_b_tasks:
            unique_b_tasks.append(tsk.name)

    for b_tsk in unique_b_tasks:
        count_temp=len([x for x in order[2] if x.name==b_tsk])
        
        check=[x for x in batch_data.batch_tasks_count if x[0]==b_tsk]
        if len(check)>0:
            check[0][1]+=count_temp
        else:
            batch_data.batch_tasks_count.append([b_tsk,count_temp])
            
    return batch_data
# #############################################################################
def extract_if_inspection_happens_afterwards(tasks_list,task_dependences_list):
    #if inspection happens after a task this means that this task will have only one dependency
    for tsk in task_dependences_list: #tsk is the inspection task
        if len(tsk[1])==1:
            if tsk[1][0]!='-':
                t=[x for x in tasks_list if x.name==tsk[0]]
                if t[0].typ=='inspection':
                    temp=[x for x in tasks_list if x.name==tsk[1][0]]
                    temp[0].inspection_after=True
        
    

# #############################################################################

class buffers:
    def __init__(self,name,capacity,machines):
        self.name=name
        self.capacity=capacity
        self.status_full=False
        self.max_number=0 #shows the maximum number of occupied spaces
        self.machines=machines # the names of the machines that has output to the specific buffer
        self.current_spaces_occupancy=0 # is the current count of spaces occupied
        self.current_tasks_in=[] #is a list with all the tasks stored in the buffer at 
        
# ######################################################################################################
#class for storing all the data input and output 
class data:
    def __init__(self,machines,buffers_list,settings,solution_list,orders_kpi_list,assignable_tasks_total,batch_data,orders,orders_list,product_counter):
        self.task_to_assign=None
        self.batch_task_to_assign=None
        self.machine_to_assign=None
        self.machine_to_assign_object=None
        self.machines=machines
        self.buffers_list=buffers_list
        self.settings=settings
        self.solution_list=solution_list
        self.orders_kpi_list=orders_kpi_list
        self.assignable_tasks_total=assignable_tasks_total      # a list with separated according to the order the assignanble tasks
        self.assignable_maintenance_tasks=[]
        self.assignable_tasks=[]                                # on each iteration one specific order is selected and a task is selected from it
        self.batch_data=batch_data
        self.orders=orders              # is a list with the assigned orders (here only the involved tasks and order name)
        self.assigned_orders=[]         # a list with the order objects of the assigned orders
        self.orders_list=orders_list    # its a complete list with order objects
        self.tasks_list=None
        self.task_dependences_list=None
        self.task_dependences_list_repair=None
        self.product_list=None
        self.rescheduling_time=0            # is the final rescheduling time for a rescheduling
        self.temp_rescheduling_time=0       #is the temporary rescheduling time, until the rescheduling is preformed this time might change according to the invovled events
        self.current_time=0
        self.rescheduling_preparation_time=30
        self.new_event_occured=False
        self.unassigned_events=[]       # a list which will contain all the pending events
        self.events_to_assign_list=[]
        self.unlocked_task=None
        self.buffer_full_status=False
        self.detected_defects_Master=[]
        self.detected_defects= []      
        self.non_detected_defects=[]
        self.product_counter=product_counter
        self.dummy_scheduling_repair_tasks=[]
        self.test=None #for storing temporary var for testing
        self.past_events_with_the_rescheduling_time=[]
        self.maintenance_counter=0
        self.maintenance_past_tasks=[]
# #############################################################################
### products
def product_structure(table,tasks_details_excel):
    temp_list=[]
    for level in table:
        temp_list.append([table[level].dropna(axis=0),level])
        
    
    product_ranges_temp=[]
    for index, value in temp_list[0][0].items():
        product_ranges_temp.append(index)
    product_ranges_temp.append(len(table[1])) 
       
    product_ranges=[]
    for start_index in range(len(product_ranges_temp)):
        if product_ranges_temp[start_index]!=product_ranges_temp[-2]:
            product_ranges.append([product_ranges_temp[start_index],product_ranges_temp[start_index+1]-1])
        else:
            product_ranges.append([product_ranges_temp[start_index],product_ranges_temp[-1]-1])
            break
    
    product_taks=[]
    number_of_products=0
    for serie in temp_list:                                 # for each one of the levels
        for index, value in serie[0].items():               # 
            for inRange_index in range(len(product_ranges)):
                if index <= product_ranges[inRange_index][1]:
                    prod='Product'+str(inRange_index+1)
                    if number_of_products<inRange_index+1:
                        number_of_products=inRange_index+1
                    break
            
            for taskName in tasks_details_excel:
                if taskName==value:
                    task_type=tasks_details_excel[taskName][0]
                    break
            
            product_taks.append([prod,value,serie[1],task_type])
    return product_taks,number_of_products    
# #############################################################################
#function for creating the buffer objects
def buffers_objects_creation(Buffers_characteristics_excel,machines_list,settings):
    buffers_list_temp=[]
    for buffer in Buffers_characteristics_excel:
        machine_temp=[x for x in machines_list if x.output_buffer==buffer]
        
        if settings.buffers_policy==1: #if the entered buffers capacity is used for the buffers
            bufferCapacity=Buffers_characteristics_excel[buffer][0]
        elif settings.buffers_policy==0: #if infinent buffers are used
            bufferCapacity=100000         #100000 is used as an infinante buffer
            
        temp=buffers(buffer,
                     bufferCapacity,
                     machine_temp)
        buffers_list_temp.append(temp)
        
    return buffers_list_temp

# ################################################################
# solution list creation
def solution_list_creation(machines):
    solution_list=[]
    for m in machines: # create the solution list, with the machines names
        temp=[m.name,[],m]
        solution_list.append(temp)
    
    return solution_list

# #################################################################
 # function for grouping all the code for finding the bottom tasks
def bottom_tasks_group(orders):
    temp=cs.find_bottom_tasks(orders,1) #find the bottom "normal"tasks, 1 means that the normal tasks will be evaluated
    assignable_tasks=temp[0]
    orders=temp[1]
    return orders,assignable_tasks

def dumy_scheduling_task_generation(task_type,tasks_list,task_dependences_list):
    dummy_scheduling_task_list_local=[]
    for task in tasks_list:
        if task.typ==task_type:
            task_dep_temp=cs.find_dependencies(task.name,task_dependences_list)
            temp=cs.scheduling_task(None,
                                copy.deepcopy(task.typ),
                                copy.deepcopy(task.name),
                                copy.deepcopy(task.level),
                                None,
                                copy.deepcopy(task_dep_temp[0]),      #unlock_task
                                copy.deepcopy(task_dep_temp[1]),      #unlock_dependent_tasks
                                copy.deepcopy(task_dep_temp[2]),
                                task.product,
                                task.processingTime,
                                task.capable_machines_objects,
                                task.rawMaterial,
                                task.scrapCost,
                                task.reparable,
                                task.batch_spaces,
                                task.buffer_spaces,
                                task.inspection_after,
                                copy.deepcopy(task.bottom_tasks_non_repairable),
                                copy.deepcopy(task.repairing_bottom_tasks),
                                copy.deepcopy(task.probability_to_be_reparable),
                                copy.deepcopy(task.total_tasks_to_assign_non_reparable))
            
            dummy_scheduling_task_list_local.append(temp)
    return dummy_scheduling_task_list_local
# #############################################################################
# calculate the total number of products per order for adjusting the counter for the data loading process
def products_count_per_order(order,orders_list):
    current_order=[x for x in orders_list if x.name==order[0][0]]
    count=0
    for prod in current_order[0].products_involved:
        count+=prod[1]
    return count
# #############################################################################
def extract_bottom_tasks_non_repairable_defect(task, task_dependences_list):
    task_dep=[x for x in task_dependences_list if x[0]==task.name]
    total_tasks_to_remake=[]
    if task_dep[0][1][0]!='-': #if it is not a bottom task
        list_to_check=task_dep[0][1]
        total_tasks_to_remake=copy.deepcopy(list_to_check)
        bottom_tasks=[]
        exit_p=False
        while exit_p==False:
            temp_list=[]
            for dep_tsk in list_to_check:
                temp=[x for x in task_dependences_list if x[0]==dep_tsk]
                if temp[0][1][0]!='-':
                    temp_list.extend(temp[0][1])
                    total_tasks_to_remake.extend(temp[0][1])
                else:
                    bottom_tasks.append(dep_tsk)
            if len(temp_list)>0:
                list_to_check=temp_list
            else:
                exit_p=True
        total_tasks_to_remake.append(task.name) # add also the task it self       
        # if there is a defect and the product is non repairable the defect was detected with inspection, the inspection task must be added
        # always there will be one to one the task with the corresponding inspection, thats why x[1][0]
        
        insp_task=[x for x in task_dependences_list if x[1][0]==task.name]
        if task.typ != 'inspection':
            if len(insp_task)>0:
                total_tasks_to_remake.append(insp_task[0][0])
    else: #if it is bottom task then the current task it self is the bottom task
        bottom_tasks=[task.name]
        insp_task=[x for x in task_dependences_list if x[1][0]==task.name]
        total_tasks_to_remake.append(task.name)
        if len(insp_task)>0:
            total_tasks_to_remake.append(insp_task[0][0])

    return bottom_tasks,total_tasks_to_remake
                
# #############################################################################
def extract_bottom_repairing_tasks(task,task_dependences_list_repair):
    if task.reparable==True:
        temp=[x for x in task_dependences_list_repair if x[1][0]==task.name]
        if type(temp[0][0]) is list: 
            bottom_repairing_task_list=temp[0][0]
        else:
            bottom_repairing_task_list=[temp[0][0]]
    else:
        bottom_repairing_task_list=None
    return bottom_repairing_task_list

# #############################################################################
# function for creating the scheduling tasks that are required for each product
def product_scheduling_tasks_generation(product_list,dummy_scheduling_task_list):
    for prod in product_list:
        pro_sch_list_temp=[]
        for tsk in prod.tasks:
            if tsk[3]!='repair':
                temp=[x for x in dummy_scheduling_task_list if x.name==tsk[1]]
                pro_sch_list_temp.extend(temp)
        prod.dummy_scheduling_tasks=pro_sch_list_temp


# #############################################################################

def repairing_tasks_actual_level_assignment(product_taks_repair,product_taks):
    #find the unique names of the "repairng Products"
    rep_prod_temp=[]
    product_taks_repair_corrected=[]
    for prd in product_taks_repair:
        rep_prod_temp.append(prd[0])
    rep_prod=list(set(rep_prod_temp)) #a list with the unique "repairing product" names
    
    for r_prod in rep_prod: # for each of the "repairing Products"
        temp=[x for x in product_taks_repair if x[0]==r_prod] # all the corresponding repairing tasks + the defected one
        norm_t=[x for x in temp if x[3]=='normal']
        rep_t=[x for x in temp if x[3]=='repair']        
        actual_info=[x for x in product_taks if x[1]==norm_t[0][1]]
        for tsk in rep_t:
            new_level=round(actual_info[0][2]-(tsk[2]/10),1)
            temp_rep_task=[actual_info[0][0],tsk[1],new_level,tsk[3]]
            product_taks_repair_corrected.append(temp_rep_task)
            product_taks.append(temp_rep_task)
                   
    return product_taks
# #############################################################################
def define_unloked_repairing_tasks(product_taks_repair,dummy_scheduling_repair_task_list,dummy_scheduling_task_list,task_dependences_list_repair,product_list):
    #find the unique names of the "repairng Products"
    rep_prod_temp=[]
    for prd in product_taks_repair:
        rep_prod_temp.append(prd[0])
    rep_prod=list(set(rep_prod_temp)) #a list with the unique "repairing product" names
    for prd in rep_prod:
        temp=[x for x in product_taks_repair if x[0]==prd] # all the corresponding repairing tasks + the defected one
        norm_t=[x for x in temp if x[3]=='normal']
        rep_t=[x for x in temp if x[3]=='repair']
        normal_task_object=[x for x in dummy_scheduling_task_list if x.name==norm_t[0][1]]
        inspection_task_object=[x for x in dummy_scheduling_task_list if x.name==normal_task_object[0].unlock_task]
        actual_product=[x for x in product_list if x.name==normal_task_object[0].product]
        repaing_tasks_groups=[]
        for lis in  rep_t: 
            temp_dep=cs.find_dependencies(lis[1],task_dependences_list_repair) #unlock_task,unlock_dependent_tasks,task_dependencies
            repairing_task_object=[x for x in dummy_scheduling_repair_task_list if x.name==lis[1]]
            repaing_tasks_groups.append(repairing_task_object[0])
            if temp_dep[0]==None: # if it is top level
                
                if inspection_task_object[0].task_type=='inspection':
                    repairing_task_object[0].unlock_task=inspection_task_object[0].unlock_task
                    repairing_task_object[0].unlock_dependent_tasks=inspection_task_object[0].unlock_dependent_tasks
                else:
                    repairing_task_object[0].unlock_task=inspection_task_object[0].name
                    repairing_task_object[0].unlock_dependent_tasks=normal_task_object[0].unlock_dependent_tasks

            else:
                repairing_task_object[0].unlock_task=temp_dep[0]
                repairing_task_object[0].unlock_dependent_tasks=temp_dep[1]
        actual_product[0].tasks_to_assign_repairing.append(repaing_tasks_groups)
        
# #############################################################################          
def assing_capable_machines_objects(tasks_list, machines_list):
    for tsk in tasks_list:
        for m in tsk.processingTime:
            temp_machine=[x for x in machines_list if x.name==m[0]]
            tsk.capable_machines_objects.append(temp_machine[0])
# #############################################################################

def data_loading(settings):


    xl=pd.ExcelFile(settings.file_path)
    machines_excel=xl.parse('machines')
    task_times_excel=xl.parse('tasks_times')
    products_excel=xl.parse('products')
    task_dependences_excel=xl.parse('task_dependences')
    orders_excel=xl.parse('orders').drop(['order_name'], axis=1)
    tasks_details_excel=xl.parse('tasks_details').drop(['-'], axis=1)
    repairing_str=xl.parse('repairing')
    batch_all_machines_capacities=xl.parse('batch_all_machines_capacities')
    Buffers_characteristics_excel=xl.parse('Buffers_characteristics').drop(['Name'], axis=1)

    ### extract the times from the excel 
    
    # tasks dependences
    task_dependences_list=[]                    #list for saving the tasks dependences
    task_dependences_list_repair=[] 
    for task in task_dependences_excel:
        temp_list=[]
        for row in range(len(task_dependences_excel[task].dropna(axis=0))):
            temp_list.append(task_dependences_excel[task][row])
        for t in tasks_details_excel:
            if t==task:
                task_type=tasks_details_excel[t][0]
                break
        if task_type!="repair":
            task_dependences_list.append([task,temp_list])          # dependences list for the normal and ispection tasks
        else:
            task_dependences_list_repair.append([task,temp_list])   # dependences list for the repairing tasks
        
    
     ### tasks times
    tasks_times=[]
    for task in task_times_excel.columns[1:]:
        for row in task_times_excel[task].dropna(axis=0).index:
            temp_list=[task_times_excel['machine_Name'][row],task,task_times_excel[task].dropna(axis=0)[row]]
            tasks_times.append(temp_list)
          
    
     
    result=product_structure(products_excel,tasks_details_excel)
    product_taks=result[0]
    repair_result=product_structure(repairing_str,tasks_details_excel)
    product_taks_repair=repair_result[0]

    product_taks=repairing_tasks_actual_level_assignment(product_taks_repair,product_taks)
    
            
    ### product class taribute definition
    product_list_temp=[]
    for prod in product_taks:
        if prod[0] not in product_list_temp:
            product_list_temp.append(prod[0])    #this list contains the unique product names
    
    product_list=[]
    for prod in product_list_temp:
        temp=mc.product(prod,
                        [x[0:4] for x in product_taks if x[0]==prod])
        product_list.append(temp)
        
    ### tasks details
    tasks_list=[]
    for task in tasks_details_excel:
        if tasks_details_excel[task][2]==1:
            reparability=True
        elif tasks_details_excel[task][2]==0:
            reparability=False
        temp=mc.tasks(task,                                                     #name
                      tasks_details_excel[task][0],                             #type
                      [x[0:3] for x in product_taks if x[1]==task][0][2],       #level
                      [x[0:3] for x in tasks_times if x[1]==task],              #processing times
                      [x[0:3] for x in product_taks if x[1]==task][0][0],       #product
                      tasks_details_excel[task][1],                             #raw material
                      tasks_details_excel[task][3],                             #scrap cost
                      reparability,                                             #reparable
                      tasks_details_excel[task][4],                             #number of spaces for batch process
                      tasks_details_excel[task][5],                             #number of spaces occupied at the buffer for storing the task
                      tasks_details_excel[task][6])                             # probability to be repairable 
        if temp.typ!='repair':
           res=extract_bottom_tasks_non_repairable_defect(temp, task_dependences_list) # extract the bottom levels for each task, to be used when the defect is non reparable and a new one is required 
           temp.bottom_tasks_non_repairable=res[0]
           temp.total_tasks_to_assign_non_reparable=res[1]
           
        temp.repairing_bottom_tasks=extract_bottom_repairing_tasks(temp,task_dependences_list_repair)
        
        tasks_list.append(temp)
        
    extract_if_inspection_happens_afterwards(tasks_list,task_dependences_list)    
    ### dummy scheduling tasks create a tasks list based on the scheduling task class in order to have dummy scheduling tasks
    dummy_scheduling_task_list=[]
    temp_dymmy_list=dumy_scheduling_task_generation('normal',tasks_list,task_dependences_list)
    dummy_scheduling_task_list.extend(temp_dymmy_list)
    temp_dymmy_list=dumy_scheduling_task_generation('inspection',tasks_list,task_dependences_list)
    dummy_scheduling_task_list.extend(temp_dymmy_list)
    temp_dymmy_list=dumy_scheduling_task_generation('batch_all',tasks_list,task_dependences_list)
    dummy_scheduling_task_list.extend(temp_dymmy_list)
    temp_dymmy_list=dumy_scheduling_task_generation('batch_ind',tasks_list,task_dependences_list)
    dummy_scheduling_task_list.extend(temp_dymmy_list)
    
    dummy_scheduling_repair_task_list=[]
    temp_dymmy_list=dumy_scheduling_task_generation('repair',tasks_list,task_dependences_list_repair)
    dummy_scheduling_repair_task_list.extend(temp_dymmy_list)
    
    define_unloked_repairing_tasks(product_taks_repair,dummy_scheduling_repair_task_list,dummy_scheduling_task_list,task_dependences_list_repair,product_list)
    
    product_scheduling_tasks_generation(product_list,dummy_scheduling_task_list)

    ### extract the machines from the excel and stractur it as indicated in machines_class
    temp_cap_list= batch_all_machines_capacities.values.tolist()
    capacities_list=[]
    for rec in temp_cap_list: #formalise the capacieties in list format
        cleanedList = [x for x in rec if str(x) != 'nan']
        capacities_list.append(cleanedList)

        
    
    machines_list=[]
    for i in range(len(machines_excel)):
        temp_list=[]
        for attribute in machines_excel:
            temp_list.append(machines_excel[attribute][i])
            
        if temp_list[1]=="batch_all": #for the batch all machines extract from the excel the capacities
            cap_sets=[x for x in capacities_list if x[0]==temp_list[0]]
            temp_cap_list=[]
            count=1
            for rec in cap_sets:
                size=int((len(rec)-2)/2) # calculate how many different tasks can be perfomred at the same time 
                temp=[]
                for i in range(size):
                    t_l=[rec[(i+1)*2],rec[((i+1)*2)+1]]
                    temp.append(t_l)
                set_name='set'+str(count)
                temp_cap_list.append([set_name,temp])
                count+=1
            machine_batch_all_capacities=temp_cap_list
        else:
            machine_batch_all_capacities=temp_list[9]
        
        if temp_list[1]=='inspection':
            detectionAccuracy=temp_list[8]
        else:
            detectionAccuracy=None
        
        if temp_list[12]==1:
            prediction_status=True
            predictionHorizon=temp_list[13]
            predictionResponceTime=temp_list[14]
            predictionRepetability=temp_list[15]
            predictionAccurasy=temp_list[16]
            preventionTime=temp_list[17]
            prevention_machine_impovment=temp_list[18]
        else:
            prediction_status=False
            predictionHorizon=None
            predictionResponceTime=None
            predictionRepetability=None
            predictionAccurasy=None
            preventionTime=None
            prevention_machine_impovment=None
            
        if temp_list[19]==1:
            corrective_maintenance_active=True
            corrective_maintenance_RT=temp_list[20]
            corrective_maintenance_time_required=temp_list[21]
        else:
            corrective_maintenance_active=False
            corrective_maintenance_RT=None
            corrective_maintenance_time_required=None
            
        if temp_list[22]==1:
            detection_prevention_active=True
            detection_prevention_accuracy=temp_list[23]
            detection_prevention_machine_impovment=temp_list[24]
            detection_prevention_RT=temp_list[25]
            detection_prevention_prevention_time_required=temp_list[26]
        else:
            detection_prevention_active=False
            detection_prevention_accuracy=None
            detection_prevention_machine_impovment=None
            detection_prevention_RT=None
            detection_prevention_prevention_time_required=None
            
            
        temp=mc.machines(    temp_list[0], #name
                             temp_list[1], #type
                             temp_list[2], #operation cost
                             temp_list[3], #defect profile
                             temp_list[4], #defect rate
                             temp_list[5], #machine energy consumptuion
                             temp_list[6], #MTBF
                             temp_list[7], #MTBT
                             [x[0:3] for x in tasks_times if x[0]==temp_list[0]], #for filtering based on machine 
                             detectionAccuracy, #Detection accuracy
                             machine_batch_all_capacities, #number of spaces for batch process for machine
                             temp_list[10], #output buffer name
                             temp_list[11],  # defect profile
                             prediction_status,
                             predictionHorizon,
                             predictionResponceTime,
                             predictionRepetability,
                             predictionAccurasy,
                             preventionTime,
                             prevention_machine_impovment,
                             corrective_maintenance_active,
                             corrective_maintenance_RT,
                             corrective_maintenance_time_required,
                             detection_prevention_active,
                             detection_prevention_accuracy,
                             detection_prevention_machine_impovment,
                             detection_prevention_RT,
                             detection_prevention_prevention_time_required)
        machines_list.append(temp)
    
    assing_capable_machines_objects(tasks_list, copy.deepcopy(machines_list))
    buffers_list=buffers_objects_creation(Buffers_characteristics_excel,machines_list,settings)
    
   
    ### orders creation
    orders_list=[]
    for order in orders_excel:
        temp=orders_excel[order].dropna(axis=0)
        temp_len=int((len(temp)-3)/2)
        temp_list=[]
        for i in range(temp_len):
            temp_list.append([product_list[int(temp[4+(i*2)])], int(temp[5+(i*2)])])
        
        
        
        temp_orders=mc.orders(order,        #order name
                              temp[0],      #order arrival date
                              temp[1],      #order due date 
                              temp[2],      #customer importance
                              temp[3],      #order responce Time
                              temp_list 
                              )    
        orders_list.append(temp_orders)
    
    # for each order caclulate the tasks that are required 
    product_counter=0
    order_temp=[]
    for order in orders_list:
        # create the scheduling tasks for each order
        res=cs.task_extraction_from_order(order,task_dependences_list,product_counter,tasks_list)
        tasks_to_schedule=res[0]
        batch_tasks_to_schedule=res[1]
        product_counter=res[2]
        tmp=[order.name,tasks_to_schedule,batch_tasks_to_schedule]
        order_temp.append(tmp)
        order.tasks_to_make=[copy.deepcopy(tmp)]

    ### section for calculating the estimated order lead time for each order
    # ######################################################################################################
    #class for grouping all the information regarding the batch all tasks
    
    class batch_data_cl:
        def __init__(self, dummy_sch_tasks,batch_counter,inventory_batch_all_list):
            self.dummy_sch_tasks=dummy_sch_tasks
            self.batch_counter=batch_counter
            self.inventory_batch_all_list=inventory_batch_all_list
            self.pending_batch_ind_tasks=[]
            self.past_batch_ind_tasks=[]
            self.batch_tasks_count=[]
                

    batch_data=batch_data_cl(dummy_scheduling_task_list,0,[])
    for order in order_temp:
        order_characteristics=[x for x in orders_list if x.name==order[0]]
        
        orders_kpi_list=kpi_order_instance_creation([order])
        batch_data_tmp=batch_tasks_number(order,copy.deepcopy(batch_data))
        machines_temp=copy.deepcopy(machines_list)
        solution_list=solution_list_creation(machines_temp)
        
        temp=bottom_tasks_group([order])
        order=temp[0]
        # prod_counter_local=products_count_per_order(order,orders_list)
        prod_counter_local=copy.deepcopy(product_counter)
        assignable_tasks=temp[1]
        evm.tasks_allocation_to_machines(machines_temp,assignable_tasks[0])
        
        # for atsk in assignable_tasks[0]:
        #     for m_atsk in atsk.capable_machine_objects:
        #         temp_m=[x for x in machines_temp if x.name==m_atsk.name]
        #         atsk.capable_machine_objects.append(temp_m[0])

                
        
        data_class=data(machines_temp,
                        copy.deepcopy(buffers_list),
                        settings,
                        solution_list,
                        orders_kpi_list,
                        assignable_tasks,
                        batch_data_tmp,
                        order,
                        [],        #orders_list, in the current case only one order is assigned
                        prod_counter_local)
        data_class.assigned_orders.append(order_characteristics[0])
        
        data_class.dummy_scheduling_repair_tasks=dummy_scheduling_repair_task_list  
        data_class.product_list=product_list              
        # data_class.events_managment_mode=False
        
        dt=cs.core(data_class)
        dt=kpi.production_cost_calculation(dt)
        estimated_tardiness=kpi.tardiness_calulation_in_data_loading(dt)
        
        # solution_list=cs.heuristics(settings,orders,machines_temp,batch_data_tmp,copy.deepcopy(buffers_list),orders_kpi_list,solution_list,assignable_tasks)
        # section for saving the order estimated makespan to the order object
        order_object=[x for x in orders_list if x.name==order[0][0]]
        order_object[0].estimated_makespan=dt.orders_kpi_list[0].makespan
        order_object[0].estimated_tardiness=estimated_tardiness
        for m in dt.solution_list:
            order_object[0].estimated_resourse_utilization.append(m[2])
    
    
    solution_list_f=solution_list_creation(machines_list)
    data_class_final=data(machines_list,
                          buffers_list,
                          settings,
                          solution_list_f,
                          [],
                          [],
                          batch_data,
                          [],
                          orders_list,
                          product_counter)
                          
    data_class_final.dummy_scheduling_repair_tasks=dummy_scheduling_repair_task_list
    data_class_final.tasks_list=tasks_list
    data_class_final.task_dependences_list=task_dependences_list
    data_class_final.task_dependences_list_repair=task_dependences_list_repair
    data_class_final.product_list=product_list
    
    return  data_class_final



