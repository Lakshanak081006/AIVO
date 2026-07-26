from __future__ import annotations
import re
from datetime import date, timedelta
from typing import Any
from app.simulated_apis.services import travel_data_service

NUMBER_WORDS={"one":1,"two":2,"three":3,"four":4,"five":5,"six":6,"ஒரு":1,"இரண்டு":2,"மூன்று":3,"एक":1,"दो":2,"तीन":3}

def detect_language(text: str) -> str:
    if re.search(r"[\u0B80-\u0BFF]", text): return "Tamil"
    if re.search(r"[\u0900-\u097F]", text): return "Hindi"
    return "English"

def _next_weekend(today: date) -> tuple[date,date]:
    days=(5-today.weekday())%7
    if days==0: days=7
    start=today+timedelta(days=days)
    return start,start+timedelta(days=1)

def extract_requirements(instruction: str, response_language: str | None=None, today: date | None=None) -> dict[str,Any]:
    text=instruction.strip(); lower=text.lower(); today=today or date.today(); language=detect_language(text)
    cities=list(travel_data_service.cities)
    aliases={
      "கோயம்புத்தூர்":"Coimbatore","கோயம்புத்தூர":"Coimbatore","கோவை":"Coimbatore","சென்னை":"Chennai","பெங்களூரு":"Bengaluru","கொச்சி":"Kochi","ஹைதராபாத்":"Hyderabad","மைசூர்":"Mysuru","மதுரை":"Madurai","ஊட்டி":"Ooty","புதுச்சேரி":"Pondicherry","மும்பை":"Mumbai","டெல்லி":"Delhi",
      "कोयंबटूर":"Coimbatore","चेन्नई":"Chennai","बेंगलुरु":"Bengaluru","कोच्चि":"Kochi","हैदराबाद":"Hyderabad","मैसूर":"Mysuru","मदुरै":"Madurai","ऊटी":"Ooty","पुडुचेरी":"Pondicherry","मुंबई":"Mumbai","दिल्ली":"Delhi"
    }
    mentioned=[c for c in cities if c.lower() in lower]
    for alias,canonical in aliases.items():
        if alias in text and canonical not in mentioned: mentioned.append(canonical)
    source=destination=None
    match=re.search(r"from\s+([a-zA-Z ]+?)\s+to\s+([a-zA-Z ]+?)(?:\s+for|\s+on|\s+under|\s+within|\s+next|\s+this|$)", text, re.I)
    if match:
        source=next((c for c in cities if c.lower() in match.group(1).lower()),None)
        destination=next((c for c in cities if c.lower() in match.group(2).lower()),None)
    if not source and len(mentioned)>=2: source,destination=mentioned[0],mentioned[1]
    if not destination and len(mentioned)==1: destination=mentioned[0]
    # common Tamil city pair wording still contains transliterated city names in demos
    duration=None
    dm=re.search(r"(?:for\s+)?(\d+|one|two|three|four|five)[ -]?(?:day|days)",lower)
    if dm: duration=int(dm.group(1)) if dm.group(1).isdigit() else NUMBER_WORDS.get(dm.group(1))
    tm=re.search(r"(\d+)\s*(?:நாள்|दिन)",text)
    if tm: duration=int(tm.group(1))
    if duration is None:
        for word,number in NUMBER_WORDS.items():
            if re.search(re.escape(word)+r"\s*(?:நாள்|दिन)",text,re.I): duration=number; break
    start=end=None
    iso=re.findall(r"\b(20\d{2}-\d{2}-\d{2})\b",text)
    if iso:
        start=date.fromisoformat(iso[0]); end=date.fromisoformat(iso[1]) if len(iso)>1 else start+timedelta(days=(duration or 1)-1)
    elif "next weekend" in lower or "அடுத்த வார இறுதி" in text or "अगले सप्ताहांत" in text:
        start,end=_next_weekend(today)
    elif "this weekend" in lower:
        days=(5-today.weekday())%7; start=today+timedelta(days=days); end=start+timedelta(days=1)
    elif "tomorrow" in lower:
        start=today+timedelta(days=1); end=start+timedelta(days=(duration or 1)-1)
    elif "next friday" in lower:
        days=(4-today.weekday())%7 or 7; start=today+timedelta(days=days); end=start+timedelta(days=(duration or 1)-1)
    if start and not end: end=start+timedelta(days=(duration or 1)-1)
    if start and end: duration=(end-start).days+1
    travellers=None
    mt=re.search(r"(?:for\s+)?(\d+|one|two|three|four|five)\s+(?:people|persons|travellers|travelers)",lower)
    if mt: travellers=int(mt.group(1)) if mt.group(1).isdigit() else NUMBER_WORDS.get(mt.group(1))
    mt2=re.search(r"(\d+)\s*(?:பேர்|பேர|लोग)",text)
    if mt2: travellers=int(mt2.group(1))
    if travellers is None:
        for word,number in NUMBER_WORDS.items():
            if re.search(re.escape(word)+r"\s*(?:பேர்|பேர|लोग)",text,re.I): travellers=number; break
    budget=None; currency="INR"
    bm=re.search(r"(?:₹|rs\.?|inr)\s*([\d,]+)",lower)
    if not bm: bm=re.search(r"(?:under|within|budget(?:\s+of)?)\s*₹?\s*([\d,]+)",lower)
    if bm: budget=float(bm.group(1).replace(",",""))
    usd=re.search(r"\$\s*([\d,]+)",text)
    if usd: budget=float(usd.group(1).replace(",","")); currency="USD"
    transport=next((x.upper() for x in ["train","bus","flight","car"] if x in lower),None)
    interests=[]
    for key,label in [("histor","Historical"),("museum","Museums"),("beach","Beaches"),("shopping","Shopping"),("park","Parks"),("indoor","Indoor activities")]:
        if key in lower: interests.append(label)
    hotel_pref="Budget" if any(x in lower for x in ["affordable","cheap","budget hotel"]) else None
    special=[]
    if "rain" in lower: special.append("Prefer indoor activities during rain")
    return {"source":source,"destination":destination,"start_date":start,"end_date":end,"trip_duration_days":duration,
      "traveller_count":travellers,"budget":budget,"currency":currency,"transport_preference":transport,
      "hotel_preference":hotel_pref,"minimum_hotel_rating":None,"food_preference":"Vegetarian" if "vegetarian" in lower else None,
      "tourist_interests":interests,"special_requirements":special,"detected_language":language,
      "response_language":response_language or language}

def missing_fields(data: dict[str,Any]) -> list[str]:
    missing=[]
    for field in ["source","destination","start_date","end_date","traveller_count","budget"]:
        if data.get(field) in (None,""): missing.append(field)
    return missing

def clarification_question(fields: list[str]) -> str:
    labels={"source":"starting city","destination":"destination","start_date":"travel dates","end_date":"travel dates","traveller_count":"number of travellers","budget":"total budget"}
    unique=[]
    for f in fields:
        label=labels[f]
        if label not in unique: unique.append(label)
    return "Please provide the " + ", ".join(unique) + "."
