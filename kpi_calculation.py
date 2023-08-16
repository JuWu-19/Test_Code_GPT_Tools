# -*- coding: utf-8 -*-
"""
Created on Tue Dec 22 07:50:38 2020
In this module the KPIs will be calulated

@author: Foivos_Surface
"""
class order_kpis:
    def __init__(self,order_name):
        self.order_name=order_name
        self.makespan=0
        self.operational_cost=0
        self.raw_materials_cost=0
        self.max_makespan=0
        self.tardiness=0

# ##################################################################################################################
def kpi_order_instance_creation(new_orders): #function for creating the kpis object for an order
    temp=[]
    for order in new_orders:
        new_order_kpi_object=order_kpis(order[0]) #order is only the name of the order, new orders is a list wiht the names of all the new orders
        temp.append(new_order_kpi_object)
        
    return temp

# ##################################################################################################################
# function for calculating the makespan for each assinged task
def makespan_calculation(dt,machine_index,task):        #task is added separately from the dt, due to the batch processes, where another task needs to be loaded
     
    try:            #calculate the time that the previous task if the selected machine was finished
        previous_task_makespan=dt.solution_list[machine_index[0][0]][1][-1].makespan
    except:
        previous_task_makespan=0
    
    startin_time_list=[task.unlock_makespan,previous_task_makespan,dt.rescheduling_time]
    max_starting_time=max(startin_time_list)
    task.starting_time=max_starting_time
    task.makespan=max_starting_time + task.processing_time + task.setup_time
    
    dt=day_calculation_makespan_correction(dt,task)
        
    return dt

 # ##################################################################################################################
                               
def overall_order_makespan(dt,task_to_assign):
    current_order=[x for x in dt.orders_kpi_list if x.order_name==task_to_assign.order]
    if current_order[0].makespan<task_to_assign.makespan:
        current_order[0].makespan=task_to_assign.makespan
        
    return dt

# ##################################################################################################################

def day_calculation_makespan_correction(dt,task):
    day=int(task.makespan/dt.settings.minutes_per_day) # 1440 is the nuber of minutes per day
    upper_limit=(day*dt.settings.minutes_per_day)+(dt.settings.number_of_shifts*60)
    if task.makespan>upper_limit:
       task.makespan= ((day+1)*dt.settings.minutes_per_day)+task.processing_time + task.setup_time # if true make starting time for the task the starting of the next day
       
    return dt

# ##################################################################################################################
# for resource utilization calculation
def total_processing_setup_time(dt,machine_index,task):
    dt.solution_list[machine_index[0][0]][2].total_processing_time+=task.processing_time
    dt.solution_list[machine_index[0][0]][2].period_processing_time+=task.processing_time
    dt.solution_list[machine_index[0][0]][2].total_setup_time+=task.setup_time
    
    return dt
# ##################################################################################################################
def resource_utilization(dt,machine_index,task):
    dt=total_processing_setup_time(dt,machine_index,task)
    max_makespan=max_makespan_calculation(dt.solution_list)
    if max_makespan<task.makespan:
        max_makespan=task.makespan
    day=int(max_makespan/dt.settings.minutes_per_day)+1  # 1440 is the nuber of minutes per day
    if day==1:
        available_time=max_makespan
    else:
        # available_time=(day-1)*(dt.settings.number_of_shifts*60)+(day-1)*dt.settings.minutes_per_day-max_makespan
        available_time=day*(dt.settings.number_of_shifts*60)
    # for calculating the RU the setup time is subtracted from the the total available time
    try:
        dt.solution_list[machine_index[0][0]][2].resource_utilization=100*dt.solution_list[machine_index[0][0]][2].total_processing_time/(available_time-dt.solution_list[machine_index[0][0]][2].total_setup_time)
    except:
        dt.solution_list[machine_index[0][0]][2].resource_utilization=0

    return dt
# ##################################################################################################################

def final_resource_utilization(solution_list,settings):
    for machine_index in enumerate(solution_list):
        try:
            task_to_assign=solution_list[machine_index[0]][1][-1]
            solution_list=resource_utilization(solution_list,[machine_index],task_to_assign,settings)
        except:
            pass
    
    return solution_list
    
# ##################################################################################################################
# find the max makespan for calculating the resource utlization
def max_makespan_calculation(solution_list):
    max_makespan=0
    for makespan_check in solution_list:
        try :
            mksp=makespan_check[1][-1].makespan
        except:
            mksp=0
        if max_makespan<mksp:
            max_makespan=mksp

    return max_makespan

# ##################################################################################################################
# production cost calculation for each order separatly, operational and raw material
def production_cost_calculation(dt):
    for order in dt.orders_kpi_list:
        temp_raw_materials=0
        max_makespan_old=0
        for machine in dt.solution_list:
            filtered_machine_task_list=order_task_filtering(machine[1],order) #filter and keep only the tasks that belongs to the current order
            temp_processing_time=0
            
            # max makespan calculation
            try:                        # in case that there is no task assigned to the machine
                max_makespan_new=filtered_machine_task_list[-1].makespan
                if max_makespan_new>max_makespan_old:
                    max_makespan_old=max_makespan_new
            except:
                pass
                
                
            for task in filtered_machine_task_list:
                temp_processing_time+=task.processing_time #calculate the total processing time of the task for the current machine
                temp_raw_materials+=task.raw_material            #calculate the raw materials cost
            
            op_cost_temp=temp_processing_time*machine[2].operationalCost
            order.operational_cost+=op_cost_temp 
        order.max_makespan=max_makespan_old
        order.raw_materials_cost+=temp_raw_materials
        
    return dt
                
# ##################################################################################################################
# Filter orders in order to have tasks of the order under investigation        
def order_task_filtering(task_list,order):
    filtered_task_lsit=[]
    for task in task_list:
        try:
            if task.order==order.order_name:
                filtered_task_lsit.append(task)
        except:
            pass
    
    return filtered_task_lsit
                
# ##################################################################################################################
# estimated Tardiness calculation
def tardiness_calulation_in_data_loading(dt):
    for order in dt.orders_kpi_list:
        order_specs=[x for x in dt.assigned_orders if x.name==order.order_name]
        
        temp_makespan=order.max_makespan+order_specs[0].arrival_date
        estimated_tardiness=temp_makespan-order_specs[0].due_date
        if estimated_tardiness<0:
            estimated_tardiness_final=0
        else:
            estimated_tardiness_final=estimated_tardiness
            
    return estimated_tardiness_final


# ##################################################################################################################
# Tardiness calculation  
def tardiness_calculation(dt):
    for order in dt.orders_kpi_list:
        order_specs=[x for x in dt.assigned_orders if x.name==order.order_name]

        tardiness=order.max_makespan-order_specs[0].due_date
        if tardiness<0:
            tardiness_final=0
        else:
            tardiness_final=tardiness
        
        order.tardiness=tardiness_final
        
    return dt
        
        
    
    
    
    
                                    
    
    