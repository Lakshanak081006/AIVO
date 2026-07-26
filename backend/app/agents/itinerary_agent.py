from __future__ import annotations
from datetime import datetime, time, timedelta
from typing import Any

def generate_itinerary(requirements: dict[str,Any], attractions: list[dict[str,Any]], weather: list[dict[str,Any]]) -> list[dict[str,Any]]:
    start=requirements["start_date"]; end=requirements["end_date"]
    if isinstance(start,str): start=datetime.fromisoformat(start).date()
    if isinstance(end,str): end=datetime.fromisoformat(end).date()
    heavy_dates={w["weather_date"] if isinstance(w["weather_date"],str) else w["weather_date"].isoformat() for w in weather if float(w.get("rain_probability") or 0)>=70}
    indoor=[a for a in attractions if a.get("environment_type")!="outdoor" and not a.get("closed_days")]
    outdoor=[a for a in attractions if a.get("environment_type")=="outdoor" and not a.get("closed_days")]
    days=[]; cursor=start; index=0
    while cursor<=end:
        heavy=cursor.isoformat() in heavy_dates
        pool=(indoor if heavy else attractions) or indoor or outdoor
        picks=[pool[(index+j)%len(pool)] for j in range(min(2,len(pool)))] if pool else []
        activities=[]
        if cursor==start:
            activities.append({"start_time":"08:00","end_time":"09:00","activity":"Arrival and hotel check-in","location":requirements["destination"],"activity_type":"Travel","environment_type":"indoor","travel_time_minutes":30,"estimated_cost":0,"weather_suitability":"Good","notes":"Keep identification and booking details ready"})
        else:
            activities.append({"start_time":"08:00","end_time":"09:00","activity":"Breakfast","location":"Hotel","activity_type":"Meal","environment_type":"indoor","travel_time_minutes":0,"estimated_cost":250,"weather_suitability":"Good","notes":None})
        slots=[("09:30","12:00"),("14:00","16:30")]
        for slot,a in zip(slots,picks):
            activities.append({"start_time":slot[0],"end_time":slot[1],"activity":f"Visit {a['name']}","location":a["address"],"activity_type":a["category"],"environment_type":a["environment_type"],"travel_time_minutes":30,"estimated_cost":float(a["entry_fee"]),"weather_suitability":"Good" if not heavy or a["environment_type"]!="outdoor" else "Poor","notes":"Indoor replacement selected due to rain" if heavy else None})
        activities.append({"start_time":"12:30","end_time":"13:30","activity":"Lunch","location":"Nearby restaurant","activity_type":"Meal","environment_type":"indoor","travel_time_minutes":15,"estimated_cost":350,"weather_suitability":"Good","notes":requirements.get("food_preference")})
        activities.append({"start_time":"17:00","end_time":"18:00","activity":"Rest and local exploration","location":"Near hotel","activity_type":"Leisure","environment_type":"mixed","travel_time_minutes":15,"estimated_cost":100,"weather_suitability":"Good","notes":None})
        activities.append({"start_time":"19:30","end_time":"20:30","activity":"Dinner","location":"Hotel or nearby restaurant","activity_type":"Meal","environment_type":"indoor","travel_time_minutes":10,"estimated_cost":400,"weather_suitability":"Good","notes":None})
        if cursor==end:
            activities.append({"start_time":"21:00","end_time":"22:00","activity":"Hotel checkout and departure preparation","location":"Hotel","activity_type":"Travel","environment_type":"indoor","travel_time_minutes":30,"estimated_cost":0,"weather_suitability":"Good","notes":"Confirm departure timing"})
        activities.sort(key=lambda x:x["start_time"])
        days.append({"day_number":index+1,"date":cursor.isoformat(),"title":f"Day {index+1} in {requirements['destination']}","activities":activities,"estimated_daily_cost":sum(float(a["estimated_cost"]) for a in activities)})
        cursor+=timedelta(days=1); index+=1
    return days
