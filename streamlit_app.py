import streamlit as st
from skyfield.api import load, wgs84
from geopy.geocoders import Nominatim
from datetime import datetime
import datetime as dt
import ollama

st.set_page_config(page_title="What's in the Sky Tonight?", page_icon="🌌")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Spectral:wght@400;600;700&family=Inter:wght@400;500;600&display=swap');

.stApp {
    background-image: 
        linear-gradient(180deg, rgba(6,7,16,0.7) 0%, rgba(6,7,16,0.9) 40%, rgba(6,7,16,0.97) 100%),
        url('https://images.unsplash.com/photo-1509773896068-7fd415d91e2e?q=80&w=1169&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D');
    background-size: cover;
    background-position: center top;
    background-attachment: fixed;
    background-repeat: no-repeat;
    color: #E8E6F0;
}

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

h1 {
    font-family: 'Spectral', serif !important;
    font-weight: 700 !important;
    letter-spacing: 0.5px;
    background: linear-gradient(90deg, #D4A056, #E8E6F0);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

h2, h3 {
    font-family: 'Spectral', serif !important;
    color: #D4A056 !important;
}
            
.block-container {
    padding-top: 3rem;
    padding-bottom: 3rem;
}

h2, h3 {
    margin-top: 2rem !important;
}

[data-testid="stVerticalBlock"] > div {
    margin-bottom: 0.3rem;
}            

.stButton > button {
    background: linear-gradient(135deg, #D4A056, #B8843E);
    color: #0B0E1A;
    font-weight: 600;
    border: none;
    border-radius: 8px;
    padding: 0.6rem 1.5rem;
    transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(212, 160, 86, 0.35);
}

[data-testid="stTextInput"] input, [data-testid="stSelectbox"] div, .stSlider {
    background-color: rgba(255,255,255,0.04) !important;
    border-radius: 8px;
}

div[data-baseweb="select"] > div {
    background-color: rgba(255,255,255,0.04) !important;
    border-color: rgba(212,160,86,0.3) !important;
}

[data-testid="stInfo"] {
    background-color: rgba(212, 160, 86, 0.1) !important;
    border-left: 3px solid #D4A056;
}

[data-testid="stNotification"] {
    border-radius: 10px;
}

.stCaption, [data-testid="stCaptionContainer"] {
    color: #8B8AA0 !important;
}

#stars {
    position: fixed;
    top: 0; left: 0;
    width: 100%; height: 100%;
    z-index: -1;
    background-image:
        radial-gradient(2px 2px at 20px 30px, white, transparent),
        radial-gradient(2px 2px at 90px 80px, white, transparent),
        radial-gradient(2px 2px at 150px 40px, white, transparent),
        radial-gradient(2px 2px at 210px 110px, white, transparent),
        radial-gradient(2px 2px at 280px 60px, white, transparent),
        radial-gradient(2
            px 2px at 340px 130px, white, transparent);
    background-repeat: repeat;
    background-size: 400px 200px;
    opacity: 0.8;
    animation: twinkle 4s ease-in-out infinite alternate;
}

@keyframes twinkle {
    from { opacity: 0.3; }
    to { opacity: 0.7; }
}
            
/* Style sliders to match amber theme */
[data-testid="stSlider"] [role="slider"] {
    background-color: #D4A056 !important;
    border-color: #D4A056 !important;
}

[data-testid="stSlider"] > div > div > div > div {
    background-color: #D4A056 !important;
}

[data-testid="stTickBar"] {
    color: #8B8AA0 !important;
}            
</style>
<div id="stars"></div>
""", unsafe_allow_html=True)



METEOR_SHOWERS = [
    {"name": "Quadrantids", "start": (1, 1), "end": (1, 5), "peak": "Jan 3-4"},
    {"name": "Lyrids", "start": (4, 16), "end": (4, 25), "peak": "Apr 22"},
    {"name": "Eta Aquarids", "start": (4, 19), "end": (5, 28), "peak": "May 5"},
    {"name": "Perseids", "start": (7, 17), "end": (8, 24), "peak": "Aug 12-13"},
    {"name": "Orionids", "start": (10, 2), "end": (11, 7), "peak": "Oct 21"},
    {"name": "Leonids", "start": (11, 6), "end": (11, 30), "peak": "Nov 17-18"},
    {"name": "Geminids", "start": (12, 4), "end": (12, 17), "peak": "Dec 13-14"},
]

def azimuth_to_compass(azimuth):
    directions = ["North", "North-East", "East", "South-East", 
                  "South", "South-West", "West", "North-West"]
    index = round(azimuth / 45) % 8
    return directions[index]

PLANET_IMAGES = {
    "Moon": "https://images-assets.nasa.gov/image/GSFC_20171208_Archive_e001861/GSFC_20171208_Archive_e001861~medium.jpg",
    "Venus": "https://images-assets.nasa.gov/image/PIA00271/PIA00271~medium.jpg",
    "Mars": "https://images-assets.nasa.gov/image/PIA04591/PIA04591~orig.jpg",
    "Jupiter": "https://images-assets.nasa.gov/image/PIA00343/PIA00343~small.jpg",
    "Saturn": "https://images-assets.nasa.gov/image/PIA11141/PIA11141~medium.jpg",
    "ISS": "https://images-assets.nasa.gov/image/9802669/9802669~medium.jpg",
    "Mercury": "https://images-assets.nasa.gov/image/PIA00271/PIA00271~medium.jpg",
}

def check_active_meteor_showers(month, day):
    return [s for s in METEOR_SHOWERS if s["start"] <= (month, day) <= s["end"]]

@st.cache_resource
def load_ephemeris():
    ts = load.timescale()
    eph = load('de421.bsp')
    return ts, eph

ts, eph = load_ephemeris()
st.title("What's in the Sky Tonight")
st.write("Tell us where and when — we'll chart what's overhead.")

# ---------- Inputs ----------
import geonamescache

@st.cache_resource
def load_city_list():
    gc = geonamescache.GeonamesCache()
    cities = gc.get_cities()
    # Build a list like "Hyderabad, India"
    city_list = []
    for city_id, info in cities.items():
        name = info['name']
        country = info['countrycode']
        population = info.get('population', 0)
        city_list.append((f"{name}, {country}", name, population))
    # Sort by population (biggest cities first, easier to find)
    city_list.sort(key=lambda x: -x[2])
    return city_list

city_data = load_city_list()
city_display_names = [c[0] for c in city_data]

selected_city = st.selectbox(
    "Select your city",
    city_display_names,
    index=city_display_names.index("Hyderabad, IN") if "Hyderabad, IN" in city_display_names else 0
)

# Extract just the city name (without country code) for geocoding
city_name = selected_city.split(",")[0]
col1, col2 = st.columns(2)
with col1:
    date_input = st.date_input("Date", datetime.now())
with col2:
    st.write("Time")
    hour = st.slider("Hour (0-23)", 0, 23, 21)
    minute = st.slider("Minute (0-59)", 0, 59, 0, step=5)
    time_input = dt.time(hour, minute)
    st.caption(f"Selected: {hour:02d}:{minute:02d}")

generate = st.button(" Generate Sky Guide")

if generate:
    with st.spinner("Looking up your location..."):
        geolocator = Nominatim(user_agent="sky-tonight-ai")
        location_data = geolocator.geocode(city_name)

    if location_data is None:
        st.error("City not found. Try a different spelling.")
        st.stop()

    latitude = location_data.latitude
    longitude = location_data.longitude
    short_address = ", ".join(location_data.address.split(",")[:2])
    st.markdown(f"""
    <div style="
        background: rgba(212,160,86,0.12);
        border-left: 3px solid #D4A056;
        border-radius: 8px;
        padding: 12px 16px;
        color: #E8E6F0;
        margin-bottom: 10px;
    ">
        📍 {short_address}
    </div>
    """, unsafe_allow_html=True)

    # ---------- Time setup ----------
    local_dt = dt.datetime.combine(date_input, time_input)
    utc_dt = local_dt - dt.timedelta(hours=5, minutes=30)
    t = ts.utc(utc_dt.year, utc_dt.month, utc_dt.day, utc_dt.hour, utc_dt.minute, 0)

    location = wgs84.latlon(latitude, longitude)
    earth = eph['earth']
    sun = eph['sun']
    moon = eph['moon']

    # ---------- Day/night ----------
    sun_alt, sun_az, _ = (earth + location).at(t).observe(sun).apparent().altaz()
    is_night = sun_alt.degrees < 0

    # ---------- Moon ----------
    moon_alt, moon_az, _ = (earth + location).at(t).observe(moon).apparent().altaz()

    # ---------- Planets ----------
    planet_names = {
        'Mercury': 'mercury', 'Venus': 'venus', 'Mars': 'mars',
        'Jupiter': 'jupiter barycenter', 'Saturn': 'saturn barycenter',
    }
    visible_planets = []
    with st.spinner("Calculating planet positions..."):
        for name, key in planet_names.items():
            planet = eph[key]
            alt, az, distance = (earth + location).at(t).observe(planet).apparent().altaz()
            above_horizon = alt.degrees > 0
            naked_eye_visible = above_horizon and is_night
            visible_planets.append({
                'name': name, 'altitude': round(alt.degrees, 1),
                'azimuth': round(az.degrees, 1), 'naked_eye_visible': naked_eye_visible
            })

    # ---------- ISS ----------
    iss_visible = False
    iss_alt = None
    with st.spinner("Tracking the ISS..."):
        try:
            iss_url = 'https://celestrak.org/NORAD/elements/gp.php?CATNR=25544&FORMAT=TLE'
            satellites = load.tle_file(iss_url)
            iss = satellites[0]
            difference = iss - location
            iss_alt, iss_az, iss_distance = difference.at(t).altaz()
            iss_visible = iss_alt.degrees > 10
        except Exception as e:
            st.warning(f"Could not fetch ISS data: {e}")

    # ---------- Meteor showers ----------
    active_showers = check_active_meteor_showers(date_input.month, date_input.day)

    # ---------- Display raw data ----------
    st.subheader("Sky Data")

    # Build a list of "cards" to display
    cards = []

    moon_dir = azimuth_to_compass(moon_az.degrees)
    cards.append(("Moon", f"{moon_alt.degrees:.1f}° altitude", moon_dir))

    visible_now = [p for p in visible_planets if p['naked_eye_visible']]
    for p in visible_now:
        direction = azimuth_to_compass(p['azimuth'])
        cards.append((p['name'], f"{p['altitude']}° altitude", direction))

    if iss_visible:
        cards.append(("ISS", f"{iss_alt.degrees:.1f}° altitude", "Overhead pass"))

    if active_showers:
        cards.append((active_showers[0]['name'], "Meteor shower active", f"Peak: {active_showers[0]['peak']}"))

    # Render cards in a responsive row
    cols = st.columns(len(cards)) if cards else []
    for col, (name, stat, sub) in zip(cols, cards):
        with col:
            bg_image = PLANET_IMAGES.get(name, "")
            st.markdown(f"""
            <div style="
                background-image: linear-gradient(rgba(11,14,26,0.55), rgba(11,14,26,0.85)), url('{bg_image}');
                background-size: cover;
                background-position: center;
                border: 1px solid rgba(212,160,86,0.25);
                border-radius: 12px;
                padding: 18px;
                text-align: center;
                min-height: 140px;
            ">
                <div style="color:#D4A056; font-weight:600; font-size:1.05rem;">{name}</div>
                <div style="color:#E8E6F0; font-size:1.3rem; margin-top:6px;">{stat}</div>
                <div style="color:#C9C7D9; font-size:0.85rem; margin-top:4px;">{sub}</div>
            </div>
            """, unsafe_allow_html=True)

    if not visible_now and not iss_visible and not active_showers:
        if not is_night:
            st.info("It's daytime right now — nothing visible to the naked eye. Try a nighttime hour instead.")
        else:
            st.info("No major objects visible at this exact time — try a different time tonight.")

    # ---------- Build LLM prompt ----------
    sky_summary = f"""
Location: {city_name}
Date/Time: {date_input} {time_input} local time
Is it night: {is_night}
Moon: altitude={moon_alt.degrees:.1f}°, direction: {azimuth_to_compass(moon_az.degrees)}
Planets visible to naked eye:
"""
    if visible_now:
        for p in visible_now:
            direction = azimuth_to_compass(p['azimuth'])
            sky_summary += f"- {p['name']}: altitude {p['altitude']}°, direction: {direction}\n"
    else:
        sky_summary += "- None currently visible\n"
    sky_summary += f"\nISS visible: {'Yes' if iss_visible else 'No'}\n"
    sky_summary += f"\nActive meteor shower: {active_showers[0]['name'] if active_showers else 'None'}\n"

    prompt = f"""You are a friendly, enthusiastic amateur astronomy guide.

Based ONLY on the exact data provided below, write a short, warm, conversational guide (under 150 words)
telling the user what they can see in the sky at the SPECIFIC time given, and in which direction (use the azimuth
to describe direction in plain words, e.g. 0°=North, 90°=East, 180°=South, 270°=West).

STRICT RULES:
- Do NOT invent or guess any times, rise times, or set times that are not explicitly given in the data.
- Do NOT invent altitude or azimuth values — only use the exact numbers provided.
- The time given in the data IS the time the user is looking at the sky right now. Do not suggest a different time to look unless nothing is visible.
- If nothing is visible, say so honestly and suggest checking again later that night, without making up a specific time.
- Use the direction already provided in the data (e.g. "North-East") — do not calculate or guess directions yourself.
- Do NOT invent or guess any times, altitude, or direction values not explicitly given in the data.

Data:
{sky_summary}
"""

    st.subheader(" Your AI Sky Guide")
    with st.spinner("Generating your personalized guide..."):
        response = ollama.chat(model='llama3.2', messages=[{'role': 'user', 'content': prompt}])
        st.write(response['message']['content'])