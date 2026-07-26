from __future__ import annotations
import asyncio, json
from datetime import date, datetime, time
from decimal import Decimal
from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import delete, select
from sqlalchemy.orm import Session
from app.api.dependencies import get_current_user
from app.core.exceptions import ResourceNotFoundError
from app.database.session import get_db
from app.models.feedback import Feedback
from app.models.travel import TravelPlan, TravelRequest
from app.models.user import User
from app.models.workflow import ActionLog, SimulatedBooking, WorkflowEvent
from app.schemas.travel import BookingRequest, ClarificationRequest, ConfirmationAction, FeedbackRequest, ReplanRequest, TravelPlanRequest
from app.services.workflow_service import WorkflowService

router=APIRouter(prefix="/travel",tags=["Agentic Travel Planning"])

def val(v):
    if isinstance(v,(date,datetime,time)): return v.isoformat()
    if isinstance(v,Decimal): return float(v)
    if hasattr(v,"value"): return v.value
    return v

def model_dict(obj,exclude=()):
    return {c.name:val(getattr(obj,c.name)) for c in obj.__table__.columns if c.name not in exclude}

def plan_payload(plan,full=True):
    data=model_dict(plan)
    data["request"]=model_dict(plan.travel_request) if getattr(plan,"travel_request",None) else None
    if full:
        data["selected_transport"]=model_dict(plan.selected_transport) if plan.selected_transport else None
        data["selected_hotel"]=model_dict(plan.selected_hotel) if plan.selected_hotel else None
        data["transport_options"]=[model_dict(x) for x in plan.transport_options]
        data["hotel_options"]=[model_dict(x) for x in plan.hotel_options]
        data["weather"]=[model_dict(x) for x in plan.weather_records]
        data["attractions"]=[model_dict(x) for x in plan.attractions]
        data["itinerary"]=[{**model_dict(d),"activities":[model_dict(a) for a in d.activities]} for d in plan.itinerary_days]
        data["budget_breakdown"]=model_dict(plan.budget_breakdown) if plan.budget_breakdown else None
        alt=next((t.output_data for t in plan.tasks if t.task_name=="Generate alternatives"),{})
        data["alternatives"]=alt
        data["progress"]=progress_payload(plan)
    return data

def progress_payload(plan):
    total=sum(t.weight for t in plan.tasks) or 1; completed=sum(t.weight for t in plan.tasks if t.status.value=="COMPLETED")
    return {"percentage":round(completed/total*100),"tasks":[model_dict(t) for t in plan.tasks],"current_agent":next((t.agent_name for t in plan.tasks if t.status.value in {"RUNNING","RETRYING"}),None),"workflow_status":plan.travel_request.workflow_status.value}

@router.post("/extract-requirements")
def extract_endpoint(payload:TravelPlanRequest,user:User=Depends(get_current_user)):
    from app.agents.requirement_agent import extract_requirements, missing_fields
    data=extract_requirements(payload.instruction,payload.response_language)
    serialized={k:val(v) for k,v in data.items()}
    return {"success":True,"data":serialized,"missing_fields":missing_fields(data)}

@router.post("/validate-requirements")
def validate_endpoint(payload:TravelPlanRequest,user:User=Depends(get_current_user)):
    from app.agents.requirement_agent import extract_requirements, missing_fields
    data=extract_requirements(payload.instruction,payload.response_language); missing=missing_fields(data)
    return {"success":True,"valid":not missing,"missing_fields":missing,"data":{k:val(v) for k,v in data.items()}}

@router.post("/plan")
async def create_plan(payload:TravelPlanRequest,user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    service=WorkflowService(db); req=await service.create_request(user,payload.instruction,payload.response_language)
    if req.clarification_required:
        return {"success":True,"status":"clarification_required","request_id":req.id,"missing_fields":req.missing_fields,"question":req.clarification_question,"extracted_requirements":req.extracted_requirements}
    plan=await service.run(req)
    return {"success":True,"status":"completed","request_id":req.id,"plan_id":plan.id,"data":plan_payload(service.get_plan(user,plan.id))}

@router.post("/clarify")
async def clarify(payload:ClarificationRequest,user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    req=db.scalar(select(TravelRequest).where(TravelRequest.id==payload.request_id,TravelRequest.user_id==user.id))
    if not req: raise ResourceNotFoundError("Travel request was not found")
    svc=WorkflowService(db)
    req=await svc.apply_clarification(req,payload.answer)
    if req.clarification_required: return {"success":True,"status":"clarification_required","request_id":req.id,"missing_fields":req.missing_fields,"question":req.clarification_question}
    plan=await svc.run(req); return {"success":True,"status":"completed","plan_id":plan.id,"data":plan_payload(svc.get_plan(user,plan.id))}

@router.get("/plans")
def plans(user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    return {"success":True,"data":[plan_payload(x,False) for x in WorkflowService(db).list_plans(user)]}
@router.get("/plans/{plan_id}")
def plan(plan_id:int,user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    return {"success":True,"data":plan_payload(WorkflowService(db).get_plan(user,plan_id))}
@router.delete("/plans/{plan_id}")
def delete_plan(plan_id:int,user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    item=WorkflowService(db).get_plan(user,plan_id); db.delete(item); db.commit(); return {"success":True,"message":"Plan deleted"}
@router.post("/plans/{plan_id}/duplicate")
async def duplicate(plan_id:int,user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    svc=WorkflowService(db); item=svc.get_plan(user,plan_id)
    req=await svc.create_request(user,item.travel_request.original_instruction,item.travel_request.response_language)
    new=await svc.run(req); return {"success":True,"plan_id":new.id,"data":plan_payload(svc.get_plan(user,new.id))}

@router.get("/plans/{plan_id}/tasks")
def tasks(plan_id:int,user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    p=WorkflowService(db).get_plan(user,plan_id); return {"success":True,"data":[model_dict(x) for x in p.tasks]}
@router.get("/plans/{plan_id}/progress")
def progress(plan_id:int,user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    p=WorkflowService(db).get_plan(user,plan_id); return {"success":True,"data":progress_payload(p)}
@router.get("/plans/{plan_id}/transport-options")
def transports(plan_id:int,user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    return {"success":True,"data":[model_dict(x) for x in WorkflowService(db).get_plan(user,plan_id).transport_options]}
@router.get("/plans/{plan_id}/hotel-options")
def hotels(plan_id:int,user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    return {"success":True,"data":[model_dict(x) for x in WorkflowService(db).get_plan(user,plan_id).hotel_options]}
@router.get("/plans/{plan_id}/weather")
def weather(plan_id:int,user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    return {"success":True,"data":[model_dict(x) for x in WorkflowService(db).get_plan(user,plan_id).weather_records]}
@router.get("/plans/{plan_id}/attractions")
def attractions(plan_id:int,user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    return {"success":True,"data":[model_dict(x) for x in WorkflowService(db).get_plan(user,plan_id).attractions]}
@router.get("/plans/{plan_id}/itinerary")
def itinerary(plan_id:int,user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    p=WorkflowService(db).get_plan(user,plan_id); return {"success":True,"data":[{**model_dict(d),"activities":[model_dict(a) for a in d.activities]} for d in p.itinerary_days]}
@router.get("/plans/{plan_id}/budget")
def budget(plan_id:int,user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    p=WorkflowService(db).get_plan(user,plan_id); return {"success":True,"data":model_dict(p.budget_breakdown) if p.budget_breakdown else None}
@router.get("/plans/{plan_id}/alternatives")
def alternatives(plan_id:int,user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    p=WorkflowService(db).get_plan(user,plan_id); return {"success":True,"data":next((t.output_data for t in p.tasks if t.task_name=="Generate alternatives"),{})}

@router.get("/plans/{plan_id}/action-logs")
def logs(plan_id:int,agent:str|None=None,status_filter:str|None=Query(default=None,alias="status"),user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    WorkflowService(db).get_plan(user,plan_id); stmt=select(ActionLog).where(ActionLog.travel_plan_id==plan_id).order_by(ActionLog.timestamp)
    if agent: stmt=stmt.where(ActionLog.agent_name==agent)
    rows=list(db.scalars(stmt)); data=[model_dict(x) for x in rows if not status_filter or x.status.value==status_filter]
    return {"success":True,"data":data}
@router.get("/plans/{plan_id}/events")
def events(plan_id:int,user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    WorkflowService(db).get_plan(user,plan_id); rows=list(db.scalars(select(WorkflowEvent).where(WorkflowEvent.travel_plan_id==plan_id).order_by(WorkflowEvent.created_at)))
    return {"success":True,"data":[model_dict(x) for x in rows]}
@router.get("/plans/{plan_id}/stream")
def stream(plan_id:int,user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    WorkflowService(db).get_plan(user,plan_id); rows=list(db.scalars(select(WorkflowEvent).where(WorkflowEvent.travel_plan_id==plan_id).order_by(WorkflowEvent.created_at)))
    async def generator():
        for row in rows:
            yield f"event: {row.event_type}\ndata: {json.dumps(model_dict(row),default=str)}\n\n"; await asyncio.sleep(.03)
        yield 'event: stream_complete\ndata: {"status":"complete"}\n\n'
    return StreamingResponse(generator(),media_type="text/event-stream")

@router.post("/plans/{plan_id}/replan")
async def replan(plan_id:int,payload:ReplanRequest,user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    new=await WorkflowService(db).replan(user,plan_id,payload.event_type,payload.payload,payload.reason); return {"success":True,"old_plan_id":plan_id,"new_plan_id":new.id,"data":plan_payload(WorkflowService(db).get_plan(user,new.id))}
@router.get("/plans/{plan_id}/versions")
def versions(plan_id:int,user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    p=WorkflowService(db).get_plan(user,plan_id); return {"success":True,"data":[model_dict(v) for v in p.versions]}
@router.get("/plans/{plan_id}/compare")
def compare(plan_id:int,user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    p=WorkflowService(db).get_plan(user,plan_id); return {"success":True,"data":{"versions":[model_dict(v) for v in p.versions],"replanning":[model_dict(r) for r in p.replanning_history]}}

@router.post("/plans/{plan_id}/confirmation")
def confirmation(plan_id:int,payload:ConfirmationAction,user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    p=WorkflowService(db).get_plan(user,plan_id); item=WorkflowService(db).confirm(user,p,payload.action_type,payload.decision,payload.description); return {"success":True,"data":model_dict(item)}
@router.post("/plans/{plan_id}/book")
def book(plan_id:int,payload:BookingRequest,user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    p=WorkflowService(db).get_plan(user,plan_id); rows=WorkflowService(db).book(user,p,payload.booking_types); return {"success":True,"message":"Simulated booking completed","data":[model_dict(x) for x in rows]}
@router.get("/plans/{plan_id}/bookings")
def bookings(plan_id:int,user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    p=WorkflowService(db).get_plan(user,plan_id); return {"success":True,"data":[model_dict(x) for x in p.bookings]}
@router.post("/plans/{plan_id}/bookings/{booking_id}/cancel")
def cancel_booking(plan_id:int,booking_id:int,user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    p=WorkflowService(db).get_plan(user,plan_id); item=next((x for x in p.bookings if x.id==booking_id),None)
    if not item: raise ResourceNotFoundError("Booking was not found")
    from app.models.enums import BookingStatus; item.status=BookingStatus.CANCELLED; item.cancelled_at=datetime.utcnow(); db.commit(); return {"success":True,"data":model_dict(item)}

@router.post("/plans/{plan_id}/feedback")
def feedback(plan_id:int,payload:FeedbackRequest,user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    p=WorkflowService(db).get_plan(user,plan_id); item=WorkflowService(db).add_feedback(user,p,payload); return {"success":True,"message":"Feedback saved","data":model_dict(item)}
@router.get("/plans/{plan_id}/feedback")
def get_feedback(plan_id:int,user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    p=WorkflowService(db).get_plan(user,plan_id); return {"success":True,"data":[model_dict(x) for x in p.feedback_items]}
