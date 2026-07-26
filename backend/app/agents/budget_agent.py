from __future__ import annotations
from typing import Any
from app.simulated_apis.services import travel_data_service

def calculate_budget(requirements:dict[str,Any], transport:dict[str,Any], hotel:dict[str,Any], itinerary:list[dict[str,Any]]) -> dict[str,Any]:
    travellers=int(requirements["traveller_count"]); days=int(requirements["trip_duration_days"])
    costs=travel_data_service.city_costs(requirements["destination"])
    attraction=sum(float(a["estimated_cost"]) for d in itinerary for a in d["activities"] if a["activity_type"] not in {"Meal","Travel","Leisure"})
    transport_cost=float(transport["total_price"]); hotel_cost=float(hotel["total_price"])
    food=costs["food_daily"]*days*travellers; local=costs["local_daily"]*days
    subtotal=transport_cost+hotel_cost+food+local+attraction
    taxes=round((transport_cost+hotel_cost)*.05,2); reserve=round(subtotal*.05,2); total=round(subtotal+taxes+reserve,2)
    budget=float(requirements["budget"]); remaining=round(budget-total,2)
    return {"currency":requirements.get("currency","INR"),"transport_cost":transport_cost,"hotel_cost":hotel_cost,
      "food_cost":food,"local_transport_cost":local,"attraction_cost":attraction,"taxes":taxes,"emergency_reserve":reserve,
      "other_expenses":0,"total_cost":total,"user_budget":budget,"remaining_budget":max(0,remaining),
      "exceeded_amount":max(0,-remaining),"within_budget":remaining>=0}

def cheaper_alternative(requirements, transports, hotels, itinerary, original):
    cheapest_t=min(transports,key=lambda x:float(x["total_price"])); cheapest_h=min(hotels,key=lambda x:float(x["total_price"]));
    free_itinerary=[]
    for day in itinerary:
        clone={**day,"activities":[{**a,"estimated_cost":0 if a["activity_type"] not in {"Meal","Travel","Leisure"} else a["estimated_cost"],"notes":("Replaced with a free activity" if a["activity_type"] not in {"Meal","Travel","Leisure"} else a.get("notes"))} for a in day["activities"]]}
        free_itinerary.append(clone)
    revised=calculate_budget(requirements,cheapest_t,cheapest_h,free_itinerary)
    return {"original_total":original["total_cost"],"revised_total":revised["total_cost"],"savings":round(original["total_cost"]-revised["total_cost"],2),
      "selected_transport":cheapest_t,"selected_hotel":cheapest_h,"budget":revised,"itinerary":free_itinerary,
      "changes":["Selected the cheapest available transport","Selected the cheapest available hotel","Replaced paid attractions with free activities"],
      "trade_offs":["Longer travel time may be required","Hotel may be farther from the city centre","Fewer paid attractions"]}
