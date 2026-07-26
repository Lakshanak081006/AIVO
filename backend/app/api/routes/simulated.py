from __future__ import annotations
import json
from datetime import date
from pathlib import Path
from fastapi import APIRouter, Query
from app.simulated_apis.services import travel_data_service
router=APIRouter(prefix="/simulated",tags=["Simulated APIs"])
@router.get("/transport/search")
async def transport(source:str,destination:str,start_date:date=date.today(),travellers:int=1): return {"data":await travel_data_service.search_transport(source,destination,start_date,travellers)}
@router.get("/hotels/search")
async def hotels(city:str,nights:int=1,travellers:int=1): return {"data":await travel_data_service.search_hotels(city,nights,travellers)}
@router.get("/attractions/search")
async def attractions(city:str): return {"data":await travel_data_service.search_attractions(city)}
@router.get("/weather")
async def weather(city:str,start_date:date=date.today(),end_date:date=date.today()): return {"data":await travel_data_service.get_weather(city,start_date,end_date)}
@router.get("/routes")
async def routes(source:str,destination:str): return {"data":await travel_data_service.route(source,destination)}
