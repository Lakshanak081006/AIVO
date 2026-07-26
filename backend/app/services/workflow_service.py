from __future__ import annotations
import asyncio
from datetime import date, datetime, time, timezone
from decimal import Decimal
from typing import Any
from uuid import uuid4
from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload
from app.agents.budget_agent import calculate_budget, cheaper_alternative
from app.agents.itinerary_agent import generate_itinerary
from app.agents.planner_agent import make_task_plan
from app.agents.requirement_agent import clarification_question, extract_requirements, missing_fields
from app.agents.scoring import rank_hotels, rank_transport
from app.core.config import settings
from app.core.exceptions import ConflictError, LyzrUnavailableError, LyzrAuthenticationError, LyzrResponseError, ResourceNotFoundError, ValidationFailureError, WorkflowError
from app.models.enums import ActionLogStatus, BookingStatus, ConfirmationStatus, PlanStatus, TaskPriority, TaskStatus, TransportType, WorkflowStatus
from app.models.feedback import Feedback
from app.models.itinerary import BudgetBreakdown, ItineraryActivity, ItineraryDay
from app.models.option import Attraction, HotelOption, TransportOption, WeatherRecord
from app.models.task import AgentTask, TaskDependency
from app.models.travel import PlanVersion, TravelPlan, TravelRequest
from app.models.user import User
from app.models.workflow import ActionLog, ConfirmationRequest, ReplanningHistory, SimulatedBooking, WorkflowEvent
from app.schemas.travel import FeedbackRequest
from app.simulated_apis.services import travel_data_service
from app.utils.retry import with_retry
from app.utils.translation import final_summary as translated_summary

class WorkflowService:
    def __init__(self, db: Session):
        self.db=db

    def _event(self, request_id:int|None, plan_id:int|None, event_type:str, agent:str, task:str, status:str, progress:int, message:str, data:dict|None=None):
        event=WorkflowEvent(travel_request_id=request_id,travel_plan_id=plan_id,event_type=event_type,agent_name=agent,task_name=task,status=status,progress_percentage=max(0,min(100,progress)),message=message,event_data=data or {})
        self.db.add(event); self.db.flush(); return event

    def _log(self, request_id:int|None, plan_id:int|None, agent:str, task:str, action:str, message:str, *, status=ActionLogStatus.INFO, tool=None, decision=None, reason=None, error=None, retry=0):
        log=ActionLog(travel_request_id=request_id,travel_plan_id=plan_id,agent_name=agent,task_name=task,action_type=action,action_performed=message,tool_used=tool,input_summary=None,output_summary=None,decision=decision,decision_reason=reason,error_details=error or {},retry_count=retry,status=status,metadata_json={})
        self.db.add(log); self.db.flush(); return log

    def _serialize_requirements(self,data):
        return {k:(v.isoformat() if isinstance(v,date) else v) for k,v in data.items()}

    # ------------------------------------------------------------------
    # Lyzr-aware requirement extraction helpers
    # ------------------------------------------------------------------

    async def _lyzr_extract(self, user: User, instruction: str, response_language: str, session_id: str) -> dict | None:
        """Try Lyzr extraction. Returns mapped requirements dict or None on any failure."""
        from app.integrations.lyzr_service import lyzr_service
        from app.services.lyzr_response_mapper import map_lyzr_to_requirements
        try:
            result = await lyzr_service.chat(
                user_id=user.email or str(user.id),
                session_id=session_id,
                message=instruction,
            )
            mapped = map_lyzr_to_requirements(result)
            # Carry clarification fields from Lyzr result
            mapped["_lyzr_clarification_required"] = bool(result.get("clarification_required"))
            mapped["_lyzr_missing_fields"] = result.get("missing_fields") or []
            mapped["_lyzr_clarification_question"] = result.get("clarification_question")
            mapped["_lyzr_raw"] = result
            self._log(None, None, "Lyzr Requirement Agent", "Extract requirements", "LYZR_REQUIREMENT_EXTRACTION",
                      "Requirements extracted using Lyzr Studio.", status=ActionLogStatus.SUCCESS)
            return mapped
        except (LyzrUnavailableError, LyzrAuthenticationError, LyzrResponseError) as exc:
            self._log(None, None, "Lyzr Integration", "Extract requirements", "LYZR_FALLBACK",
                      f"Lyzr unavailable. Existing local requirement agent used. Reason: {type(exc).__name__}",
                      status=ActionLogStatus.WARNING)
            return None
        except Exception as exc:
            self._log(None, None, "Lyzr Integration", "Extract requirements", "LYZR_FALLBACK",
                      f"Lyzr unexpected error. Using local agent. Reason: {type(exc).__name__}",
                      status=ActionLogStatus.WARNING)
            return None

    async def create_request(self, user: User, instruction: str, response_language: str) -> TravelRequest:
        session_id = f"aiva-{uuid4().hex}"
        lyzr_result = None

        if settings.LYZR_ENABLED:
            lyzr_result = await self._lyzr_extract(user, instruction, response_language, session_id)

        if lyzr_result:
            extracted = lyzr_result
            # Override response_language from caller
            extracted["response_language"] = response_language
            # Use Lyzr clarification fields if present
            lyzr_missing = extracted.pop("_lyzr_missing_fields", [])
            lyzr_clarify = extracted.pop("_lyzr_clarification_required", False)
            lyzr_question = extracted.pop("_lyzr_clarification_question", None)
            extracted.pop("_lyzr_raw", None)
            missing = lyzr_missing if lyzr_missing else missing_fields(extracted)
            clarify_q = lyzr_question if lyzr_question else (clarification_question(missing) if missing else None)
        else:
            extracted = extract_requirements(instruction, response_language)
            lyzr_missing = []
            lyzr_clarify = False
            lyzr_question = None
            missing = missing_fields(extracted)
            clarify_q = clarification_question(missing) if missing else None

        # Apply user preferences for missing fields
        preference = user.preference
        if preference:
            if not extracted.get("transport_preference") and preference.preferred_transport_type:
                extracted["transport_preference"] = preference.preferred_transport_type.value
            if not extracted.get("food_preference") and preference.preferred_food_type:
                extracted["food_preference"] = preference.preferred_food_type
            if not extracted.get("tourist_interests") and preference.tourist_interests:
                extracted["tourist_interests"] = preference.tourist_interests

        req = TravelRequest(
            user_id=user.id,
            original_instruction=instruction,
            detected_language=extracted.get("detected_language"),
            response_language=extracted.get("response_language", response_language),
            source=extracted.get("source"),
            destination=extracted.get("destination"),
            start_date=extracted.get("start_date"),
            end_date=extracted.get("end_date"),
            trip_duration_days=extracted.get("trip_duration_days"),
            traveller_count=extracted.get("traveller_count") or 1,
            budget=Decimal(str(extracted.get("budget") or 0)),
            currency=extracted.get("currency") or "INR",
            transport_preference=extracted.get("transport_preference"),
            hotel_preference=extracted.get("hotel_preference"),
            minimum_hotel_rating=extracted.get("minimum_hotel_rating"),
            food_preference=extracted.get("food_preference"),
            tourist_interests=extracted.get("tourist_interests") or [],
            special_requirements=extracted.get("special_requirements") or [],
            extracted_requirements=self._serialize_requirements(extracted),
            missing_fields=missing,
            clarification_required=bool(missing),
            clarification_question=clarify_q,
            workflow_status=WorkflowStatus.WAITING_FOR_CLARIFICATION if missing else WorkflowStatus.CREATED,
            lyzr_session_id=session_id if settings.LYZR_ENABLED else None,
        )
        self.db.add(req); self.db.flush()
        self._log(req.id, None, "Requirement Agent", "Extract requirements", "EXTRACT",
                  f"Extracted travel requirements; missing fields: {', '.join(missing) if missing else 'none'}",
                  status=ActionLogStatus.SUCCESS)
        self._event(req.id, None, "requirements_extracted", "Requirement Agent", "Extract requirements",
                    "COMPLETED", 5, "Travel requirements extracted", {"missing_fields": missing})
        self.db.commit(); self.db.refresh(req)
        return req

    async def apply_clarification(self, req: TravelRequest, answer: str) -> TravelRequest:
        """Apply a clarification answer, reusing the Lyzr session if available."""
        if settings.LYZR_ENABLED and req.lyzr_session_id:
            from app.integrations.lyzr_service import lyzr_service
            from app.services.lyzr_response_mapper import map_lyzr_to_requirements
            try:
                result = await lyzr_service.chat(
                    user_id=req.user.email or str(req.user_id),
                    session_id=req.lyzr_session_id,
                    message=answer,
                )
                mapped = map_lyzr_to_requirements(result)
                lyzr_missing = result.get("missing_fields") or []
                lyzr_question = result.get("clarification_question")
                # Merge into existing extracted requirements
                current = dict(req.extracted_requirements or {})
                for key, val in self._serialize_requirements(mapped).items():
                    if val not in (None, [], ""):
                        current[key] = val
                self._apply_current_to_req(req, current)
                req.missing_fields = lyzr_missing if lyzr_missing else missing_fields(
                    {**current, "start_date": req.start_date, "end_date": req.end_date,
                     "traveller_count": req.traveller_count, "budget": float(req.budget) if req.budget else None})
                req.clarification_required = bool(req.missing_fields)
                req.clarification_question = lyzr_question if lyzr_question else (
                    clarification_question(req.missing_fields) if req.missing_fields else None)
                req.workflow_status = WorkflowStatus.WAITING_FOR_CLARIFICATION if req.missing_fields else WorkflowStatus.CREATED
                req.clarification_answer = answer
                self.db.commit(); self.db.refresh(req); return req
            except Exception as exc:
                self._log(req.id, None, "Lyzr Integration", "Clarification", "LYZR_FALLBACK",
                          f"Lyzr clarification failed, using local agent. Reason: {type(exc).__name__}",
                          status=ActionLogStatus.WARNING)

        # Local fallback (original logic)
        combined = f"{req.original_instruction}. Additional details: {answer}"
        parsed = extract_requirements(combined, req.response_language)
        current = dict(req.extracted_requirements or {})
        for key, val in self._serialize_requirements(parsed).items():
            if val not in (None, [], ""): current[key] = val
        if len(req.missing_fields) == 1:
            field = req.missing_fields[0]
            if field == "budget":
                import re
                m = re.search(r"[\d,]+", answer); current[field] = float(m.group().replace(",", "")) if m else None
            elif field == "traveller_count":
                import re
                m = re.search(r"\d+", answer); current[field] = int(m.group()) if m else None
            elif field in {"source", "destination"}: current[field] = answer.strip().title()
        self._apply_current_to_req(req, current)
        req.missing_fields = missing_fields(
            {**current, "start_date": req.start_date, "end_date": req.end_date,
             "traveller_count": req.traveller_count, "budget": float(req.budget) if req.budget else None})
        req.clarification_required = bool(req.missing_fields)
        req.clarification_question = clarification_question(req.missing_fields) if req.missing_fields else None
        req.workflow_status = WorkflowStatus.WAITING_FOR_CLARIFICATION if req.missing_fields else WorkflowStatus.CREATED
        req.clarification_answer = answer
        self.db.commit(); self.db.refresh(req); return req

    def _apply_current_to_req(self, req: TravelRequest, current: dict) -> None:
        """Write merged requirement dict back onto the TravelRequest ORM object."""
        for field in ["start_date", "end_date"]:
            if isinstance(current.get(field), str) and current[field]:
                setattr(req, field, date.fromisoformat(current[field]))
        for field in ["source", "destination", "trip_duration_days", "traveller_count",
                      "currency", "transport_preference", "hotel_preference", "food_preference"]:
            if current.get(field) is not None: setattr(req, field, current[field])
        if current.get("budget") is not None: req.budget = Decimal(str(current["budget"]))
        req.extracted_requirements = current

    async def run(self, req:TravelRequest) -> TravelPlan:
        if req.clarification_required: raise ValidationFailureError("Required travel details are missing")
        req.workflow_status=WorkflowStatus.PLANNING
        plan=TravelPlan(user_id=req.user_id,travel_request_id=req.id,title=f"{req.destination} trip",status=PlanStatus.GENERATING,total_cost=Decimal("0"),currency=req.currency,budget=req.budget,remaining_budget=req.budget,budget_exceeded=False,current_version=1,confirmation_status=ConfirmationStatus.PENDING)
        self.db.add(plan); self.db.flush()
        tasks=self._create_tasks(req,plan)
        self._event(req.id,plan.id,"workflow_started","Coordinator Agent","Workflow","RUNNING",8,"Agentic travel planning started")
        self.db.commit()
        requirements={"source":req.source,"destination":req.destination,"start_date":req.start_date,"end_date":req.end_date,"trip_duration_days":req.trip_duration_days or ((req.end_date-req.start_date).days+1),"traveller_count":req.traveller_count,"budget":float(req.budget),"currency":req.currency,"transport_preference":req.transport_preference,"hotel_preference":req.hotel_preference,"food_preference":req.food_preference,"tourist_interests":req.tourist_interests,"special_requirements":req.special_requirements}
        try:
            results=await asyncio.gather(
                self._run_tool(req,plan,tasks["Search transport"],"Transport Agent","transport",lambda:travel_data_service.search_transport(req.source,req.destination,req.start_date,req.traveller_count)),
                self._run_tool(req,plan,tasks["Search hotels"],"Hotel Agent","hotel",lambda:travel_data_service.search_hotels(req.destination,max(1,(req.end_date-req.start_date).days),req.traveller_count)),
                self._run_tool(req,plan,tasks["Check weather"],"Weather Agent","weather",lambda:travel_data_service.get_weather(req.destination,req.start_date,req.end_date)),
                self._run_tool(req,plan,tasks["Search attractions"],"Attraction Agent","attraction",lambda:travel_data_service.search_attractions(req.destination)),
                return_exceptions=True,
            )
            if any(isinstance(r,Exception) for r in results):
                errors=[str(r) for r in results if isinstance(r,Exception)]
                raise WorkflowError("One or more required search agents failed: "+"; ".join(errors))
            transport_data,hotel_data,weather_data,attraction_data=results
            transports=rank_transport(transport_data,req.transport_preference); hotels=rank_hotels(hotel_data)
            if not transports or not hotels: raise WorkflowError("No available transport or hotel options")
            self._persist_options(plan,transports,hotels,weather_data,attraction_data)
            self.db.flush()
            plan.selected_transport_id=plan.transport_options[0].id
            plan.selected_hotel_id=plan.hotel_options[0].id
            itinerary=generate_itinerary(requirements,attraction_data,weather_data)
            self._set_task(tasks["Generate itinerary"],TaskStatus.RUNNING)
            self._persist_itinerary(plan,itinerary)
            self._set_task(tasks["Generate itinerary"],TaskStatus.COMPLETED,{"days":len(itinerary)})
            budget=calculate_budget(requirements,transports[0],hotels[0],itinerary)
            self._set_task(tasks["Calculate budget"],TaskStatus.RUNNING)
            self._persist_budget(plan,budget)
            self._set_task(tasks["Calculate budget"],TaskStatus.COMPLETED,budget)
            alternatives=cheaper_alternative(requirements,transports,hotels,itinerary,budget) if not budget["within_budget"] else {}
            self._set_task(tasks["Generate alternatives"],TaskStatus.COMPLETED,alternatives)
            plan.total_cost=Decimal(str(budget["total_cost"])); plan.remaining_budget=Decimal(str(budget["remaining_budget"])); plan.budget_exceeded=not budget["within_budget"]
            plan.status=PlanStatus.READY; req.workflow_status=WorkflowStatus.COMPLETED
            plan.final_summary=self._summary(req,plan,transports[0],hotels[0],budget,alternatives)
            # Optional Lyzr decision summary
            decision_meta = await self._lyzr_decision_summary(req, plan, transports[0], hotels[0], budget, alternatives)
            if decision_meta.get("decision_summary"):
                plan.final_summary = decision_meta["decision_summary"]
            self._set_task(tasks["Validate final plan"],TaskStatus.COMPLETED,{"valid":True})
            self._set_task(tasks["Save plan"],TaskStatus.COMPLETED,{"plan_id":plan.id})
            self._version(plan,"Initial generated plan",alternatives)
            self._log(req.id,plan.id,"Coordinator Agent","Complete workflow","COMPLETE","Travel plan completed and saved",status=ActionLogStatus.SUCCESS,decision="Plan ready",reason="All required agents completed successfully")
            self._event(req.id,plan.id,"workflow_completed","Coordinator Agent","Workflow","COMPLETED",100,"Travel plan completed",{"budget_exceeded":plan.budget_exceeded})
            self.db.commit(); self.db.refresh(plan); return plan
        except Exception as exc:
            req.workflow_status=WorkflowStatus.FAILED; plan.status=PlanStatus.FAILED
            self._log(req.id,plan.id,"Coordinator Agent","Workflow","FAILURE","Travel workflow failed",status=ActionLogStatus.ERROR,error={"message":str(exc)})
            self._event(req.id,plan.id,"workflow_failed","Coordinator Agent","Workflow","FAILED",100,str(exc))
            self.db.commit(); raise

    async def _run_tool(self,req,plan,task,agent,tool,operation):
        self._set_task(task,TaskStatus.RUNNING); self._event(req.id,plan.id,"agent_started",agent,task.task_name,"RUNNING",20,f"{agent} started")
        def retry_notice(number,delay,error):
            task.retry_count=number; task.status=TaskStatus.RETRYING
            self._log(req.id,plan.id,agent,task.task_name,"RETRY",f"Retry {number} after {delay:.2f}s",status=ActionLogStatus.RETRY,tool=tool,error={"message":str(error)},retry=number)
            self._event(req.id,plan.id,"retry_started",agent,task.task_name,"RETRYING",25,f"Retrying {tool} service")
            self.db.flush()
        try:
            result=await with_retry(operation,on_retry=retry_notice)
            self._set_task(task,TaskStatus.COMPLETED,{"count":len(result) if isinstance(result,list) else 1})
            self._log(req.id,plan.id,agent,task.task_name,"TOOL_RESULT",f"{agent} returned {len(result) if isinstance(result,list) else 1} result(s)",status=ActionLogStatus.SUCCESS,tool=tool)
            self._event(req.id,plan.id,"task_completed",agent,task.task_name,"COMPLETED",45,f"{task.task_name} completed")
            self.db.flush(); return result
        except Exception as exc:
            # Demonstration-safe fallback: clear the simulated failure and use the local dataset.
            travel_data_service.set_failure(tool, None)
            try:
                result=await operation()
                self._set_task(task,TaskStatus.COMPLETED,{"count":len(result) if isinstance(result,list) else 1,"fallback_used":True})
                self._log(req.id,plan.id,agent,task.task_name,"FALLBACK",f"{agent} used the local fallback dataset",status=ActionLogStatus.WARNING,tool=tool,error={"message":str(exc)},retry=task.retry_count)
                self._event(req.id,plan.id,"fallback_used",agent,task.task_name,"COMPLETED",40,f"Fallback data used for {tool}")
                self.db.flush(); return result
            except Exception as fallback_error:
                task.status=TaskStatus.FAILED; task.error_message=str(fallback_error); task.completed_at=datetime.now(timezone.utc)
                self._log(req.id,plan.id,agent,task.task_name,"TOOL_FAILURE",f"{agent} failed",status=ActionLogStatus.ERROR,tool=tool,error={"message":str(fallback_error)},retry=task.retry_count)
                self.db.flush(); raise

    def _create_tasks(self,req,plan):
        result={}; definitions=make_task_plan()
        for d in definitions:
            task=AgentTask(task_uuid=d["task_uuid"],travel_request_id=req.id,travel_plan_id=plan.id,task_name=d["task_name"],description=d["task_name"],agent_name=d["agent_name"],priority=TaskPriority(d["priority"]),status=TaskStatus.COMPLETED if d["task_name"]=="Validate requirements" else TaskStatus.WAITING,can_run_in_parallel=d["can_run_in_parallel"],weight=d["weight"],retry_count=0,maximum_retries=settings.MAX_TOOL_RETRIES,input_data={},output_data={})
            self.db.add(task); self.db.flush(); result[task.task_name]=task
        for d in definitions:
            for dep in d["dependencies"]:
                self.db.add(TaskDependency(task_id=result[d["task_name"]].id,depends_on_task_id=result[dep].id))
        return result

    def _set_task(self,task,status,output=None):
        task.status=status
        if status==TaskStatus.RUNNING: task.started_at=datetime.now(timezone.utc)
        if status in {TaskStatus.COMPLETED,TaskStatus.FAILED}: task.completed_at=datetime.now(timezone.utc)
        if output is not None: task.output_data=output
        self.db.flush()

    def _persist_options(self,plan,transports,hotels,weather,attractions):
        for x in transports:
            plan.transport_options.append(TransportOption(external_reference=x["external_reference"],provider=x["provider"],transport_type=TransportType(x["transport_type"]),service_number=x["service_number"],source=x["source"],destination=x["destination"],departure_date=date.fromisoformat(x["departure_date"]),departure_time=time.fromisoformat(x["departure_time"]),arrival_date=date.fromisoformat(x["arrival_date"]),arrival_time=time.fromisoformat(x["arrival_time"]),duration_minutes=x["duration_minutes"],price_per_person=Decimal(str(x["price_per_person"])),traveller_count=x["traveller_count"],total_price=Decimal(str(x["total_price"])),available=x["available"],available_seats=x["available_seats"],number_of_stops=x["number_of_stops"],rating=x["rating"],cancellation_policy=x["cancellation_policy"],booking_class=x["booking_class"],normalized_score=x.get("normalized_score"),recommendation_type=x.get("recommendation_type"),raw_data=x))
        for x in hotels:
            plan.hotel_options.append(HotelOption(external_reference=x["external_reference"],name=x["name"],city=x["city"],address=x["address"],latitude=x["latitude"],longitude=x["longitude"],price_per_night=Decimal(str(x["price_per_night"])),number_of_nights=x["number_of_nights"],number_of_rooms=x["number_of_rooms"],total_price=Decimal(str(x["total_price"])),rating=x["rating"],room_type=x["room_type"],amenities=x["amenities"],available=x["available"],cancellation_policy=x["cancellation_policy"],distance_from_city_centre=x["distance_from_city_centre"],check_in_time=time.fromisoformat(x["check_in_time"]),check_out_time=time.fromisoformat(x["check_out_time"]),normalized_score=x.get("normalized_score"),recommendation_type=x.get("recommendation_type"),raw_data=x))
        for x in weather:
            plan.weather_records.append(WeatherRecord(city=x["city"],weather_date=date.fromisoformat(x["weather_date"]),condition=x["condition"],minimum_temperature=x["minimum_temperature"],maximum_temperature=x["maximum_temperature"],rain_probability=x["rain_probability"],wind_speed=x["wind_speed"],weather_alert=x["weather_alert"],outdoor_suitability=x["outdoor_suitability"],raw_data=x))
        for x in attractions:
            plan.attractions.append(Attraction(external_reference=x["external_reference"],name=x["name"],city=x["city"],category=x["category"],description=x["description"],address=x["address"],latitude=x["latitude"],longitude=x["longitude"],entry_fee=Decimal(str(x["entry_fee"])),opening_time=time.fromisoformat(x["opening_time"]),closing_time=time.fromisoformat(x["closing_time"]),average_visit_duration_minutes=x["average_visit_duration_minutes"],rating=x["rating"],environment_type=x["environment_type"],closed_days=x["closed_days"],distance_from_hotel=x["distance_from_hotel"],weather_suitable=x["weather_suitable"],selected=x["selected"],raw_data=x))

    def _persist_itinerary(self,plan,itinerary):
        for d in itinerary:
            day=ItineraryDay(day_number=d["day_number"],itinerary_date=date.fromisoformat(d["date"]),title=d["title"],estimated_daily_cost=Decimal(str(d["estimated_daily_cost"])),notes=None)
            for idx,a in enumerate(d["activities"]):
                day.activities.append(ItineraryActivity(start_time=time.fromisoformat(a["start_time"]),end_time=time.fromisoformat(a["end_time"]),activity=a["activity"],location=a["location"],activity_type=a["activity_type"],environment_type=a["environment_type"],travel_time_minutes=a["travel_time_minutes"],estimated_cost=Decimal(str(a["estimated_cost"])),weather_suitability=a["weather_suitability"],notes=a.get("notes"),display_order=idx))
            plan.itinerary_days.append(day)

    def _persist_budget(self,plan,b):
        plan.budget_breakdown=BudgetBreakdown(**{k:Decimal(str(v)) if k not in {"within_budget","currency"} else v for k,v in b.items()})

    def _summary(self,req,plan,t,h,b,alternatives):
        return translated_summary(req.response_language,days=req.trip_duration_days,source=req.source,destination=req.destination,transport=t["transport_type"],provider=t["provider"],hotel=h["name"],currency=req.currency,total=b["total_cost"],within_budget=b["within_budget"],exceeded=b["exceeded_amount"],alternatives=bool(alternatives))

    async def _lyzr_decision_summary(self, req, plan, transport, hotel, budget, alternatives) -> dict:
        """Optionally call Lyzr for a final decision summary. Falls back silently."""
        if not settings.LYZR_ENABLED:
            return {}
        from app.integrations.lyzr_service import lyzr_service
        from app.services.lyzr_response_mapper import extract_decision_summary
        session_id = req.lyzr_session_id or f"aiva-{uuid4().hex}"
        context = (
            f"Trip: {req.source} to {req.destination}, {req.trip_duration_days} days, "
            f"{req.traveller_count} travellers. Budget: {req.currency} {float(req.budget):.0f}. "
            f"Selected transport: {transport['provider']} {transport['transport_type']} "
            f"({req.currency} {transport['total_price']}). "
            f"Selected hotel: {hotel['name']} rating {hotel['rating']} "
            f"({req.currency} {hotel['total_price']}). "
            f"Total cost: {req.currency} {budget['total_cost']:.0f}. "
            f"Within budget: {budget['within_budget']}. "
            f"Cheaper alternative available: {bool(alternatives)}. "
            f"Please provide a concise decision_summary for the traveller."
        )
        try:
            result = await lyzr_service.chat(
                user_id=req.user.email or str(req.user_id),
                session_id=session_id,
                message=context,
            )
            meta = extract_decision_summary(result)
            self._log(req.id, plan.id, "Lyzr Decision Agent", "Decision summary",
                      "LYZR_DECISION_SUMMARY", "Final decision summary generated.",
                      status=ActionLogStatus.SUCCESS)
            return meta
        except Exception as exc:
            self._log(req.id, plan.id, "Lyzr Integration", "Decision summary",
                      "LYZR_FALLBACK", f"Lyzr decision summary skipped: {type(exc).__name__}",
                      status=ActionLogStatus.WARNING)
            return {}

    def _snapshot(self,plan,extra=None):
        return {"plan_id":plan.id,"version":plan.current_version,"selected_transport_id":plan.selected_transport_id,"selected_hotel_id":plan.selected_hotel_id,"total_cost":float(plan.total_cost),"budget":float(plan.budget),"final_summary":plan.final_summary,"extra":extra or {}}
    def _version(self,plan,reason,extra=None):
        self.db.add(PlanVersion(travel_plan_id=plan.id,version_number=plan.current_version,reason=reason,snapshot=self._snapshot(plan,extra),total_cost=plan.total_cost))

    def get_plan(self,user,plan_id):
        stmt=select(TravelPlan).where(TravelPlan.id==plan_id,TravelPlan.user_id==user.id).options(selectinload(TravelPlan.travel_request),selectinload(TravelPlan.transport_options),selectinload(TravelPlan.hotel_options),selectinload(TravelPlan.attractions),selectinload(TravelPlan.weather_records),selectinload(TravelPlan.itinerary_days).selectinload(ItineraryDay.activities),selectinload(TravelPlan.budget_breakdown),selectinload(TravelPlan.tasks),selectinload(TravelPlan.action_logs),selectinload(TravelPlan.workflow_events),selectinload(TravelPlan.versions),selectinload(TravelPlan.feedback_items),selectinload(TravelPlan.bookings))
        plan=self.db.scalar(stmt)
        if not plan: raise ResourceNotFoundError("Travel plan was not found")
        return plan

    def list_plans(self,user): return list(self.db.scalars(select(TravelPlan).where(TravelPlan.user_id==user.id).order_by(TravelPlan.created_at.desc())))

    async def replan(self,user,plan_id,event_type,payload,reason=None):
        plan=self.get_plan(user,plan_id); old=self._snapshot(plan); req=plan.travel_request
        previous=plan.current_version; plan.current_version+=1; plan.status=PlanStatus.REPLANNING; req.workflow_status=WorkflowStatus.REPLANNING
        affected=[]; preserved=["User profile","Original request"]
        event=event_type.upper()
        if event in {"HEAVY_RAIN","WEATHER"}: travel_data_service.set_failure("weather","heavy_rain"); affected=["Check weather","Generate itinerary","Calculate budget"]
        elif event in {"TRANSPORT_CANCELLATION","TRANSPORT_API_FAILURE"}: travel_data_service.set_failure("transport","cancelled" if "CANCELLATION" in event else "error"); affected=["Search transport","Generate itinerary","Calculate budget"]
        elif event in {"HOTEL_UNAVAILABLE","HOTEL_API_FAILURE"}: travel_data_service.set_failure("hotel","unavailable" if "UNAVAILABLE" in event else "error"); affected=["Search hotels","Generate itinerary","Calculate budget"]
        elif event=="ATTRACTION_CLOSED": travel_data_service.set_failure("attraction","closed"); affected=["Search attractions","Generate itinerary","Calculate budget"]
        elif event=="BUDGET_DECREASE": req.budget=Decimal(str(payload.get("budget",float(req.budget)*.8))); plan.budget=req.budget; affected=["Calculate budget","Generate alternatives"]
        elif event=="TRAVELLER_INCREASE": req.traveller_count=int(payload.get("traveller_count",req.traveller_count+1)); affected=["Search transport","Search hotels","Calculate budget"]
        else: affected=["Generate itinerary","Calculate budget"]
        # Remove generated plan and create a replacement plan while preserving request and history.
        plan.status=PlanStatus.CANCELLED; self.db.commit()
        try:
            new_plan=await self.run(req)
        finally:
            for tool in ("transport","hotel","weather","attraction"):
                travel_data_service.set_failure(tool,None)
        new_plan.current_version=plan.current_version
        new=self._snapshot(new_plan)
        self.db.add(ReplanningHistory(travel_plan_id=new_plan.id,previous_version=previous,new_version=new_plan.current_version,reason=reason or event_type,triggering_event={"event_type":event_type,"payload":payload},affected_tasks=affected,preserved_tasks=preserved,old_selection=old,new_selection=new,old_total=Decimal(str(old["total_cost"])),new_total=new_plan.total_cost,cost_difference=new_plan.total_cost-Decimal(str(old["total_cost"])),explanation=f"Replanned because of {event_type}. Only affected planning decisions were recomputed."))
        self._event(req.id,new_plan.id,"replanning_completed","Replanning Agent","Replan","COMPLETED",100,"Dynamic replanning completed",{"old_plan_id":plan.id,"new_plan_id":new_plan.id})
        self.db.commit(); return new_plan

    def add_feedback(self,user,plan,payload:FeedbackRequest):
        item=Feedback(user_id=user.id,travel_plan_id=plan.id,**payload.model_dump()); self.db.add(item)
        tags=[x.lower() for x in payload.preference_tags]
        suggestions=list(user.preference.pending_suggestions or [])
        mapping={"prefer trains":("preferred_transport_type","TRAIN"),"avoid early morning":("avoid_early_morning",True),"prefer indoor places":("tourist_interests",["Indoor activities"]),"prefer free attractions":("tourist_interests",["Free attractions"])}
        for tag,(field,value) in mapping.items():
            if tag in tags and not any(s.get("field")==field and s.get("status")=="PENDING" for s in suggestions):
                suggestions.append({"id":str(uuid4()),"field":field,"suggested_value":value,"reason":f"Suggested from feedback tag: {tag}","source":"feedback","status":"PENDING","created_at":datetime.now(timezone.utc).isoformat()})
        user.preference.pending_suggestions=suggestions
        self.db.commit(); self.db.refresh(item); return item

    def confirm(self,user,plan,action_type,decision,description=None):
        status=ConfirmationStatus(decision)
        item=ConfirmationRequest(travel_plan_id=plan.id,user_id=user.id,action_type=action_type,description=description or f"Approve {action_type}",payload={},status=status,responded_at=datetime.now(timezone.utc))
        self.db.add(item); plan.confirmation_status=status
        if status==ConfirmationStatus.APPROVED: plan.status=PlanStatus.CONFIRMED
        self.db.commit(); return item

    def book(self,user,plan,booking_types):
        if plan.confirmation_status!=ConfirmationStatus.APPROVED: raise ConflictError("Approve the booking confirmation first")
        bookings=[]
        for kind in booking_types:
            if kind.upper()=="TRANSPORT": provider=plan.selected_transport.provider; option_id=plan.selected_transport_id; amount=plan.selected_transport.total_price
            elif kind.upper()=="HOTEL": provider=plan.selected_hotel.name; option_id=plan.selected_hotel_id; amount=plan.selected_hotel.total_price
            else: continue
            b=SimulatedBooking(travel_plan_id=plan.id,user_id=user.id,booking_reference=f"SIM-{kind[:2].upper()}-{uuid4().hex[:10].upper()}",booking_type=kind.upper(),provider=provider,selected_option_id=option_id,amount=amount,currency=plan.currency,status=BookingStatus.CONFIRMED,confirmation_status=ConfirmationStatus.APPROVED,booking_details={"simulated":True})
            self.db.add(b); bookings.append(b)
        plan.status=PlanStatus.BOOKED; self.db.commit(); return bookings
