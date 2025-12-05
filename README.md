🧠 AI Intelligence Features
1. Zone Classification
Automatically categorizes areas into:

🏡 Quiet Residential Zone (>60% residential)
🛍️ Shopping District (>40% shops)
🍽️ Food & Entertainment Hub (>30% restaurants)
🏢 Business District (>50% offices)
🎯 Balanced Neighborhood (mixed use)
🌆 Hyper-Active Hub (commercial + entertainment)
2. Scoring System (0-10 scale)
Walkability Score: Density of amenities within walking distance
Safety Score: Based on POI types, lighting, police stations
Parking Ease: Availability of parking facilities
Family Friendliness: Schools, parks, hospitals nearby
Nightlife Score: Bars, clubs, entertainment venues
3. Lifestyle Insights
Best For: Shopping, Dining, Working, Living, Nightlife
Ideal Times: When to visit based on traffic patterns
Activity Recommendations: What to do in the area
# 🎯 **Project Overview - Crisp & Clear**

## **How Prediction Works**

The system uses a **hybrid machine learning approach** combining two models: **KNN (K-Nearest Neighbors)** finds the 5 most similar locations based on 96 POI categories (shops, restaurants, parks, etc.), while **Random Forest** uses 5 specialized regressors and 1 classifier to predict speed, congestion, and severity. When you query a location, the system first fetches nearby POIs via TomTom API, calculates similarity to 150 pre-trained locations, and generates predictions. These model predictions are then **enriched with real-time data** from three APIs: OpenWeatherMap (current weather), TomTom Traffic Flow (live speed/congestion), and TomTom Incidents (accidents, road works). Finally, all this data is combined into a **knowledge base** and fed to **Groq's Llama 3.3 70B LLM**, which analyzes everything and generates a natural language response explaining traffic conditions, safety, and recommendations.

---

## **Chatbot Functionality**

The chatbot works through two interfaces: **REST API (`/chat`)** and **WhatsApp Business API**. When a user sends a message like "Traffic at Koregaon Park, Pune", the system geocodes the location, runs the hybrid ML models to predict severity, fetches real-time weather/traffic/incidents, creates a comprehensive knowledge base with model outputs and live data, then passes it to the LLM which generates a conversational response. For WhatsApp, incoming messages hit a webhook endpoint (`/webhook/whatsapp`), get processed through the same logic, and the formatted response is sent back via Meta's WhatsApp Business API. The bot understands natural questions, supports location sharing, marks messages as read, and formats traffic reports with emojis and structured sections for easy reading on mobile.

---

## **SOS Message**

The SOS feature (`/sos` endpoint) allows users to send emergency alerts by providing their origin, destination, and up to 3 emergency contact phone numbers. When triggered, the system uses TomTom's routing API to calculate the route, generates a Google Maps link with live location, and sends WhatsApp messages via Twilio to all contacts with the message: *"🚨 EMERGENCY ALERT: [User] is traveling from [Origin] to [Destination]. Track location: [Map Link]"*. It includes error handling to track which messages succeeded or failed, and returns a response with delivery status. The feature is designed for women's safety and emergency situations where quick location sharing is critical.

---

## **Email/WhatsApp Reminders**

The reminder system (`/reminders` endpoint) uses **APScheduler** to schedule future traffic notifications via WhatsApp or email. Users provide a message, recipient (phone/email), reminder type, and scheduled time (ISO format). The scheduler stores the job, and when the time arrives, it either sends a WhatsApp message using Twilio's API or an email via SMTP. The system supports recurring reminders (daily traffic updates), one-time alerts (meeting reminders), and traffic-based triggers (notify when congestion drops below 40%). Each reminder gets a unique ID, and users can list, cancel, or modify scheduled reminders. It's perfect for commuters who want to be notified when traffic is light or when they should leave for work.

---

## **Safest Route**

The safe route feature (`/safe-route` endpoint) uses the **A* pathfinding algorithm** combined with a custom **SafetyCalculator** that loads danger zones from a JSON file (each with coordinates, severity, radius). When calculating routes, the system evaluates multiple paths between origin and destination, then scores each route based on: distance from danger zones, time of day (night routes get lower safety scores), proximity to safety POIs (police stations, hospitals), and traffic severity. Each route receives a **safety score (0-100)**, and the system returns three options: **Safest** (highest safety score, may be longer), **Fastest** (shortest time, lower safety), and **Balanced** (compromise between safety and time). The response includes turn-by-turn navigation, estimated time, distance, danger zones along the route, and nearby safety POIs (hospitals, police stations).

---

## **Visualizations**

The project includes two interactive dashboards: **Incident Analytics Dashboard** (`/api/incidents/dashboard`) and **Traffic Prediction Visualizations** (`/visualizations/{location}`). The incident dashboard uses **Leaflet.js** for mapping, showing real-time traffic incidents with color-coded markers (red for severe, yellow for moderate), a heatmap layer for congestion hotspots, and quick-jump buttons for major cities. It includes **Chart.js** visualizations: pie chart for incident type distribution (accidents, road works, jams), bar chart for severity levels, and a summary table of top 5 most delayed incidents. The traffic prediction page shows an 18-hour timeline graph (6 AM to midnight) with severity levels color-coded (green=LOW, yellow=MODERATE, orange=HIGH, red=VERY_HIGH), current conditions cards (speed, congestion, weather), and a POI distribution map showing what amenities are nearby (shopping, dining, parking). All charts are interactive, responsive, and auto-refresh every 5 minutes with live data.

---

**TL;DR**: Hybrid ML (KNN+RF) predicts traffic → Real-time APIs enrich data → LLM explains in plain English → Available via REST API, WhatsApp bot, and visual dashboards with emergency SOS and safe routing features. 🚀


✨ Key Features
🎯 Core Features
#	Feature	Description	Technology
1	Traffic Prediction	Hourly traffic severity forecast (18 hours: 6AM-12AM)	KNN + Random Forest
2	Real-time Data	Live traffic flow, weather, incidents	TomTom APIs + OpenWeather
3	Conversational AI	Natural language Q&A about traffic	Groq LLM (Llama 3.3 70B)
4	WhatsApp Bot	Check traffic via WhatsApp messages	Meta Business API
5	Safe Route Planning	Find safest route avoiding danger zones	A* Algorithm + Safety Scoring
6	POI Analysis	96 POI categories for area characterization	TomTom Places API
7	Incident Analytics	Real-time traffic incidents with heatmaps	TomTom Incidents API
8	Urban Insights	Area classification, walkability, safety scores	Custom Algorithm
9	Smart Reminders	Schedule traffic alerts (WhatsApp/Email)	APScheduler + Twilio
10	SOS Alerts	Emergency location sharing	WhatsApp API


backnend in running on  http://127.0.0.1:8000 