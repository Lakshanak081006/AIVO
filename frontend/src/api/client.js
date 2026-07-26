import axios from 'axios'

const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'

export const api = axios.create({
  baseURL,
  timeout: 10000,
})

api.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Helper to manage client-side mock plans state
function getStoredPlans() {
  const stored = localStorage.getItem('aiva_mock_plans')
  if (stored) {
    try { return JSON.parse(stored) } catch(e){}
  }
  const defaultPlans = [generateMockPlan('1', 'Plan a two-day trip from Coimbatore to Chennai for two people next weekend under ₹20000. I prefer train travel and museums.')]
  localStorage.setItem('aiva_mock_plans', JSON.stringify(defaultPlans))
  return defaultPlans
}

function saveStoredPlans(plans) {
  localStorage.setItem('aiva_mock_plans', JSON.stringify(plans))
}

function generateMockPlan(id, instruction) {
  const isChennai = instruction.toLowerCase().includes('chennai')
  const isMumbai = instruction.toLowerCase().includes('mumbai')
  const isBengaluru = instruction.toLowerCase().includes('bengaluru')
  
  const dest = isChennai ? 'Chennai' : isMumbai ? 'Mumbai' : isBengaluru ? 'Bengaluru' : 'Chennai'
  const source = 'Coimbatore'
  
  return {
    id,
    title: `Trip from ${source} to ${dest}`,
    status: 'COMPLETED',
    version: 1,
    currency: '₹',
    total_cost: 16500,
    confirmation_status: 'NOT_SUBMITTED',
    final_summary: `Your 2-day travel plan from ${source} to ${dest} is fully generated. We have reserved high-rated express transport, a centrally located 4-star hotel, and optimized indoor museum itineraries to keep your travel comfortable and well within your ₹20,000 budget.`,
    request: {
      source,
      destination: dest,
      traveller_count: 2,
      trip_duration_days: 2,
      extracted_requirements: {
        origin: source,
        destination: dest,
        budget: 20000,
        travellers: 2,
        duration: '2 days',
        mode_preference: 'Train',
        interests: ['Museums', 'History', 'Local Food']
      }
    },
    progress: {
      percentage: 100,
      tasks: [
        { id: 't1', task_name: 'Extract Requirements', agent_name: 'Requirement', priority: 1, status: 'COMPLETED', retry_count: 0 },
        { id: 't2', task_name: 'Decompose Tasks', agent_name: 'Planner', priority: 1, status: 'COMPLETED', retry_count: 0 },
        { id: 't3', task_name: 'Search Transport', agent_name: 'Transport', priority: 2, status: 'COMPLETED', retry_count: 0 },
        { id: 't4', task_name: 'Search Hotels', agent_name: 'Hotel', priority: 2, status: 'COMPLETED', retry_count: 0 },
        { id: 't5', task_name: 'Fetch Weather Forecast', agent_name: 'Weather', priority: 2, status: 'COMPLETED', retry_count: 0 },
        { id: 't6', task_name: 'Select Attractions', agent_name: 'Attraction', priority: 3, status: 'COMPLETED', retry_count: 0 },
        { id: 't7', task_name: 'Build Itinerary', agent_name: 'Itinerary', priority: 4, status: 'COMPLETED', retry_count: 0 },
        { id: 't8', task_name: 'Calculate Budget', agent_name: 'Budget', priority: 5, status: 'COMPLETED', retry_count: 0 }
      ]
    },
    selected_transport: {
      provider: 'Cheran Superfast Express',
      transport_type: 'Train (AC Tier 2)',
      total_price: 3200
    },
    selected_hotel: {
      name: 'Grand Central Residency',
      rating: 4.6,
      total_price: 6800
    },
    transport_options: [
      { id: 'tr1', provider: 'Cheran Superfast Express', transport_type: 'Train (AC 2 Tier)', departure_time: '22:30', duration_minutes: 420, total_price: 3200, rating: 4.7, normalized_score: 0.94 },
      { id: 'tr2', provider: 'Kovai Express', transport_type: 'Train (AC Chair Car)', departure_time: '06:15', duration_minutes: 450, total_price: 2400, rating: 4.4, normalized_score: 0.88 },
      { id: 'tr3', provider: 'Indigo Airlines', transport_type: 'Flight', departure_time: '08:45', duration_minutes: 75, total_price: 9500, rating: 4.5, normalized_score: 0.72 }
    ],
    hotel_options: [
      { id: 'ho1', name: 'Grand Central Residency', price_per_night: 3400, total_price: 6800, rating: 4.6, distance_from_city_centre: '1.2 km', normalized_score: 0.92 },
      { id: 'ho2', name: 'Heritage Heritage Hotel', price_per_night: 2800, total_price: 5600, rating: 4.2, distance_from_city_centre: '2.5 km', normalized_score: 0.85 },
      { id: 'ho3', name: 'Royal Residency', price_per_night: 4500, total_price: 9000, rating: 4.8, distance_from_city_centre: '0.8 km', normalized_score: 0.81 }
    ],
    weather: [
      { id: 'w1', weather_date: 'Day 1 (Saturday)', condition: 'Partly Cloudy', minimum_temperature: 24, maximum_temperature: 32, rain_probability: 20, outdoor_suitability: 'SUITABLE', weather_alert: null },
      { id: 'w2', weather_date: 'Day 2 (Sunday)', condition: 'Pleasant', minimum_temperature: 23, maximum_temperature: 31, rain_probability: 15, outdoor_suitability: 'SUITABLE', weather_alert: null }
    ],
    attractions: [
      { id: 'a1', name: dest === 'Chennai' ? 'Government Museum & Art Gallery' : 'Chhatrapati Shivaji Museum', environment_type: 'indoor', category: 'Museum / History', rating: 4.7, entry_fee: 100, weather_suitable: true },
      { id: 'a2', name: dest === 'Chennai' ? 'Fort St. George Museum' : 'Gateway of India', environment_type: 'indoor', category: 'Historical Monument', rating: 4.5, entry_fee: 50, weather_suitable: true },
      { id: 'a3', name: dest === 'Chennai' ? 'Marina Beach Promenade' : 'Marine Drive', environment_type: 'outdoor', category: 'Sightseeing', rating: 4.6, entry_fee: 0, weather_suitable: true }
    ],
    itinerary: [
      {
        id: 'day1',
        day_number: 1,
        itinerary_date: 'Saturday',
        activities: [
          { id: 'act1', start_time: '07:00', end_time: '08:00', activity: 'Arrival and Hotel Check-in', location: 'Grand Central Residency', activity_type: 'Check-in', travel_time_minutes: 20, estimated_cost: 0, notes: 'Fresh up and breakfast' },
          { id: 'act2', start_time: '09:30', end_time: '13:00', activity: dest === 'Chennai' ? 'Visit Government Museum & National Art Gallery' : 'Visit Prince of Wales Museum', location: 'Egmore', activity_type: 'Museum', travel_time_minutes: 15, estimated_cost: 300, notes: 'Indoor exploration of bronze sculptures & history' },
          { id: 'act3', start_time: '13:30', end_time: '15:00', activity: 'Traditional South Indian Lunch', location: 'City Centre', activity_type: 'Dining', travel_time_minutes: 10, estimated_cost: 600, notes: 'Recommended thali' },
          { id: 'act4', start_time: '16:30', end_time: '19:00', activity: dest === 'Chennai' ? 'Evening Stroll at Marina Beach' : 'Evening Walk at Marine Drive', location: 'Promenade', activity_type: 'Sightseeing', travel_time_minutes: 20, estimated_cost: 100, notes: 'Enjoy sunset breeze' }
        ]
      },
      {
        id: 'day2',
        day_number: 2,
        itinerary_date: 'Sunday',
        activities: [
          { id: 'act5', start_time: '09:00', end_time: '12:00', activity: dest === 'Chennai' ? 'Fort St. George & Clive Citadel Museum' : 'Victoria Terminus Heritage Walk', location: 'Fort District', activity_type: 'Historical Site', travel_time_minutes: 15, estimated_cost: 200, notes: 'Colonial history & artifacts' },
          { id: 'act6', start_time: '13:00', end_time: '14:30', activity: 'Artisan Cafe Lunch', location: 'Art District', activity_type: 'Dining', travel_time_minutes: 10, estimated_cost: 800, notes: 'Relaxed meal' },
          { id: 'act7', start_time: '15:30', end_time: '18:00', activity: 'Souvenir Shopping & Craft Markets', location: 'Central Bazaar', activity_type: 'Shopping', travel_time_minutes: 15, estimated_cost: 1500, notes: 'Pick up local crafts' },
          { id: 'act8', start_time: '21:30', end_time: '22:00', activity: 'Return Departure Transport', location: 'Central Railway Station', activity_type: 'Departure', travel_time_minutes: 30, estimated_cost: 0, notes: 'Board return train' }
        ]
      }
    ],
    budget_breakdown: {
      currency: '₹',
      user_budget: 20000,
      transport_cost: 3200,
      hotel_cost: 6800,
      food_cost: 2500,
      local_transport_cost: 1200,
      attraction_cost: 800,
      emergency_reserve: 2000,
      total_cost: 16500,
      remaining_budget: 3500,
      within_budget: true
    },
    alternatives: {
      original_total: 16500,
      revised_total: 13900,
      savings: 2600,
      changes: ['Switch hotel from Grand Central Residency to Heritage Hotel', 'Choose Kovai Express Chair Car'],
      trade_offs: ['1 hour longer train travel', 'Hotel located 2.5 km from city centre']
    }
  }
}

// Interceptor fallback handler for static / offline / GitHub Pages deployment
api.interceptors.response.use(
  r => r,
  async err => {
    const isNetworkErr = !err.response || err.code === 'ERR_NETWORK' || err.code === 'ECONNABORTED' || err.response?.status >= 404
    
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      return Promise.reject(err)
    }

    if (isNetworkErr) {
      const config = err.config
      const url = config.url || ''
      const method = (config.method || 'get').toLowerCase()
      let data = {}
      try { if (config.data) data = typeof config.data === 'string' ? JSON.parse(config.data) : config.data } catch(e){}

      // Auth endpoints
      if (url.includes('/auth/login')) {
        const mockUser = { id: 1, email: data.email || 'demo@example.com', full_name: 'Demo Traveller' }
        localStorage.setItem('token', 'mock-jwt-token-gh-pages')
        localStorage.setItem('user', JSON.stringify(mockUser))
        return { data: { status: 'success', data: { access_token: 'mock-jwt-token-gh-pages', user: mockUser } } }
      }

      if (url.includes('/auth/register')) {
        const mockUser = { id: 1, email: data.email || 'user@example.com', full_name: data.full_name || 'New Traveller' }
        return { data: { status: 'success', data: { user: mockUser } } }
      }

      if (url.includes('/auth/me')) {
        const mockUser = JSON.parse(localStorage.getItem('user') || '{"id":1,"email":"demo@example.com","full_name":"Demo Traveller"}')
        return { data: { status: 'success', data: mockUser } }
      }

      // Demo scenarios
      if (url.includes('/demo/scenarios')) {
        return {
          data: {
            status: 'success',
            data: [
              { id: 1, name: 'Coimbatore to Chennai (Museums & Culture)', instruction: 'Plan a two-day trip from Coimbatore to Chennai for two people next weekend under ₹20000. I prefer train travel and museums.' },
              { id: 2, name: 'Coimbatore to Mumbai (Heritage & Food)', instruction: 'Plan a three-day trip from Coimbatore to Mumbai for two people next weekend under ₹15000.' },
              { id: 3, name: 'Coimbatore to Bengaluru (Weekend Getaway)', instruction: 'Plan a weekend trip from Coimbatore to Bengaluru for three people under ₹25000.' }
            ]
          }
        }
      }

      // Travel plans list
      if (url.includes('/travel/plans') && method === 'get' && !url.match(/\/travel\/plans\/[^\/]+/)) {
        const plans = getStoredPlans()
        return { data: { status: 'success', data: plans } }
      }

      // Travel plan details
      const planDetailMatch = url.match(/\/travel\/plans\/([^\/]+)$/)
      if (planDetailMatch && method === 'get') {
        const planId = planDetailMatch[1]
        const plans = getStoredPlans()
        let plan = plans.find(p => p.id === planId)
        if (!plan) {
          plan = generateMockPlan(planId, 'Plan a trip to Chennai')
          plans.push(plan)
          saveStoredPlans(plans)
        }
        return { data: { status: 'success', data: plan } }
      }

      // Create new plan
      if (url.includes('/travel/plan') && method === 'post') {
        const plans = getStoredPlans()
        const newId = String(Date.now())
        const newPlan = generateMockPlan(newId, data.instruction || 'Trip plan')
        plans.unshift(newPlan)
        saveStoredPlans(plans)
        return { data: { status: 'success', plan_id: newId } }
      }

      // Clarification
      if (url.includes('/travel/clarify') && method === 'post') {
        const plans = getStoredPlans()
        const newId = String(Date.now())
        const newPlan = generateMockPlan(newId, 'Trip plan with clarified details')
        plans.unshift(newPlan)
        saveStoredPlans(plans)
        return { data: { status: 'success', plan_id: newId } }
      }

      // Action logs
      if (url.includes('/action-logs')) {
        const logs = [
          { id: 1, timestamp: new Date().toISOString(), agent_name: 'Requirement Agent', action_performed: 'Extracted origin: Coimbatore, destination: Chennai, budget: ₹20000, duration: 2 days', task_name: 'Extract Requirements', status: 'COMPLETED' },
          { id: 2, timestamp: new Date().toISOString(), agent_name: 'Planner Agent', action_performed: 'Created task DAG with 8 parallel & sequential agent operations', task_name: 'Decompose Tasks', status: 'COMPLETED' },
          { id: 3, timestamp: new Date().toISOString(), agent_name: 'Transport Agent', action_performed: 'Found 3 transport routes. Selected Cheran Superfast Express (AC 2 Tier)', task_name: 'Search Transport', status: 'COMPLETED' },
          { id: 4, timestamp: new Date().toISOString(), agent_name: 'Hotel Agent', action_performed: 'Found 3 hotels. Selected Grand Central Residency (4.6★ rating)', task_name: 'Search Hotels', status: 'COMPLETED' },
          { id: 5, timestamp: new Date().toISOString(), agent_name: 'Weather Agent', action_performed: 'Predicted pleasant weather (24-32°C, 20% rain risk). All indoor/outdoor places suitable.', task_name: 'Fetch Weather Forecast', status: 'COMPLETED' },
          { id: 6, timestamp: new Date().toISOString(), agent_name: 'Attraction Agent', action_performed: 'Selected Government Museum, Fort St. George, Marina Beach Promenade', task_name: 'Select Attractions', status: 'COMPLETED' },
          { id: 7, timestamp: new Date().toISOString(), agent_name: 'Budget Agent', action_performed: 'Calculated total cost ₹16500 (within ₹20000 budget). Remaining reserve ₹3500.', task_name: 'Calculate Budget', status: 'COMPLETED' }
        ]
        return { data: { status: 'success', data: logs } }
      }

      // Duplicate plan
      if (url.includes('/duplicate')) {
        const plans = getStoredPlans()
        const newId = String(Date.now())
        const dupPlan = generateMockPlan(newId, 'Duplicated trip plan')
        dupPlan.title = `Copy of ${dupPlan.title}`
        plans.unshift(dupPlan)
        saveStoredPlans(plans)
        return { data: { status: 'success', plan_id: newId } }
      }

      // Replan / Event simulation
      if (url.includes('/replan') || url.includes('/simulate-event')) {
        const plans = getStoredPlans()
        const newId = String(Date.now())
        const replanned = generateMockPlan(newId, 'Replanned weather-safe trip')
        replanned.title = `Replanned (Weather / Event Adjustment)`
        replanned.version = 2
        replanned.weather[0].condition = 'Heavy Rain'
        replanned.weather[0].rain_probability = 90
        replanned.weather[0].outdoor_suitability = 'UNSUITABLE'
        replanned.weather[0].weather_alert = 'Heavy rain predicted. Outdoor activities replaced with indoor museums & galleries.'
        replanned.final_summary = 'Replanned automatically due to rain alert: Outdoor Marina Promenade walk has been replaced with indoor Chennai Science Museum and Planetarium.'
        plans.unshift(replanned)
        saveStoredPlans(plans)
        return { data: { status: 'success', plan_id: newId, new_plan_id: newId } }
      }

      // Confirmation / Booking
      if (url.includes('/confirmation')) {
        return { data: { status: 'success', message: 'Booking decision approved.' } }
      }
      if (url.includes('/book')) {
        return { data: { status: 'success', message: 'Simulated booking confirmed for Transport & Hotel!' } }
      }
      if (url.includes('/feedback')) {
        return { data: { status: 'success', message: 'Feedback saved.' } }
      }

      // Preferences
      if (url.includes('/preferences')) {
        return {
          data: {
            status: 'success',
            data: {
              preferred_transport: 'Train',
              preferred_hotel_rating: 4,
              max_budget_buffer: 5000,
              dietary_preference: 'South Indian / Vegetarian',
              disliked_activities: ['Late night travel']
            }
          }
        }
      }
    }

    return Promise.reject(err)
  }
)
