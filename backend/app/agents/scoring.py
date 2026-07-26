from __future__ import annotations

def _minmax(values, reverse=False):
    lo,hi=min(values),max(values)
    if hi==lo: return [1.0]*len(values)
    normalized=[(v-lo)/(hi-lo) for v in values]
    return [1-n for n in normalized] if reverse else normalized

def rank_transport(items, preference=None):
    available=[x for x in items if x.get("available")]
    if not available: return []
    price=_minmax([float(x["total_price"]) for x in available],True)
    duration=_minmax([float(x["duration_minutes"]) for x in available],True)
    rating=_minmax([float(x.get("rating") or 0) for x in available])
    for i,x in enumerate(available):
        pref=1.0 if preference and x["transport_type"].upper()==preference.upper() else 0.5
        flexible=1.0 if "free" in (x.get("cancellation_policy") or "").lower() else 0.5
        x["normalized_score"]=round(price[i]*.40+duration[i]*.25+pref*.20+rating[i]*.10+flexible*.05,4)
    available.sort(key=lambda x:x["normalized_score"],reverse=True)
    available[0]["recommendation_type"]="BEST_OVERALL"
    cheapest=min(available,key=lambda x:x["total_price"])
    cheapest["recommendation_type"]=(cheapest.get("recommendation_type")+",CHEAPEST") if cheapest.get("recommendation_type") else "CHEAPEST"
    return available

def rank_hotels(items):
    available=[x for x in items if x.get("available")]
    if not available: return []
    price=_minmax([float(x["total_price"]) for x in available],True)
    rating=_minmax([float(x.get("rating") or 0) for x in available])
    distance=_minmax([float(x.get("distance_from_city_centre") or 99) for x in available],True)
    amen=_minmax([len(x.get("amenities") or []) for x in available])
    for i,x in enumerate(available):
        flexible=1.0 if "free" in (x.get("cancellation_policy") or "").lower() else .5
        x["normalized_score"]=round(price[i]*.35+rating[i]*.25+distance[i]*.20+amen[i]*.10+flexible*.10,4)
    available.sort(key=lambda x:x["normalized_score"],reverse=True)
    available[0]["recommendation_type"]="BEST_OVERALL"
    return available
