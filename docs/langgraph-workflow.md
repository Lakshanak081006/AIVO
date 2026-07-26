# LangGraph Workflow

`backend/app/workflows/graph.py` defines the state graph:

```text
START -> requirements -> planning -> parallel_search
      -> itinerary -> budget -> complete -> END
```

The production workflow service adds database transactions, asynchronous tools, retry/fallback handling, plan persistence and detailed events. The shared typed state is in `backend/app/agents/state.py`.
