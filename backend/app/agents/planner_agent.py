from __future__ import annotations
from uuid import uuid4
STANDARD_TASKS=[
 ("Validate requirements","Requirement Agent","CRITICAL",10,False,[]),
 ("Search transport","Transport Agent","HIGH",12,True,["Validate requirements"]),
 ("Search hotels","Hotel Agent","HIGH",12,True,["Validate requirements"]),
 ("Check weather","Weather Agent","HIGH",10,True,["Validate requirements"]),
 ("Search attractions","Attraction Agent","MEDIUM",10,True,["Validate requirements"]),
 ("Generate itinerary","Itinerary Agent","HIGH",12,False,["Search transport","Search hotels","Check weather","Search attractions"]),
 ("Calculate budget","Budget Agent","HIGH",10,False,["Generate itinerary"]),
 ("Generate alternatives","Alternative Agent","MEDIUM",8,False,["Calculate budget"]),
 ("Validate final plan","Coordinator Agent","CRITICAL",8,False,["Calculate budget"]),
 ("Save plan","Coordinator Agent","HIGH",5,False,["Validate final plan"]),
 ("Collect feedback","Feedback Agent","LOW",3,False,["Save plan"]),
]
def make_task_plan():
    return [{"task_uuid":str(uuid4()),"task_name":name,"agent_name":agent,"priority":priority,"weight":weight,
             "can_run_in_parallel":parallel,"dependencies":deps,"status":"NOT_STARTED"}
            for name,agent,priority,weight,parallel,deps in STANDARD_TASKS]
