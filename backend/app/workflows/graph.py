from __future__ import annotations
from app.agents.state import TravelAgentState
try:
    from langgraph.graph import END, START, StateGraph
except Exception:  # pragma: no cover
    END=START=StateGraph=None

def build_agent_graph():
    if StateGraph is None: return None
    graph=StateGraph(TravelAgentState)
    graph.add_node("requirements",lambda state:{**state,"current_agent":"Requirement Agent"})
    graph.add_node("planning",lambda state:{**state,"current_agent":"Planner Agent"})
    graph.add_node("parallel_search",lambda state:{**state,"current_agent":"Coordinator Agent"})
    graph.add_node("itinerary",lambda state:{**state,"current_agent":"Itinerary Agent"})
    graph.add_node("budget",lambda state:{**state,"current_agent":"Budget Agent"})
    graph.add_node("complete",lambda state:{**state,"current_agent":"Coordinator Agent","workflow_status":"COMPLETED"})
    graph.add_edge(START,"requirements"); graph.add_edge("requirements","planning"); graph.add_edge("planning","parallel_search")
    graph.add_edge("parallel_search","itinerary"); graph.add_edge("itinerary","budget"); graph.add_edge("budget","complete"); graph.add_edge("complete",END)
    return graph.compile()

def graph_description():
    return ["requirements","planning","parallel_search","itinerary","budget","complete"]
