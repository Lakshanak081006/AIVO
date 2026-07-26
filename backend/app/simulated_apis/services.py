from __future__ import annotations
import asyncio
import json
import math
from datetime import date, timedelta
from pathlib import Path
from typing import Any
from app.core.config import settings

DATA_FILE = Path(__file__).resolve().parents[2] / "data" / "cities.json"

class SimulatedServiceError(RuntimeError):
    pass

class TravelDataService:
    def __init__(self) -> None:
        self.cities: dict[str, dict[str, Any]] = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        self.failures: dict[str, str] = {}

    def city_name(self, value: str) -> str:
        for city in self.cities:
            if city.lower() == value.strip().lower():
                return city
        raise SimulatedServiceError(f"Unsupported city: {value}")

    async def _delay_and_check(self, tool: str) -> None:
        await asyncio.sleep(0.02 if settings.DEMONSTRATION_MODE else 0.2)
        mode = self.failures.get(tool)
        if mode == "timeout":
            await asyncio.sleep(0.05)
            raise TimeoutError(f"{tool} service timed out")
        if mode == "error":
            raise SimulatedServiceError(f"{tool} service failed")

    def set_failure(self, tool: str, mode: str | None) -> None:
        if mode:
            self.failures[tool] = mode
        else:
            self.failures.pop(tool, None)

    def distance(self, source: str, destination: str) -> int:
        a = self.cities[self.city_name(source)]["distance_base"]
        b = self.cities[self.city_name(destination)]["distance_base"]
        return max(80, abs(int(a) - int(b)))

    async def search_transport(self, source: str, destination: str, start_date: date, travellers: int) -> list[dict[str, Any]]:
        await self._delay_and_check("transport")
        source, destination = self.city_name(source), self.city_name(destination)
        distance = self.distance(source, destination)
        templates = [
            ("TRAIN", "Indian Railways", 0.85, 58, 4.3, "Sleeper"),
            ("TRAIN", "Intercity Express", 1.15, 72, 4.6, "Chair Car"),
            ("BUS", "State Express", 1.05, 50, 4.1, "AC Seater"),
            ("BUS", "GreenLine Travels", 1.35, 62, 4.5, "AC Sleeper"),
            ("FLIGHT", "SkyConnect", 4.5, 620, 4.4, "Economy"),
        ]
        results=[]
        for index,(kind,provider,mult,speed,rating,booking_class) in enumerate(templates,1):
            duration=max(75,int(distance/speed*60)+(45 if kind=="FLIGHT" else 20))
            base=max(250,round(distance*mult))
            dep_hour=[6,9,13,17,21][index-1]
            arrival_total=dep_hour*60+duration
            results.append({
                "external_reference":f"{kind[:2]}-{source[:3].upper()}-{destination[:3].upper()}-{index}",
                "provider":provider,"transport_type":kind,"service_number":f"{1000+distance+index}",
                "source":source,"destination":destination,"departure_date":start_date.isoformat(),
                "departure_time":f"{dep_hour:02d}:00","arrival_date":(start_date+timedelta(days=arrival_total//1440)).isoformat(),
                "arrival_time":f"{(arrival_total//60)%24:02d}:{arrival_total%60:02d}","duration_minutes":duration,
                "price_per_person":base,"traveller_count":travellers,"total_price":base*travellers,
                "available":not (self.failures.get("transport") == "cancelled" and index==1),"available_seats":18-index,
                "number_of_stops":0 if kind!="FLIGHT" else 0,"rating":rating,
                "cancellation_policy":"Free cancellation up to 24 hours before departure","booking_class":booking_class,
            })
        if self.failures.get("transport") == "empty": return []
        return results

    async def search_hotels(self, city: str, nights: int, travellers: int) -> list[dict[str, Any]]:
        await self._delay_and_check("hotel")
        city=self.city_name(city); rooms=max(1,math.ceil(travellers/2))
        base=1200 + int(self.cities[city]["distance_base"] % 900)
        results=[]
        for idx,(label,mult,rating,distance,amenities) in enumerate([
            ("Comfort Inn",1.0,3.7,4.5,["Wi-Fi","Breakfast"]),
            ("City Residency",1.35,4.1,2.4,["Wi-Fi","Breakfast","Parking"]),
            ("Grand Plaza",1.9,4.5,1.2,["Wi-Fi","Pool","Gym","Breakfast"]),
            ("Traveller Hostel",0.65,3.5,5.2,["Wi-Fi","Shared kitchen"]),
        ],1):
            price=round(base*mult)
            results.append({"external_reference":f"HT-{city[:3].upper()}-{idx}","name":f"{city} {label}","city":city,
              "address":f"Central {city}","latitude":11.0+idx/100,"longitude":77.0+idx/100,
              "price_per_night":price,"number_of_nights":max(1,nights),"number_of_rooms":rooms,
              "total_price":price*max(1,nights)*rooms,"rating":rating,"room_type":"Standard",
              "amenities":amenities,"available":not (self.failures.get("hotel")=="unavailable" and idx==1),
              "cancellation_policy":"Free cancellation until 6 PM one day before check-in",
              "distance_from_city_centre":distance,"check_in_time":"12:00","check_out_time":"10:00"})
        if self.failures.get("hotel") == "empty": return []
        return results

    async def search_attractions(self, city: str) -> list[dict[str, Any]]:
        await self._delay_and_check("attraction")
        city=self.city_name(city); results=[]
        for idx,item in enumerate(self.cities[city]["attractions"],1):
            name,category,environment,fee,rating=item
            results.append({"external_reference":f"AT-{city[:3].upper()}-{idx}","name":name,"city":city,"category":category,
              "description":f"Popular {category.lower()} attraction in {city}","address":f"{name}, {city}",
              "latitude":11.1+idx/100,"longitude":77.1+idx/100,"entry_fee":fee,"opening_time":"09:00",
              "closing_time":"18:00","average_visit_duration_minutes":120,"rating":rating,
              "environment_type":environment,"closed_days":[],"distance_from_hotel":1.0+idx*0.8,
              "weather_suitable":environment!="outdoor" or self.failures.get("weather")!="heavy_rain","selected":idx<=3})
        if self.failures.get("attraction") == "closed" and results:
            results[0]["closed_days"]=[date.today().strftime("%A")]
            results[0]["selected"]=False
        return results

    async def get_weather(self, city: str, start_date: date, end_date: date) -> list[dict[str, Any]]:
        await self._delay_and_check("weather")
        city=self.city_name(city); days=(end_date-start_date).days+1; results=[]
        for offset in range(max(1,days)):
            d=start_date+timedelta(days=offset)
            heavy=self.failures.get("weather")=="heavy_rain" or ((d.day+len(city))%7==0)
            results.append({"city":city,"weather_date":d.isoformat(),"condition":"Heavy rain" if heavy else "Partly cloudy",
              "minimum_temperature":23.0,"maximum_temperature":31.0,"rain_probability":90 if heavy else 25,
              "wind_speed":18 if heavy else 9,"weather_alert":"Heavy rain warning" if heavy else None,
              "outdoor_suitability":"Poor" if heavy else "Good"})
        return results

    async def route(self, source: str, destination: str) -> dict[str, Any]:
        await self._delay_and_check("route")
        distance=self.distance(source,destination)
        return {"source":self.city_name(source),"destination":self.city_name(destination),"distance_km":distance,"road_minutes":int(distance/48*60)}

    def city_costs(self, city: str) -> dict[str,int]:
        data=self.cities[self.city_name(city)]
        return {"food_daily":int(data["food_daily"]),"local_daily":int(data["local_daily"])}

travel_data_service = TravelDataService()
