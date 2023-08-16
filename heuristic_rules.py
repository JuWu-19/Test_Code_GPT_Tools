# -*- coding: utf-8 -*-
"""
Created on Fri Apr  2 08:57:15 2021

@author: foivo
"""

import random

# ######################################################################################################
# Random tasks and orders assignement
def random_task_assignment(dt):
    dt.assignable_tasks=[random.choice(dt.assignable_tasks_total)]  #select an order and assign the Order's tasks to the temp variable assignable_tasks
    try:
        dt.task_to_assign=random.choice(dt.assignable_tasks[0])   #select randomly task to assign 
    except:
       print('error at task selection')
       
    dt.machine_to_assign=random.choice(dt.task_to_assign.machine_pt)  #select randomly a capable machine for the current task
    m_obj=[x for x in dt.task_to_assign.capable_machine_objects if x.name==dt.machine_to_assign[0]]
    dt.machine_to_assign_object=m_obj[0]
    # temporary disabled
    # dt=inventory_check_batch_all(dt) 
    
    return dt

# ######################################################################################################
# Heuristic based on resource utilization and order Tardiness

def ru_tardines_task_assignment(dt):
    orders_with_tardiness=None
    active_orders_list=active_orders(dt)
    machines_with_sorted_ru_indexes=resource_utilization_find(dt)
    if len(active_orders_list)>1:       # if there is only one order there is no reason for calculating the tardiness, it will go directly to the RU
        orders_with_tardiness=temp_tardiness_calculation(dt,active_orders_list)
        tardiness_sorted=sorted(range(len(orders_with_tardiness[1])), key=lambda k: orders_with_tardiness[1][k], reverse=True) #sort them from highest to lowest
    
    
    if orders_with_tardiness!=None:      #if there are multiple oreders, ranking is required   
        for order_index in tardiness_sorted:
            order_name=active_orders_list[order_index][1]       #order to assign task
            for m_index in machines_with_sorted_ru_indexes:
                if len(dt.machines[m_index].assigned_tasks_list)>0: # if there are tasks left to the specific machine
                    current_order_tasks=[x for x in dt.machines[m_index].assigned_tasks_list if x.order==order_name]
                    if len(current_order_tasks)>0:  # if there are tasks of this order assigned to the specific machine
                        dt.task_to_assign=random.choice(current_order_tasks)
                        dt=machine_data_save(dt,m_index)
                    else:
                        break
                        
        
    
    
    else:                                # if there is only one order
        dt.assignable_tasks=[dt.assignable_tasks_total[0]]  #select an order and assign the Order's tasks to the temp variable assignable_tasks
        for m_index in machines_with_sorted_ru_indexes:
            if len(dt.machines[m_index].assigned_tasks_list)>0: # if there are tasks left to the specific machine
                dt.task_to_assign=random.choice(dt.machines[m_index].assigned_tasks_list)   #select randomly task to assign 
                dt=machine_data_save(dt,m_index)
                break
            
    


    return dt


# ######################################################################################################
# find active orders in order to examine only those
def active_orders(dt):
    active_orders_list=[]
    for check in dt.assignable_tasks_total:
        active_orders_list.append(check[0].order)
    
    active_orders_list=list(enumerate(active_orders_list))    
    return active_orders_list

# ##############################
#  calculate the lateness of each order in order to be used as ranking criterion
def temp_tardiness_calculation(dt,active_orders_list):
    orders_with_tardiness=[]
    tardiness=[]
    for order in active_orders_list:
        order_specs=[x for x in dt.assigned_orders if x.name==order[1]]
        order_kpi_specs=[x for x in dt.orders_kpi_list if x.order_name==order[1]]
        if order_kpi_specs[0].max_makespan>0:
            temp_tardiness=order_kpi_specs[0].max_makespan-order_specs[0].due_date
        else:
             temp_tardiness=dt.current_time-order_specs[0].due_date
        
        orders_with_tardiness.append([order,temp_tardiness])
        tardiness.append(temp_tardiness)
        
    return orders_with_tardiness,tardiness

# ##############################        
# find the resource utilization for each machine
def resource_utilization_find(dt):
    resource_utilization=[]
    for machine in dt.machines:
        resource_utilization.append(machine.resource_utilization)
    
    machines_with_sorted_ru=sorted(range(len(resource_utilization)), key=lambda k: resource_utilization[k])

    return machines_with_sorted_ru

# ##############################    
# store the machine processing time, machine object to dt
def machine_data_save(dt,m_index):   
    machine_name=dt.machines[m_index].name
    machine_pt=[x for x in dt.task_to_assign.machine_pt if x[0]==machine_name]
    dt.machine_to_assign=machine_pt[0]
    dt.machine_to_assign_object=dt.machines[m_index]
    
    return dt
    
    
    
    
    
    