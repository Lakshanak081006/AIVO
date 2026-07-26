# Database Design

The schema contains 21 core models: users, user_preferences, travel_requests, travel_plans, plan_versions, agent_tasks, task_dependencies, transport_options, hotel_options, attractions, weather_records, itinerary_days, itinerary_activities, budget_breakdowns, action_logs, feedback, agent_memory, replanning_history, simulated_bookings, confirmation_requests and workflow_events.

SQLite is the local default. JSON columns automatically use PostgreSQL JSONB when PostgreSQL is selected.
