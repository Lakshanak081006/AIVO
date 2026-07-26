-- Autonomous Personal Assistant - Phase 1 PostgreSQL schema
-- Generated from SQLAlchemy metadata.
-- Recommended setup: cd backend && alembic upgrade head


CREATE TABLE users (
	id SERIAL NOT NULL, 
	full_name VARCHAR(100) NOT NULL, 
	email VARCHAR(320) NOT NULL, 
	password_hash VARCHAR(255) NOT NULL, 
	preferred_language VARCHAR(20) NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
);


CREATE TABLE agent_memory (
	id SERIAL NOT NULL, 
	user_id INTEGER NOT NULL, 
	memory_key VARCHAR(150) NOT NULL, 
	memory_value JSONB NOT NULL, 
	approved BOOLEAN NOT NULL, 
	source VARCHAR(100), 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_agent_memory_user_key UNIQUE (user_id, memory_key), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);


CREATE TABLE travel_requests (
	id SERIAL NOT NULL, 
	user_id INTEGER NOT NULL, 
	original_instruction TEXT NOT NULL, 
	detected_language VARCHAR(20), 
	response_language VARCHAR(20) NOT NULL, 
	source VARCHAR(120), 
	destination VARCHAR(120), 
	start_date DATE, 
	end_date DATE, 
	trip_duration_days INTEGER, 
	traveller_count INTEGER NOT NULL, 
	budget NUMERIC(12, 2) NOT NULL, 
	currency VARCHAR(3) NOT NULL, 
	transport_preference VARCHAR(50), 
	hotel_preference VARCHAR(100), 
	minimum_hotel_rating FLOAT, 
	food_preference VARCHAR(100), 
	tourist_interests JSONB NOT NULL, 
	special_requirements JSONB NOT NULL, 
	extracted_requirements JSONB NOT NULL, 
	missing_fields JSONB NOT NULL, 
	clarification_required BOOLEAN NOT NULL, 
	clarification_question TEXT, 
	clarification_answer TEXT, 
	workflow_status VARCHAR(25) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_travel_requests_travellers_positive CHECK (traveller_count > 0), 
	CONSTRAINT ck_travel_requests_budget_nonnegative CHECK (budget >= 0), 
	CONSTRAINT ck_travel_requests_date_order CHECK (end_date IS NULL OR start_date IS NULL OR end_date >= start_date), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);


CREATE TABLE user_preferences (
	id SERIAL NOT NULL, 
	user_id INTEGER NOT NULL, 
	preferred_language VARCHAR(20) NOT NULL, 
	preferred_currency VARCHAR(3) NOT NULL, 
	preferred_transport_type VARCHAR(15), 
	preferred_departure_time TIME WITHOUT TIME ZONE, 
	maximum_travel_duration INTEGER, 
	preferred_hotel_category VARCHAR(50), 
	minimum_hotel_rating FLOAT, 
	maximum_hotel_distance FLOAT, 
	preferred_food_type VARCHAR(100), 
	tourist_interests JSONB NOT NULL, 
	avoid_early_morning BOOLEAN NOT NULL, 
	avoid_late_night BOOLEAN NOT NULL, 
	accessibility_requirements JSONB NOT NULL, 
	pending_suggestions JSONB NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_user_preferences_hotel_rating CHECK (minimum_hotel_rating IS NULL OR (minimum_hotel_rating >= 0 AND minimum_hotel_rating <= 5)), 
	CONSTRAINT ck_user_preferences_hotel_distance CHECK (maximum_hotel_distance IS NULL OR maximum_hotel_distance >= 0), 
	CONSTRAINT ck_user_preferences_travel_duration CHECK (maximum_travel_duration IS NULL OR maximum_travel_duration > 0), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);


CREATE TABLE travel_plans (
	id SERIAL NOT NULL, 
	user_id INTEGER NOT NULL, 
	travel_request_id INTEGER NOT NULL, 
	title VARCHAR(200) NOT NULL, 
	status VARCHAR(10) NOT NULL, 
	selected_transport_id INTEGER, 
	selected_hotel_id INTEGER, 
	total_cost NUMERIC(12, 2) NOT NULL, 
	currency VARCHAR(3) NOT NULL, 
	budget NUMERIC(12, 2) NOT NULL, 
	remaining_budget NUMERIC(12, 2) NOT NULL, 
	budget_exceeded BOOLEAN NOT NULL, 
	current_version INTEGER NOT NULL, 
	final_summary TEXT, 
	confirmation_status VARCHAR(9) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_travel_plans_total_nonnegative CHECK (total_cost >= 0), 
	CONSTRAINT ck_travel_plans_budget_nonnegative CHECK (budget >= 0), 
	CONSTRAINT ck_travel_plans_version_positive CHECK (current_version > 0), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
	FOREIGN KEY(travel_request_id) REFERENCES travel_requests (id) ON DELETE CASCADE
);


CREATE TABLE agent_tasks (
	id SERIAL NOT NULL, 
	task_uuid VARCHAR(36) NOT NULL, 
	travel_request_id INTEGER NOT NULL, 
	travel_plan_id INTEGER, 
	task_name VARCHAR(150) NOT NULL, 
	description TEXT, 
	agent_name VARCHAR(100) NOT NULL, 
	priority VARCHAR(8) NOT NULL, 
	status VARCHAR(11) NOT NULL, 
	can_run_in_parallel BOOLEAN NOT NULL, 
	weight INTEGER NOT NULL, 
	retry_count INTEGER NOT NULL, 
	maximum_retries INTEGER NOT NULL, 
	input_data JSONB NOT NULL, 
	output_data JSONB NOT NULL, 
	error_message TEXT, 
	started_at TIMESTAMP WITH TIME ZONE, 
	completed_at TIMESTAMP WITH TIME ZONE, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_agent_tasks_weight_positive CHECK (weight > 0), 
	CONSTRAINT ck_agent_tasks_retry_nonnegative CHECK (retry_count >= 0), 
	CONSTRAINT ck_agent_tasks_max_retry_nonnegative CHECK (maximum_retries >= 0), 
	FOREIGN KEY(travel_request_id) REFERENCES travel_requests (id) ON DELETE CASCADE, 
	FOREIGN KEY(travel_plan_id) REFERENCES travel_plans (id) ON DELETE CASCADE
);


CREATE TABLE attractions (
	id SERIAL NOT NULL, 
	travel_plan_id INTEGER NOT NULL, 
	external_reference VARCHAR(100) NOT NULL, 
	name VARCHAR(180) NOT NULL, 
	city VARCHAR(120) NOT NULL, 
	category VARCHAR(80) NOT NULL, 
	description TEXT, 
	address TEXT NOT NULL, 
	latitude FLOAT, 
	longitude FLOAT, 
	entry_fee NUMERIC(10, 2) NOT NULL, 
	opening_time TIME WITHOUT TIME ZONE, 
	closing_time TIME WITHOUT TIME ZONE, 
	average_visit_duration_minutes INTEGER NOT NULL, 
	rating FLOAT, 
	environment_type VARCHAR(20) NOT NULL, 
	closed_days JSONB NOT NULL, 
	distance_from_hotel FLOAT, 
	weather_suitable BOOLEAN NOT NULL, 
	selected BOOLEAN NOT NULL, 
	raw_data JSONB NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_attraction_fee_nonnegative CHECK (entry_fee >= 0), 
	CONSTRAINT ck_attraction_duration_positive CHECK (average_visit_duration_minutes > 0), 
	CONSTRAINT ck_attraction_rating CHECK (rating IS NULL OR (rating >= 0 AND rating <= 5)), 
	FOREIGN KEY(travel_plan_id) REFERENCES travel_plans (id) ON DELETE CASCADE
);


CREATE TABLE budget_breakdowns (
	id SERIAL NOT NULL, 
	travel_plan_id INTEGER NOT NULL, 
	transport_cost NUMERIC(12, 2) NOT NULL, 
	hotel_cost NUMERIC(12, 2) NOT NULL, 
	food_cost NUMERIC(12, 2) NOT NULL, 
	local_transport_cost NUMERIC(12, 2) NOT NULL, 
	attraction_cost NUMERIC(12, 2) NOT NULL, 
	taxes NUMERIC(12, 2) NOT NULL, 
	emergency_reserve NUMERIC(12, 2) NOT NULL, 
	other_expenses NUMERIC(12, 2) NOT NULL, 
	total_cost NUMERIC(12, 2) NOT NULL, 
	user_budget NUMERIC(12, 2) NOT NULL, 
	remaining_budget NUMERIC(12, 2) NOT NULL, 
	exceeded_amount NUMERIC(12, 2) NOT NULL, 
	within_budget BOOLEAN NOT NULL, 
	currency VARCHAR(3) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_budget_transport_nonnegative CHECK (transport_cost >= 0), 
	CONSTRAINT ck_budget_hotel_nonnegative CHECK (hotel_cost >= 0), 
	CONSTRAINT ck_budget_food_nonnegative CHECK (food_cost >= 0), 
	CONSTRAINT ck_budget_local_nonnegative CHECK (local_transport_cost >= 0), 
	CONSTRAINT ck_budget_attraction_nonnegative CHECK (attraction_cost >= 0), 
	CONSTRAINT ck_budget_taxes_nonnegative CHECK (taxes >= 0), 
	CONSTRAINT ck_budget_reserve_nonnegative CHECK (emergency_reserve >= 0), 
	CONSTRAINT ck_budget_other_nonnegative CHECK (other_expenses >= 0), 
	CONSTRAINT ck_budget_total_nonnegative CHECK (total_cost >= 0), 
	CONSTRAINT ck_budget_user_nonnegative CHECK (user_budget >= 0), 
	CONSTRAINT ck_budget_exceeded_nonnegative CHECK (exceeded_amount >= 0), 
	FOREIGN KEY(travel_plan_id) REFERENCES travel_plans (id) ON DELETE CASCADE
);


CREATE TABLE confirmation_requests (
	id SERIAL NOT NULL, 
	travel_plan_id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	action_type VARCHAR(80) NOT NULL, 
	description TEXT NOT NULL, 
	payload JSONB NOT NULL, 
	status VARCHAR(9) NOT NULL, 
	expires_at TIMESTAMP WITH TIME ZONE, 
	responded_at TIMESTAMP WITH TIME ZONE, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(travel_plan_id) REFERENCES travel_plans (id) ON DELETE CASCADE, 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);


CREATE TABLE feedback (
	id SERIAL NOT NULL, 
	user_id INTEGER NOT NULL, 
	travel_plan_id INTEGER NOT NULL, 
	overall_rating INTEGER NOT NULL, 
	transport_rating INTEGER, 
	hotel_rating INTEGER, 
	itinerary_rating INTEGER, 
	budget_rating INTEGER, 
	recommendation_rating INTEGER, 
	text_feedback TEXT, 
	preference_tags JSONB NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_feedback_overall_rating CHECK (overall_rating BETWEEN 1 AND 5), 
	CONSTRAINT ck_feedback_transport_rating CHECK (transport_rating IS NULL OR transport_rating BETWEEN 1 AND 5), 
	CONSTRAINT ck_feedback_hotel_rating CHECK (hotel_rating IS NULL OR hotel_rating BETWEEN 1 AND 5), 
	CONSTRAINT ck_feedback_itinerary_rating CHECK (itinerary_rating IS NULL OR itinerary_rating BETWEEN 1 AND 5), 
	CONSTRAINT ck_feedback_budget_rating CHECK (budget_rating IS NULL OR budget_rating BETWEEN 1 AND 5), 
	CONSTRAINT ck_feedback_recommendation_rating CHECK (recommendation_rating IS NULL OR recommendation_rating BETWEEN 1 AND 5), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
	FOREIGN KEY(travel_plan_id) REFERENCES travel_plans (id) ON DELETE CASCADE
);


CREATE TABLE hotel_options (
	id SERIAL NOT NULL, 
	travel_plan_id INTEGER NOT NULL, 
	external_reference VARCHAR(100) NOT NULL, 
	name VARCHAR(180) NOT NULL, 
	city VARCHAR(120) NOT NULL, 
	address TEXT NOT NULL, 
	latitude FLOAT, 
	longitude FLOAT, 
	price_per_night NUMERIC(12, 2) NOT NULL, 
	number_of_nights INTEGER NOT NULL, 
	number_of_rooms INTEGER NOT NULL, 
	total_price NUMERIC(12, 2) NOT NULL, 
	rating FLOAT, 
	room_type VARCHAR(80), 
	amenities JSONB NOT NULL, 
	available BOOLEAN NOT NULL, 
	cancellation_policy TEXT, 
	distance_from_city_centre FLOAT, 
	check_in_time TIME WITHOUT TIME ZONE, 
	check_out_time TIME WITHOUT TIME ZONE, 
	normalized_score FLOAT, 
	recommendation_type VARCHAR(50), 
	raw_data JSONB NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_hotel_price_nonnegative CHECK (price_per_night >= 0), 
	CONSTRAINT ck_hotel_nights_positive CHECK (number_of_nights > 0), 
	CONSTRAINT ck_hotel_rooms_positive CHECK (number_of_rooms > 0), 
	CONSTRAINT ck_hotel_total_nonnegative CHECK (total_price >= 0), 
	CONSTRAINT ck_hotel_rating CHECK (rating IS NULL OR (rating >= 0 AND rating <= 5)), 
	FOREIGN KEY(travel_plan_id) REFERENCES travel_plans (id) ON DELETE CASCADE
);


CREATE TABLE itinerary_days (
	id SERIAL NOT NULL, 
	travel_plan_id INTEGER NOT NULL, 
	day_number INTEGER NOT NULL, 
	itinerary_date DATE NOT NULL, 
	title VARCHAR(180), 
	estimated_daily_cost NUMERIC(12, 2) NOT NULL, 
	notes TEXT, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_itinerary_day_number UNIQUE (travel_plan_id, day_number), 
	CONSTRAINT ck_itinerary_day_positive CHECK (day_number > 0), 
	CONSTRAINT ck_itinerary_daily_cost_nonnegative CHECK (estimated_daily_cost >= 0), 
	FOREIGN KEY(travel_plan_id) REFERENCES travel_plans (id) ON DELETE CASCADE
);


CREATE TABLE plan_versions (
	id SERIAL NOT NULL, 
	travel_plan_id INTEGER NOT NULL, 
	version_number INTEGER NOT NULL, 
	reason TEXT, 
	snapshot JSONB NOT NULL, 
	total_cost NUMERIC(12, 2) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_plan_version UNIQUE (travel_plan_id, version_number), 
	CONSTRAINT ck_plan_versions_number_positive CHECK (version_number > 0), 
	CONSTRAINT ck_plan_versions_total_nonnegative CHECK (total_cost >= 0), 
	FOREIGN KEY(travel_plan_id) REFERENCES travel_plans (id) ON DELETE CASCADE
);


CREATE TABLE replanning_history (
	id SERIAL NOT NULL, 
	travel_plan_id INTEGER NOT NULL, 
	previous_version INTEGER NOT NULL, 
	new_version INTEGER NOT NULL, 
	reason TEXT NOT NULL, 
	triggering_event JSONB NOT NULL, 
	affected_tasks JSONB NOT NULL, 
	preserved_tasks JSONB NOT NULL, 
	old_selection JSONB NOT NULL, 
	new_selection JSONB NOT NULL, 
	old_total NUMERIC(12, 2) NOT NULL, 
	new_total NUMERIC(12, 2) NOT NULL, 
	cost_difference NUMERIC(12, 2) NOT NULL, 
	explanation TEXT, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_replanning_previous_positive CHECK (previous_version > 0), 
	CONSTRAINT ck_replanning_version_order CHECK (new_version > previous_version), 
	FOREIGN KEY(travel_plan_id) REFERENCES travel_plans (id) ON DELETE CASCADE
);


CREATE TABLE simulated_bookings (
	id SERIAL NOT NULL, 
	travel_plan_id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	booking_reference VARCHAR(80) NOT NULL, 
	booking_type VARCHAR(50) NOT NULL, 
	provider VARCHAR(120) NOT NULL, 
	selected_option_id INTEGER, 
	amount NUMERIC(12, 2) NOT NULL, 
	currency VARCHAR(3) NOT NULL, 
	status VARCHAR(9) NOT NULL, 
	confirmation_status VARCHAR(9) NOT NULL, 
	booking_details JSONB NOT NULL, 
	cancelled_at TIMESTAMP WITH TIME ZONE, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_booking_amount_nonnegative CHECK (amount >= 0), 
	FOREIGN KEY(travel_plan_id) REFERENCES travel_plans (id) ON DELETE CASCADE, 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);


CREATE TABLE transport_options (
	id SERIAL NOT NULL, 
	travel_plan_id INTEGER NOT NULL, 
	external_reference VARCHAR(100) NOT NULL, 
	provider VARCHAR(120) NOT NULL, 
	transport_type VARCHAR(15) NOT NULL, 
	service_number VARCHAR(50), 
	source VARCHAR(120) NOT NULL, 
	destination VARCHAR(120) NOT NULL, 
	departure_date DATE NOT NULL, 
	departure_time TIME WITHOUT TIME ZONE NOT NULL, 
	arrival_date DATE NOT NULL, 
	arrival_time TIME WITHOUT TIME ZONE NOT NULL, 
	duration_minutes INTEGER NOT NULL, 
	price_per_person NUMERIC(12, 2) NOT NULL, 
	traveller_count INTEGER NOT NULL, 
	total_price NUMERIC(12, 2) NOT NULL, 
	available BOOLEAN NOT NULL, 
	available_seats INTEGER, 
	number_of_stops INTEGER NOT NULL, 
	rating FLOAT, 
	cancellation_policy TEXT, 
	booking_class VARCHAR(50), 
	normalized_score FLOAT, 
	recommendation_type VARCHAR(50), 
	raw_data JSONB NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_transport_duration_nonnegative CHECK (duration_minutes >= 0), 
	CONSTRAINT ck_transport_price_nonnegative CHECK (price_per_person >= 0), 
	CONSTRAINT ck_transport_total_nonnegative CHECK (total_price >= 0), 
	CONSTRAINT ck_transport_travellers_positive CHECK (traveller_count > 0), 
	CONSTRAINT ck_transport_rating CHECK (rating IS NULL OR (rating >= 0 AND rating <= 5)), 
	FOREIGN KEY(travel_plan_id) REFERENCES travel_plans (id) ON DELETE CASCADE
);


CREATE TABLE weather_records (
	id SERIAL NOT NULL, 
	travel_plan_id INTEGER NOT NULL, 
	city VARCHAR(120) NOT NULL, 
	weather_date DATE NOT NULL, 
	condition VARCHAR(80) NOT NULL, 
	minimum_temperature FLOAT, 
	maximum_temperature FLOAT, 
	rain_probability FLOAT, 
	wind_speed FLOAT, 
	weather_alert TEXT, 
	outdoor_suitability VARCHAR(50), 
	raw_data JSONB NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_weather_rain_probability CHECK (rain_probability IS NULL OR (rain_probability >= 0 AND rain_probability <= 100)), 
	FOREIGN KEY(travel_plan_id) REFERENCES travel_plans (id) ON DELETE CASCADE
);


CREATE TABLE workflow_events (
	id SERIAL NOT NULL, 
	travel_request_id INTEGER, 
	travel_plan_id INTEGER, 
	event_type VARCHAR(80) NOT NULL, 
	agent_name VARCHAR(100), 
	task_name VARCHAR(150), 
	status VARCHAR(50) NOT NULL, 
	progress_percentage INTEGER NOT NULL, 
	message TEXT NOT NULL, 
	event_data JSONB NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_workflow_event_progress CHECK (progress_percentage >= 0 AND progress_percentage <= 100), 
	FOREIGN KEY(travel_request_id) REFERENCES travel_requests (id) ON DELETE CASCADE, 
	FOREIGN KEY(travel_plan_id) REFERENCES travel_plans (id) ON DELETE CASCADE
);


CREATE TABLE action_logs (
	id SERIAL NOT NULL, 
	travel_request_id INTEGER, 
	travel_plan_id INTEGER, 
	agent_task_id INTEGER, 
	timestamp TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	agent_name VARCHAR(100), 
	task_name VARCHAR(150), 
	action_type VARCHAR(80) NOT NULL, 
	action_performed TEXT NOT NULL, 
	tool_used VARCHAR(120), 
	input_summary TEXT, 
	output_summary TEXT, 
	decision TEXT, 
	decision_reason TEXT, 
	error_details JSONB NOT NULL, 
	retry_count INTEGER NOT NULL, 
	status VARCHAR(7) NOT NULL, 
	metadata JSONB NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_action_logs_retry_nonnegative CHECK (retry_count >= 0), 
	FOREIGN KEY(travel_request_id) REFERENCES travel_requests (id) ON DELETE CASCADE, 
	FOREIGN KEY(travel_plan_id) REFERENCES travel_plans (id) ON DELETE CASCADE, 
	FOREIGN KEY(agent_task_id) REFERENCES agent_tasks (id) ON DELETE SET NULL
);


CREATE TABLE itinerary_activities (
	id SERIAL NOT NULL, 
	itinerary_day_id INTEGER NOT NULL, 
	start_time TIME WITHOUT TIME ZONE NOT NULL, 
	end_time TIME WITHOUT TIME ZONE NOT NULL, 
	activity VARCHAR(180) NOT NULL, 
	location VARCHAR(200) NOT NULL, 
	activity_type VARCHAR(80) NOT NULL, 
	environment_type VARCHAR(20) NOT NULL, 
	travel_time_minutes INTEGER NOT NULL, 
	estimated_cost NUMERIC(10, 2) NOT NULL, 
	weather_suitability VARCHAR(50), 
	notes TEXT, 
	display_order INTEGER NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_activity_travel_time_nonnegative CHECK (travel_time_minutes >= 0), 
	CONSTRAINT ck_activity_cost_nonnegative CHECK (estimated_cost >= 0), 
	CONSTRAINT ck_activity_display_order_nonnegative CHECK (display_order >= 0), 
	FOREIGN KEY(itinerary_day_id) REFERENCES itinerary_days (id) ON DELETE CASCADE
);


CREATE TABLE task_dependencies (
	id SERIAL NOT NULL, 
	task_id INTEGER NOT NULL, 
	depends_on_task_id INTEGER NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_task_dependency_pair UNIQUE (task_id, depends_on_task_id), 
	CONSTRAINT ck_task_dependency_not_self CHECK (task_id <> depends_on_task_id), 
	FOREIGN KEY(task_id) REFERENCES agent_tasks (id) ON DELETE CASCADE, 
	FOREIGN KEY(depends_on_task_id) REFERENCES agent_tasks (id) ON DELETE CASCADE
);

ALTER TABLE travel_plans ADD CONSTRAINT fk_travel_plans_selected_hotel FOREIGN KEY(selected_hotel_id) REFERENCES hotel_options (id) ON DELETE SET NULL;
ALTER TABLE travel_plans ADD CONSTRAINT fk_travel_plans_selected_transport FOREIGN KEY(selected_transport_id) REFERENCES transport_options (id) ON DELETE SET NULL;
CREATE UNIQUE INDEX ix_users_email ON users (email);
CREATE INDEX ix_agent_memory_user_id ON agent_memory (user_id);
CREATE INDEX ix_travel_requests_destination ON travel_requests (destination);
CREATE INDEX ix_travel_requests_source ON travel_requests (source);
CREATE INDEX ix_travel_requests_user_id ON travel_requests (user_id);
CREATE UNIQUE INDEX ix_user_preferences_user_id ON user_preferences (user_id);
CREATE INDEX ix_travel_plans_travel_request_id ON travel_plans (travel_request_id);
CREATE INDEX ix_travel_plans_user_id ON travel_plans (user_id);
CREATE UNIQUE INDEX ix_agent_tasks_task_uuid ON agent_tasks (task_uuid);
CREATE INDEX ix_agent_tasks_travel_plan_id ON agent_tasks (travel_plan_id);
CREATE INDEX ix_agent_tasks_travel_request_id ON agent_tasks (travel_request_id);
CREATE INDEX ix_attractions_category ON attractions (category);
CREATE INDEX ix_attractions_city ON attractions (city);
CREATE INDEX ix_attractions_external_reference ON attractions (external_reference);
CREATE INDEX ix_attractions_travel_plan_id ON attractions (travel_plan_id);
CREATE UNIQUE INDEX ix_budget_breakdowns_travel_plan_id ON budget_breakdowns (travel_plan_id);
CREATE INDEX ix_confirmation_requests_travel_plan_id ON confirmation_requests (travel_plan_id);
CREATE INDEX ix_confirmation_requests_user_id ON confirmation_requests (user_id);
CREATE INDEX ix_feedback_travel_plan_id ON feedback (travel_plan_id);
CREATE INDEX ix_feedback_user_id ON feedback (user_id);
CREATE INDEX ix_hotel_options_city ON hotel_options (city);
CREATE INDEX ix_hotel_options_external_reference ON hotel_options (external_reference);
CREATE INDEX ix_hotel_options_travel_plan_id ON hotel_options (travel_plan_id);
CREATE INDEX ix_itinerary_days_travel_plan_id ON itinerary_days (travel_plan_id);
CREATE INDEX ix_plan_versions_travel_plan_id ON plan_versions (travel_plan_id);
CREATE INDEX ix_replanning_history_travel_plan_id ON replanning_history (travel_plan_id);
CREATE UNIQUE INDEX ix_simulated_bookings_booking_reference ON simulated_bookings (booking_reference);
CREATE INDEX ix_simulated_bookings_travel_plan_id ON simulated_bookings (travel_plan_id);
CREATE INDEX ix_simulated_bookings_user_id ON simulated_bookings (user_id);
CREATE INDEX ix_transport_options_destination ON transport_options (destination);
CREATE INDEX ix_transport_options_external_reference ON transport_options (external_reference);
CREATE INDEX ix_transport_options_source ON transport_options (source);
CREATE INDEX ix_transport_options_travel_plan_id ON transport_options (travel_plan_id);
CREATE INDEX ix_weather_records_city ON weather_records (city);
CREATE INDEX ix_weather_records_travel_plan_id ON weather_records (travel_plan_id);
CREATE INDEX ix_weather_records_weather_date ON weather_records (weather_date);
CREATE INDEX ix_workflow_events_created_at ON workflow_events (created_at);
CREATE INDEX ix_workflow_events_event_type ON workflow_events (event_type);
CREATE INDEX ix_workflow_events_travel_plan_id ON workflow_events (travel_plan_id);
CREATE INDEX ix_workflow_events_travel_request_id ON workflow_events (travel_request_id);
CREATE INDEX ix_action_logs_agent_name ON action_logs (agent_name);
CREATE INDEX ix_action_logs_agent_task_id ON action_logs (agent_task_id);
CREATE INDEX ix_action_logs_task_name ON action_logs (task_name);
CREATE INDEX ix_action_logs_timestamp ON action_logs (timestamp);
CREATE INDEX ix_action_logs_travel_plan_id ON action_logs (travel_plan_id);
CREATE INDEX ix_action_logs_travel_request_id ON action_logs (travel_request_id);
CREATE INDEX ix_itinerary_activities_itinerary_day_id ON itinerary_activities (itinerary_day_id);
CREATE INDEX ix_task_dependencies_depends_on_task_id ON task_dependencies (depends_on_task_id);
CREATE INDEX ix_task_dependencies_task_id ON task_dependencies (task_id);
