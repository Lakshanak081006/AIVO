from __future__ import annotations


def final_summary(language: str, *, days: int, source: str, destination: str, transport: str, provider: str, hotel: str, currency: str, total: float, within_budget: bool, exceeded: float, alternatives: bool) -> str:
    language = (language or "English").title()
    if language == "Tamil":
        budget_text = "பட்ஜெட்டிற்குள் உள்ளது" if within_budget else f"பட்ஜெட்டை {currency} {exceeded:.2f} மீறுகிறது"
        extra = " குறைந்த செலவிலான மாற்றுத் திட்டமும் வழங்கப்பட்டுள்ளது." if alternatives else ""
        return f"{source} இலிருந்து {destination} வரை {days} நாள் பயணம் திட்டமிடப்பட்டது. {provider} {transport} மற்றும் {hotel} பரிந்துரைக்கப்பட்டுள்ளன. மதிப்பிடப்பட்ட மொத்த செலவு {currency} {total:.2f}; இது {budget_text}.{extra}"
    if language == "Hindi":
        budget_text = "बजट के भीतर है" if within_budget else f"बजट से {currency} {exceeded:.2f} अधिक है"
        extra = " कम लागत वाला वैकल्पिक प्लान भी उपलब्ध है।" if alternatives else ""
        return f"{source} से {destination} तक {days} दिन की यात्रा बनाई गई। {provider} {transport} और {hotel} की सिफारिश की गई है। अनुमानित कुल लागत {currency} {total:.2f} है और यह {budget_text}।{extra}"
    status = "within budget" if within_budget else f"over budget by {currency} {exceeded:.2f}"
    extra = " A cheaper alternative is available." if alternatives else ""
    return f"Planned a {days}-day trip from {source} to {destination}. Recommended {provider} {transport.lower()} and {hotel}. Estimated total: {currency} {total:.2f}, which is {status}.{extra}"
