# -*- coding: utf-8 -*-
"""
Created on Wed Dec  2 15:54:52 2020
Machine class definition
@author: foivo
"""
import defect_generation as defg

class machines:
    def __init__(self,name,typ, operationalCost,defectProfile,defectRate,energyConsumption,MTBF,MTBT,capableTasks,inspectionAccuracy,capacity,output_buffer,defect_profile,prediction_active,prediction_horizon,prediction_RT,prediction_repetability,prediction_accuracy,prevention_time,prevention_machine_impovment,corrective_maintenance_active,corrective_maintenance_RT,corrective_maintenance_time_required,detection_prevention_active,detection_prevention_accuracy,detection_prevention_machine_impovment,detection_prevention_RT,detection_prevention_prevention_time_required):
        self.name=name
        self.typ=typ                #types of machines, normal, batch_all, batch_ind, repair and inspection
        self.operationalCost=operationalCost
        self.defectProfile=defectProfile
        self.defectRate=defectRate
        self.energyConsumption=energyConsumption
        self.energyConsumption=energyConsumption
        self.MTBF=MTBF
        self.MTBT=MTBT
        self.capableTasks=capableTasks
        self.output_buffer=output_buffer
        self.resource_utilization=0     # this valuie will show the total utulization of each machine at any time
        self.total_processing_time=0    # a measure for storring the total processing time for each machine in order to calculate the machine utlization
        self.period_processing_time=0   # it is a variable for the starage of the processing time for a specific period of maintenance, this value will have values between [0,MTBT], once maintenance happens then from that value subtract x% *MTBT 
        self.period_dedects=0           # this variable will be used for the detect prevent strategy for counting the defects after a prevention action, this number will change the probability for identifying the correct prevention action
        self.total_setup_time=0         # a variable for storing the total setup time
        self.defect_profile=defect_profile #which type of defect generation is selected for each machine (0: exponential, 1:linear, 2:random without machine deterioration)
        self.defects_count=0
        self.total_tasks_assigned=0
        self.previous_defect_n=0        # a variable for saving the number "defect_n" from the previous time a defect was assigned
        self.actual_defect_ratio=0
        self.assigned_tasks_list=[]     # this variable will be used to store the assinged tasks to the specific machine, this list will be used for may reasons, defect prediction, task assignment heuristic
        self.prediction_active=prediction_active
        self.prediction_horizon=prediction_horizon
        self.prediction_RT=prediction_RT
        self.prediction_repetability=prediction_repetability
        self.prediction_accuracy=prediction_accuracy
        self.prevention_time=prevention_time
        self.prevention_machine_impovment=prevention_machine_impovment
        self.corrective_maintenance_active=corrective_maintenance_active
        self.corrective_maintenance_RT=corrective_maintenance_RT
        self.corrective_maintenance_time_required=corrective_maintenance_time_required
        self.inspectionAccuracy=inspectionAccuracy
        self.detection_prevention_active=detection_prevention_active
        self.detection_prevention_accuracy=detection_prevention_accuracy
        self.detection_prevention_machine_impovment=detection_prevention_machine_impovment
        self.detection_prevention_RT=detection_prevention_RT
        self.detection_prevention_prevention_time_required=detection_prevention_prevention_time_required
        
        
        total_sum=0
        for tsk in self.capableTasks:
            total_sum+=tsk[2]
        self.average_processing_time=total_sum/len(self.capableTasks) #this variable will be used for the defects generation graph
            
        temp=defg.coeficients_calculation(defect_profile, self.average_processing_time, MTBT, defectRate)
        self.total_est_defects_per_MTBT_period=temp[0]
        self.defect_generation_coefficient=temp[1]
        
            
        if typ=="batch_ind" or typ=="batch_all":
            self.capacity=capacity
            #capacity is defined in "spaces" that the machine has. An attribute at the task class will be added as well
            # if machine capacity is 100 places and a batch process has space attribute 1 means that 100 parts can be processed in the machine at the same time
        else:
            self.capacity=None
        if typ=="batch_all":
            self.batch_set='set1' #by default the first set would be the active configuration until it changes
        else:
            self.batch_set=None

#batch_all: a batch process machine where one raw material enters and many parts are getting out
#batch_ind: may different parts are entering the machine and the same number are exiting (thermal treatment)
#normal: one raw material enters one part exits              
        

class tasks:
    def __init__(self,name,typ,level,processingTime,product,rawMaterial,scrapCost,reparable,batch_spaces,buffer_spaces,probability_to_be_reparable):
        self.name=name
        self.typ=typ        #the same types as the machine type are applied
        self.level=level
        self.processingTime=processingTime
        self.product=product
        self.rawMaterial=rawMaterial
        self.scrapCost=scrapCost
        self.reparable=reparable
        self.buffer_spaces=buffer_spaces
        self.inspection_after=False     #find if inspection happes afterwards
        self.bottom_tasks_non_repairable=None
        self.total_tasks_to_assign_non_reparable=None
        self.repairing_bottom_tasks=None
        self.probability_to_be_reparable=probability_to_be_reparable
        self.capable_machines_objects=[]
        
        if typ=="batch_ind" or typ=="batch_all":
            self.batch_spaces=batch_spaces
            #capacity is defined in "spaces" that the machine has. An attribute at the task class will be added as well
            # if machine capacity is 100 places and a batch process has space attribute 1 means that 100 parts can be processed in the machine at the same time
        else:
            self.batch_spaces=None
        
        
class product:
    def __init__(self,name,tasks):
        self.name=name
        self.tasks=tasks
        self.dummy_scheduling_tasks=[]
        self.tasks_to_assign_repairing=[] # it is a list for saving in different lists the repairing tasks that must be assigned in the event of repair
        
class orders: ## this class is not in use, the same is defined before the data_loading order section
    def __init__(self,name, arrival_date, due_date,customer_importance,responce_time,products_involved):
        self.name = name
        self.arrival_date = arrival_date
        self.due_date = due_date
        self.customer_importance = customer_importance
        self.responce_time=responce_time
        self.products_involved = products_involved
        self.OC = None
        self.delay_responce=None
        self.estimated_makespan=None
        self.estimated_resourse_utilization=[]
        self.estimated_tardiness=[]
        self.tasks_to_make=None
        self.event_type='order'
