from skyfield.api import load, wgs84
from geopy.geocoders import Nominatim
from datetime import datetime
import datetime as dt
import requests
import ollama

# ---------- Meteor shower data ----------
METEOR_SHOWERS = [
    {"name": "Quadrantids", "start": (1, 1), "end": (1, 5), "peak": "Jan 3-4"},
    {"name": "Lyrids", "start": (4, 16), "end": (4, 25), "peak": "Apr 22"},
    {"name": "Eta Aquarids", "start": (4, 19), "end": (5, 28), "peak": "May 5"},
    {"name": "Perseids", "start": (7, 17), "end": (8, 24), "peak": "Aug 12-13"},
    {"name": "Orionids", "start": (10, 2), "end": (11, 7), "peak": "Oct 21"},
    {"name": "Leonids", "start": (11, 6), "end": (11, 30), "peak": "Nov 17-18"},
    {"name": "Geminids", "start": (12, 4), "end": (12, 17), "peak": "Dec 13-14"},
]

def check_active_meteor_showers(month, day):
    active = []
    for shower in METEOR_SHOWERS:
        s, e = shower["start"], shower["end"]
        if s <= (month, day) <= e:
            active.append(shower)
    return active

# ---------- Step 1: Location ----------
city_name = input("Enter your city: ")
geolocator = Nominatim(user_agent="sky-tonight-ai")
location_data = geolocator.geocode(city_name)

if location_data is None:
    print("City not found.")
    exit()

latitude = location_data.latitude
longitude = location_data.longitude
print(f"Found: {location_data.address}")
print(f"Coordinates: {latitude}, {longitude}\n")

# ---------- Step 2: Date/time ----------
date_str = input("Enter date (YYYY-MM-DD), or press Enter for today: ").strip()
time_str = input("Enter time in 24hr format (HH:MM), or press Enter for 9:00 PM: ").strip()

if date_str == "":
    date_str = datetime.now().strftime("%Y-%m-%d")
if time_str == "":
    time_str = "21:00"

year, month, day = map(int, date_str.split("-"))
hour, minute = map(int, time_str.split(":"))

local_dt = dt.datetime(year, month, day, hour, minute)
utc_dt = local_dt - dt.timedelta(hours=5, minutes=30)  # IST -> UTC

# ---------- Step 3: Skyfield setup ----------
ts = load.timescale()
eph = load('de421.bsp')
location = wgs84.latlon(latitude, longitude)
earth = eph['earth']
sun = eph['sun']
moon = eph['moon']

t = ts.utc(utc_dt.year, utc_dt.month, utc_dt.day, utc_dt.hour, utc_dt.minute, 0)

# ---------- Step 4: Day/night ----------
sun_alt, sun_az, _ = (earth + location).at(t).observe(sun).apparent().altaz()
is_night = sun_alt.degrees < 0
print(f"\nTime checked (UTC): {t.utc_iso()}")
print(f"Is it night? {'Yes' if is_night else 'No'}\n")

# ---------- Step 5: Moon ----------
moon_alt, moon_az, _ = (earth + location).at(t).observe(moon).apparent().altaz()
print(f"Moon: altitude={moon_alt.degrees:.1f}°, azimuth={moon_az.degrees:.1f}°")

# ---------- Step 6: Planets ----------
planet_names = {
    'Mercury': 'mercury',
    'Venus': 'venus',
    'Mars': 'mars',
    'Jupiter': 'jupiter barycenter',
    'Saturn': 'saturn barycenter',
}

print("\nPlanet positions:")
visible_planets = []

for name, key in planet_names.items():
    planet = eph[key]
    alt, az, distance = (earth + location).at(t).observe(planet).apparent().altaz()
    above_horizon = alt.degrees > 0
    naked_eye_visible = above_horizon and is_night
    status = "VISIBLE NOW" if naked_eye_visible else ("above horizon but daytime" if above_horizon else "below horizon")
    print(f"{name}: altitude={alt.degrees:.1f}°, azimuth={az.degrees:.1f}°  -> {status}")
    visible_planets.append({
        'name': name,
        'altitude': round(alt.degrees, 1),
        'azimuth': round(az.degrees, 1),
        'naked_eye_visible': naked_eye_visible
    })

# ---------- Step 7: ISS ----------
print("\n--- ISS Position ---")
iss_visible = False
iss_alt = None
try:
    iss_url = 'https://celestrak.org/NORAD/elements/gp.php?CATNR=25544&FORMAT=TLE'
    satellites = load.tle_file(iss_url)
    iss = satellites[0]
    difference = iss - location
    iss_alt, iss_az, iss_distance = difference.at(t).altaz()
    iss_visible = iss_alt.degrees > 10
    print(f"ISS altitude={iss_alt.degrees:.1f}°  -> {'VISIBLE' if iss_visible else 'not visible'}")
except Exception as e:
    print(f"ISS data error: {e}")

# ---------- Step 8: Meteor showers ----------
print("\n--- Meteor Showers ---")
active_showers = check_active_meteor_showers(month, day)
if active_showers:
    for s in active_showers:
        print(f"{s['name']} is active! Peak: {s['peak']}")
else:
    print("No major meteor showers active right now.")

# ---------- Step 9: Build summary for LLM ----------
sky_summary = f"""
Location: {city_name}
Date/Time: {date_str} {time_str} local time
Is it night: {is_night}

Moon: altitude={moon_alt.degrees:.1f}°, azimuth={moon_az.degrees:.1f}°

Planets visible to naked eye:
"""

visible_now = [p for p in visible_planets if p['naked_eye_visible']]
if visible_now:
    for p in visible_now:
        sky_summary += f"- {p['name']}: altitude {p['altitude']}°, azimuth {p['azimuth']}°\n"
else:
    sky_summary += "- None currently visible to the naked eye\n"

sky_summary += f"\nISS visible: {'Yes' if iss_visible else 'No'}\n"

if active_showers:
    sky_summary += f"\nActive meteor shower: {active_showers[0]['name']} (peak: {active_showers[0]['peak']})\n"
else:
    sky_summary += "\nNo active meteor showers.\n"

# ---------- Step 10: Generate AI guide ----------
print("\n--- Generating AI Sky Guide ---\n")

prompt = f"""You are a friendly, enthusiastic amateur astronomy guide.
Based on the following real astronomical data, write a short, warm, conversational guide (under 150 words)
telling the user what they can see in the sky tonight, where to look (direction), and any interesting context.
If nothing is visible, say so honestly but suggest when to check again.

Data:
{sky_summary}
"""

response = ollama.chat(model='llama3.2', messages=[{'role': 'user', 'content': prompt}])
print(response['message']['content'])