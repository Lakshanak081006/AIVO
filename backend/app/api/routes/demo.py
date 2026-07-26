from __future__ import annotations
import json
from pathlib import Path
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.dependencies import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.travel import DemoEventRequest, ReplanRequest
from app.services.workflow_service import WorkflowService
from app.simulated_apis.services import travel_data_service
router=APIRouter(prefix="/demo",tags=["Demonstration Mode"])
@router.get("/scenarios")
def scenarios():
    path=Path(__file__).resolve().parents[3]/"data"/"demo_scenarios.json"; return {"success":True,"data":json.loads(path.read_text(encoding="utf-8"))}
@router.post("/plans/{plan_id}/simulate-failure")
def simulate_failure(plan_id:int,payload:DemoEventRequest,user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    WorkflowService(db).get_plan(user,plan_id); tool=payload.event_type.lower().replace("_api_failure",""); travel_data_service.set_failure(tool,payload.mode or "error"); return {"success":True,"message":f"{tool} failure enabled"}
@router.post("/plans/{plan_id}/simulate-event")
async def simulate_event(plan_id:int,payload:DemoEventRequest,user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    plan=await WorkflowService(db).replan(user,plan_id,payload.event_type,payload.payload,"Demonstration event"); return {"success":True,"new_plan_id":plan.id,"message":"Event simulated and plan regenerated"}
