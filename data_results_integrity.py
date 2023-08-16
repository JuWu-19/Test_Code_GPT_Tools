# -*- coding: utf-8 -*-
"""
Created on Sun Jan 24 16:38:15 2021

@author: foivo
"""

def check_if_all_tasks_were_assigned(dt):
    not_assigned_tasks=[]
    results_correct=True
    for order in dt.assigned_orders:
        for task in order.tasks_to_make[0][1]:
            if task.assigned==False:
                not_assigned_tasks.append(task)
                results_correct=False
    return results_correct,not_assigned_tasks

def check_task_assignment(dt):
    assigned_tasks=[]
    results_correct=True
    for tsk in dt.assignable_tasks[0]:
        if tsk.assigned==True:
            results_correct=False
            assigned_tasks.append(tsk)
    return results_correct, assigned_tasks


def check_dubicats_of_the_tasks_to_assign(dt):
    double=False
    all_id_tasks=[x for x in dt.assignable_tasks[0] if x.task_id==dt.task_to_assign.task_id]
    order_temp=[x for x in dt.orders if x[0]==dt.task_to_assign.order]
    total_all_id_tasks=[x for x in order_temp[0][1] if x.task_id== dt.task_to_assign.task_id]
    counter=0
    for tsk in all_id_tasks:
        if tsk.name==dt.task_to_assign.name:
            counter+=1
        if counter>1:
            double=True
    return double, all_id_tasks,total_all_id_tasks,counter
            
def check_if_all_tasks_if_doubles_exist(dt,event):
    all_id_tasks=[x for x in dt.assignable_tasks[0] if x.task_id==dt.task_to_assign.task_id]
    order_temp=[x for x in dt.orders if x[0]==event.event_object[0].order]
    total_all_id_tasks=[x for x in order_temp[0][1] if x.task_id== event.event_object[0].task_id]
    double=False
    double_tasks=[]
    results_correct=True
    for tsk in total_all_id_tasks:
        counter=0
        for tsk2 in total_all_id_tasks:
            if tsk.name==tsk2.name:
                counter+=1
        if counter>1:
            double=True

    return double     



def evm_tasks_to_assign_check_dublicats(assignable_tasks_total_current, bottom_tasks):
    correct=True
    for tsk in bottom_tasks:
        check2=[x for x in assignable_tasks_total_current[0] if x.name==tsk.name and x.task_id==tsk.task_id]   
        if len(check2)>0:
            correct=False
            break
    return correct, check2
        