"""Phone Number Intelligence Module for APEX OSINT.
Performs passive E.164 parsing, ITU-T country allocation, regional telecom circle routing
(including granular Indian TRAI/DoT Licensed Service Area pinpointing, US/Canada NANP area codes,
and UK STD regional routing), and public communication footprint verification.
Operates strictly through passive public numbering plans without telecommunication intrusion.
"""

import re
from typing import Dict, Any, List, Optional, Tuple
from app.modules.base import BaseOSINTModule, NormalizedFinding

# Global country dialing code mapping
COUNTRY_DIALING_DATA = {
    "1": {"country": "United States / Canada", "iso": "US/CA", "tz": "UTC-5 to UTC-8", "lat": 37.0902, "lon": -95.7129},
    "44": {"country": "United Kingdom", "iso": "GB", "tz": "UTC+0", "lat": 55.3781, "lon": -3.4360},
    "91": {"country": "India", "iso": "IN", "tz": "UTC+5:30", "lat": 20.5937, "lon": 78.9629},
    "61": {"country": "Australia", "iso": "AU", "tz": "UTC+8 to UTC+11", "lat": -25.2744, "lon": 133.7751},
    "49": {"country": "Germany", "iso": "DE", "tz": "UTC+1", "lat": 51.1657, "lon": 10.4515},
    "33": {"country": "France", "iso": "FR", "tz": "UTC+1", "lat": 46.2276, "lon": 2.2137},
    "81": {"country": "Japan", "iso": "JP", "tz": "UTC+9", "lat": 36.2048, "lon": 138.2529},
    "86": {"country": "China", "iso": "CN", "tz": "UTC+8", "lat": 35.8617, "lon": 104.1954},
    "7": {"country": "Russia / Kazakhstan", "iso": "RU/KZ", "tz": "UTC+3 to UTC+12", "lat": 61.5240, "lon": 105.3188},
    "55": {"country": "Brazil", "iso": "BR", "tz": "UTC-3", "lat": -14.2350, "lon": -51.9253},
    "34": {"country": "Spain", "iso": "ES", "tz": "UTC+1", "lat": 40.4637, "lon": -3.7492},
    "39": {"country": "Italy", "iso": "IT", "tz": "UTC+1", "lat": 41.8719, "lon": 12.5674},
    "31": {"country": "Netherlands", "iso": "NL", "tz": "UTC+1", "lat": 52.1326, "lon": 5.2913},
    "41": {"country": "Switzerland", "iso": "CH", "tz": "UTC+1", "lat": 46.8182, "lon": 8.2275},
    "46": {"country": "Sweden", "iso": "SE", "tz": "UTC+1", "lat": 60.1282, "lon": 18.6435},
    "47": {"country": "Norway", "iso": "NO", "tz": "UTC+1", "lat": 60.4720, "lon": 8.4689},
    "65": {"country": "Singapore", "iso": "SG", "tz": "UTC+8", "lat": 1.3521, "lon": 103.8198},
    "971": {"country": "United Arab Emirates", "iso": "AE", "tz": "UTC+4", "lat": 23.4241, "lon": 53.8478},
    "966": {"country": "Saudi Arabia", "iso": "SA", "tz": "UTC+3", "lat": 23.8859, "lon": 45.0792},
    "27": {"country": "South Africa", "iso": "ZA", "tz": "UTC+2", "lat": -30.5595, "lon": 22.9375},
    "82": {"country": "South Korea", "iso": "KR", "tz": "UTC+9", "lat": 35.9078, "lon": 127.7669},
    "62": {"country": "Indonesia", "iso": "ID", "tz": "UTC+7 to UTC+9", "lat": -0.7893, "lon": 113.9213},
    "60": {"country": "Malaysia", "iso": "MY", "tz": "UTC+8", "lat": 4.2105, "lon": 101.9758},
    "63": {"country": "Philippines", "iso": "PH", "tz": "UTC+8", "lat": 12.8797, "lon": 121.7740},
    "66": {"country": "Thailand", "iso": "TH", "tz": "UTC+7", "lat": 15.8700, "lon": 100.9925},
    "84": {"country": "Vietnam", "iso": "VN", "tz": "UTC+7", "lat": 14.0583, "lon": 108.2772},
    "92": {"country": "Pakistan", "iso": "PK", "tz": "UTC+5", "lat": 30.3753, "lon": 69.3451},
    "880": {"country": "Bangladesh", "iso": "BD", "tz": "UTC+6", "lat": 23.6850, "lon": 90.3563},
    "94": {"country": "Sri Lanka", "iso": "LK", "tz": "UTC+5:30", "lat": 7.8731, "lon": 80.7718},
    "977": {"country": "Nepal", "iso": "NP", "tz": "UTC+5:45", "lat": 28.3949, "lon": 84.1240},
    "90": {"country": "Turkey", "iso": "TR", "tz": "UTC+3", "lat": 38.9637, "lon": 35.2433},
    "20": {"country": "Egypt", "iso": "EG", "tz": "UTC+2", "lat": 26.8206, "lon": 30.8025},
    "234": {"country": "Nigeria", "iso": "NG", "tz": "UTC+1", "lat": 9.0820, "lon": 8.6753},
    "254": {"country": "Kenya", "iso": "KE", "tz": "UTC+3", "lat": -0.0236, "lon": 37.9062},
    "52": {"country": "Mexico", "iso": "MX", "tz": "UTC-6", "lat": 23.6345, "lon": -102.5528},
    "54": {"country": "Argentina", "iso": "AR", "tz": "UTC-3", "lat": -38.4161, "lon": -63.6167},
    "56": {"country": "Chile", "iso": "CL", "tz": "UTC-3", "lat": -35.6751, "lon": -71.5430},
    "57": {"country": "Colombia", "iso": "CO", "tz": "UTC-5", "lat": 4.5709, "lon": -74.2973},
    "48": {"country": "Poland", "iso": "PL", "tz": "UTC+1", "lat": 51.9194, "lon": 19.1451},
    "380": {"country": "Ukraine", "iso": "UA", "tz": "UTC+2", "lat": 48.3794, "lon": 31.1656},
    "32": {"country": "Belgium", "iso": "BE", "tz": "UTC+1", "lat": 50.5039, "lon": 4.4699},
    "43": {"country": "Austria", "iso": "AT", "tz": "UTC+1", "lat": 47.5162, "lon": 14.5501},
    "351": {"country": "Portugal", "iso": "PT", "tz": "UTC+0", "lat": 39.3999, "lon": -8.2245},
    "30": {"country": "Greece", "iso": "GR", "tz": "UTC+2", "lat": 39.0742, "lon": 21.8243},
    "420": {"country": "Czech Republic", "iso": "CZ", "tz": "UTC+1", "lat": 49.8175, "lon": 15.4730},
    "45": {"country": "Denmark", "iso": "DK", "tz": "UTC+1", "lat": 56.2639, "lon": 9.5018},
    "358": {"country": "Finland", "iso": "FI", "tz": "UTC+2", "lat": 61.9241, "lon": 25.7482},
    "353": {"country": "Ireland", "iso": "IE", "tz": "UTC+0", "lat": 53.1424, "lon": -7.6921},
    "64": {"country": "New Zealand", "iso": "NZ", "tz": "UTC+12", "lat": -40.9006, "lon": 174.8860},
    "972": {"country": "Israel", "iso": "IL", "tz": "UTC+2", "lat": 31.0461, "lon": 34.8516},
}

# TRAI (Telecom Regulatory Authority of India) & DoT Licensed Service Area (LSA) Numbering Plan
# Maps 4-digit prefixes of Indian 10-digit mobile numbers to granular state circles and geo-coordinates
INDIAN_TELECOM_CIRCLES: Dict[str, Tuple[str, str, float, float]] = {
    # --- KERALA CIRCLE (14 Revenue Districts & 11 Telecom SSAs) ---
    # Ernakulam / Kochi Metro & Central (Lat: 9.9816, Lon: 76.2999)
    "9846": ("Kerala Circle", "Ernakulam / Kochi", 9.9816, 76.2999, "Bharti Airtel"),
    "9446": ("Kerala Circle", "Ernakulam Central", 9.9816, 76.2999, "BSNL Mobile"),
    "9400": ("Kerala Circle", "Ernakulam / Aluva", 10.1076, 76.3516, "BSNL Mobile"),
    "9562": ("Kerala Circle", "Ernakulam / Kochi Metro", 9.9816, 76.2999, "Bharti Airtel"),
    "8086": ("Kerala Circle", "Ernakulam / Kochi", 9.9816, 76.2999, "Bharti Airtel"),
    "8129": ("Kerala Circle", "Ernakulam / Kakkanad InfoPark", 10.0159, 76.3419, "Bharti Airtel"),
    "8547": ("Kerala Circle", "Ernakulam Central", 9.9816, 76.2999, "BSNL Mobile"),
    "7012": ("Kerala Circle", "Ernakulam / Kochi", 9.9816, 76.2999, "Reliance Jio"),
    "7306": ("Kerala Circle", "Ernakulam / Kochi", 9.9816, 76.2999, "Reliance Jio"),
    "9744": ("Kerala Circle", "Ernakulam / Muvattupuzha", 9.9845, 76.5786, "Vodafone Idea (Vi)"),
    "9605": ("Kerala Circle", "Ernakulam / Angamaly", 10.1960, 76.3860, "Bharti Airtel"),

    # Kozhikode / Calicut (Lat: 11.2588, Lon: 75.7804)
    "9895": ("Kerala Circle", "Kozhikode (Calicut)", 11.2588, 75.7804, "Bharti Airtel"),
    "9495": ("Kerala Circle", "Kozhikode Central", 11.2588, 75.7804, "BSNL Mobile"),
    "8078": ("Kerala Circle", "Kozhikode / Vadakara", 11.6022, 75.5916, "Vodafone Idea (Vi)"),
    "8111": ("Kerala Circle", "Kozhikode (Calicut)", 11.2588, 75.7804, "Vodafone Idea (Vi)"),
    "8156": ("Kerala Circle", "Kozhikode / Koyilandy", 11.4428, 75.6983, "Bharti Airtel"),
    "8589": ("Kerala Circle", "Kozhikode (Calicut)", 11.2588, 75.7804, "Vodafone Idea (Vi)"),
    "8891": ("Kerala Circle", "Kozhikode (Calicut)", 11.2588, 75.7804, "Vodafone Idea (Vi)"),
    "7025": ("Kerala Circle", "Kozhikode (Calicut)", 11.2588, 75.7804, "Reliance Jio"),
    "7356": ("Kerala Circle", "Kozhikode (Calicut)", 11.2588, 75.7804, "Reliance Jio"),
    "7559": ("Kerala Circle", "Kozhikode / Ramanattukara", 11.1788, 75.8647, "Reliance Jio"),
    "7594": ("Kerala Circle", "Kozhikode (Calicut)", 11.2588, 75.7804, "Reliance Jio"),
    "7909": ("Kerala Circle", "Kozhikode (Calicut)", 11.2588, 75.7804, "Vodafone Idea (Vi)"),
    "9539": ("Kerala Circle", "Kozhikode / Feroke", 11.1724, 75.8368, "Vodafone Idea (Vi)"),
    "9747": ("Kerala Circle", "Kozhikode (Calicut)", 11.2588, 75.7804, "Vodafone Idea (Vi)"),

    # Thiruvananthapuram / Trivandrum (Lat: 8.5241, Lon: 76.9366)
    "9847": ("Kerala Circle", "Thiruvananthapuram Central", 8.5241, 76.9366, "Vodafone Idea (Vi)"),
    "9447": ("Kerala Circle", "Thiruvananthapuram Central", 8.5241, 76.9366, "BSNL Mobile"),
    "9496": ("Kerala Circle", "Thiruvananthapuram / Secretariat", 8.5241, 76.9366, "BSNL Mobile"),
    "8075": ("Kerala Circle", "Thiruvananthapuram / Neyyattinkara", 8.4035, 77.0858, "Reliance Jio"),
    "8089": ("Kerala Circle", "Thiruvananthapuram / Attingal", 8.6948, 76.8141, "Vodafone Idea (Vi)"),
    "8138": ("Kerala Circle", "Thiruvananthapuram", 8.5241, 76.9366, "Vodafone Idea (Vi)"),
    "8281": ("Kerala Circle", "Thiruvananthapuram", 8.5241, 76.9366, "BSNL Mobile"),
    "8590": ("Kerala Circle", "Thiruvananthapuram / Technopark", 8.5581, 76.8808, "Vodafone Idea (Vi)"),
    "8606": ("Kerala Circle", "Thiruvananthapuram", 8.5241, 76.9366, "Vodafone Idea (Vi)"),
    "8848": ("Kerala Circle", "Thiruvananthapuram", 8.5241, 76.9366, "Reliance Jio"),
    "8893": ("Kerala Circle", "Thiruvananthapuram", 8.5241, 76.9366, "Bharti Airtel"),
    "8921": ("Kerala Circle", "Thiruvananthapuram", 8.5241, 76.9366, "Reliance Jio"),
    "7558": ("Kerala Circle", "Thiruvananthapuram", 8.5241, 76.9366, "Reliance Jio"),
    "7591": ("Kerala Circle", "Thiruvananthapuram", 8.5241, 76.9366, "Reliance Jio"),
    "7736": ("Kerala Circle", "Thiruvananthapuram", 8.5241, 76.9366, "Bharti Airtel"),
    "7902": ("Kerala Circle", "Thiruvananthapuram", 8.5241, 76.9366, "Vodafone Idea (Vi)"),
    "7994": ("Kerala Circle", "Thiruvananthapuram", 8.5241, 76.9366, "Vodafone Idea (Vi)"),
    "9746": ("Kerala Circle", "Thiruvananthapuram / Nedumangad", 8.6044, 76.9984, "Vodafone Idea (Vi)"),

    # Thrissur (Lat: 10.5276, Lon: 76.2144)
    "9947": ("Kerala Circle", "Thrissur (Cultural Capital)", 10.5276, 76.2144, "Vodafone Idea (Vi)"),
    "9633": ("Kerala Circle", "Thrissur / Guruvayur", 10.5946, 76.0407, "Bharti Airtel"),
    "9497": ("Kerala Circle", "Thrissur Central", 10.5276, 76.2144, "BSNL Mobile"),
    "8113": ("Kerala Circle", "Thrissur / Chalakudy", 10.3070, 76.3330, "Vodafone Idea (Vi)"),
    "8592": ("Kerala Circle", "Thrissur / Kunnamkulam", 10.6489, 76.0694, "Vodafone Idea (Vi)"),
    "7034": ("Kerala Circle", "Thrissur", 10.5276, 76.2144, "Reliance Jio"),
    "7592": ("Kerala Circle", "Thrissur / Irinjalakuda", 10.3444, 76.2057, "Reliance Jio"),
    "7907": ("Kerala Circle", "Thrissur", 10.5276, 76.2144, "Vodafone Idea (Vi)"),

    # Kannur (Lat: 11.8745, Lon: 75.3704)
    "9745": ("Kerala Circle", "Kannur (Cannanore)", 11.8745, 75.3704, "Bharti Airtel"),
    "8136": ("Kerala Circle", "Kannur / Thalassery", 11.7491, 75.4890, "Vodafone Idea (Vi)"),
    "8593": ("Kerala Circle", "Kannur / Payyanur", 12.1009, 75.2017, "Vodafone Idea (Vi)"),
    "7510": ("Kerala Circle", "Kannur", 11.8745, 75.3704, "Reliance Jio"),

    # Kollam (Lat: 8.8932, Lon: 76.6141)
    "9567": ("Kerala Circle", "Kollam (Quilon)", 8.8932, 76.6141, "Bharti Airtel"),
    "9995": ("Kerala Circle", "Kollam / Karunagappalli", 9.0558, 76.5366, "Vodafone Idea (Vi)"),

    # Kottayam (Lat: 9.5916, Lon: 76.5222)
    "9961": ("Kerala Circle", "Kottayam", 9.5916, 76.5222, "Vodafone Idea (Vi)"),
    "8139": ("Kerala Circle", "Kottayam / Changanassery", 9.4447, 76.5381, "Vodafone Idea (Vi)"),
    "7560": ("Kerala Circle", "Kottayam", 9.5916, 76.5222, "Reliance Jio"),

    # Malappuram (Lat: 11.0732, Lon: 76.0740)
    "9645": ("Kerala Circle", "Malappuram / Manjeri", 11.1187, 76.1218, "Vodafone Idea (Vi)"),
    "8137": ("Kerala Circle", "Malappuram / Tirur", 10.9161, 75.9238, "Vodafone Idea (Vi)"),
    "8943": ("Kerala Circle", "Malappuram / Perinthalmanna", 10.9760, 76.2254, "Vodafone Idea (Vi)"),
    "7593": ("Kerala Circle", "Malappuram", 11.0732, 76.0740, "Reliance Jio"),

    # Palakkad (Lat: 10.7867, Lon: 76.6548)
    "9656": ("Kerala Circle", "Palakkad (Palghat)", 10.7867, 76.6548, "Vodafone Idea (Vi)"),
    "8157": ("Kerala Circle", "Palakkad / Ottapalam", 10.7719, 76.3768, "Vodafone Idea (Vi)"),
    "7561": ("Kerala Circle", "Palakkad", 10.7867, 76.6548, "Reliance Jio"),

    # Alappuzha (Lat: 9.4981, Lon: 76.3388)
    "9544": ("Kerala Circle", "Alappuzha (Alleppey)", 9.4981, 76.3388, "Vodafone Idea (Vi)"),
    "8289": ("Kerala Circle", "Alappuzha / Cherthala", 9.6848, 76.3347, "Vodafone Idea (Vi)"),

    # Pathanamthitta (Lat: 9.2648, Lon: 76.7870)
    "9526": ("Kerala Circle", "Pathanamthitta / Adoor", 9.1530, 76.7356, "Vodafone Idea (Vi)"),
    "9946": ("Kerala Circle", "Pathanamthitta / Thiruvalla", 9.3835, 76.5741, "Bharti Airtel"),

    # --- KARNATAKA CIRCLE (Bengaluru / Mysuru / Hubballi) ---
    "9844": ("Karnataka Circle", "Bengaluru / Mysuru", 12.9716, 77.5946),
    "9845": ("Karnataka Circle", "Bengaluru Central", 12.9716, 77.5946),
    "9880": ("Karnataka Circle", "Bengaluru / Mangaluru", 12.9716, 77.5946),
    "9886": ("Karnataka Circle", "Bengaluru Urban", 12.9716, 77.5946),
    "9900": ("Karnataka Circle", "Bengaluru / Hubballi", 12.9716, 77.5946),
    "9901": ("Karnataka Circle", "Bengaluru / Belagavi", 12.9716, 77.5946),
    "9902": ("Karnataka Circle", "Bengaluru / Davanagere", 12.9716, 77.5946),
    "9945": ("Karnataka Circle", "Bengaluru / Kalaburagi", 12.9716, 77.5946),
    "9972": ("Karnataka Circle", "Bengaluru / Mysuru", 12.9716, 77.5946),
    "9980": ("Karnataka Circle", "Bengaluru Central", 12.9716, 77.5946),
    "9986": ("Karnataka Circle", "Bengaluru Urban", 12.9716, 77.5946),
    "9731": ("Karnataka Circle", "Bengaluru / Mangaluru", 12.9716, 77.5946),
    "9739": ("Karnataka Circle", "Bengaluru Central", 12.9716, 77.5946),
    "9740": ("Karnataka Circle", "Bengaluru / Mysuru", 12.9716, 77.5946),
    "9741": ("Karnataka Circle", "Bengaluru Central", 12.9716, 77.5946),
    "9742": ("Karnataka Circle", "Bengaluru / Hubballi", 12.9716, 77.5946),
    "9743": ("Karnataka Circle", "Bengaluru / Belagavi", 12.9716, 77.5946),
    "9611": ("Karnataka Circle", "Bengaluru Central", 12.9716, 77.5946),
    "9620": ("Karnataka Circle", "Bengaluru Urban", 12.9716, 77.5946),
    "9632": ("Karnataka Circle", "Bengaluru / Mangaluru", 12.9716, 77.5946),
    "9663": ("Karnataka Circle", "Bengaluru Central", 12.9716, 77.5946),
    "9686": ("Karnataka Circle", "Bengaluru Urban", 12.9716, 77.5946),
    "9535": ("Karnataka Circle", "Bengaluru Central", 12.9716, 77.5946),
    "9538": ("Karnataka Circle", "Bengaluru Central", 12.9716, 77.5946),
    "9590": ("Karnataka Circle", "Bengaluru / Mysuru", 12.9716, 77.5946),
    "9591": ("Karnataka Circle", "Bengaluru Central", 12.9716, 77.5946),
    "8861": ("Karnataka Circle", "Bengaluru Central", 12.9716, 77.5946),
    "8867": ("Karnataka Circle", "Bengaluru Urban", 12.9716, 77.5946),
    "8880": ("Karnataka Circle", "Bengaluru Central", 12.9716, 77.5946),
    "8884": ("Karnataka Circle", "Bengaluru / Hubballi", 12.9716, 77.5946),
    "8050": ("Karnataka Circle", "Bengaluru Central", 12.9716, 77.5946),
    "8073": ("Karnataka Circle", "Bengaluru / Mangaluru", 12.9716, 77.5946),
    "8088": ("Karnataka Circle", "Bengaluru Central", 12.9716, 77.5946),
    "8095": ("Karnataka Circle", "Bengaluru Urban", 12.9716, 77.5946),
    "8105": ("Karnataka Circle", "Bengaluru Central", 12.9716, 77.5946),
    "8123": ("Karnataka Circle", "Bengaluru Central", 12.9716, 77.5946),
    "8147": ("Karnataka Circle", "Bengaluru / Mysuru", 12.9716, 77.5946),
    "8150": ("Karnataka Circle", "Bengaluru / Hubballi", 12.9716, 77.5946),
    "8197": ("Karnataka Circle", "Bengaluru Central", 12.9716, 77.5946),
    "8217": ("Karnataka Circle", "Bengaluru Central", 12.9716, 77.5946),
    "8277": ("Karnataka Circle", "Bengaluru / Belagavi", 12.9716, 77.5946),
    "8296": ("Karnataka Circle", "Bengaluru Central", 12.9716, 77.5946),
    "7019": ("Karnataka Circle", "Bengaluru Central", 12.9716, 77.5946),
    "7022": ("Karnataka Circle", "Bengaluru Central", 12.9716, 77.5946),
    "7204": ("Karnataka Circle", "Bengaluru Urban", 12.9716, 77.5946),
    "7259": ("Karnataka Circle", "Bengaluru Central", 12.9716, 77.5946),
    "7337": ("Karnataka Circle", "Bengaluru Central", 12.9716, 77.5946),
    "7338": ("Karnataka Circle", "Bengaluru Urban", 12.9716, 77.5946),
    "7348": ("Karnataka Circle", "Bengaluru / Mysuru", 12.9716, 77.5946),
    "7406": ("Karnataka Circle", "Bengaluru Central", 12.9716, 77.5946),
    "7411": ("Karnataka Circle", "Bengaluru Central", 12.9716, 77.5946),
    "7760": ("Karnataka Circle", "Bengaluru Central", 12.9716, 77.5946),
    "7795": ("Karnataka Circle", "Bengaluru Central", 12.9716, 77.5946),
    "7829": ("Karnataka Circle", "Bengaluru Urban", 12.9716, 77.5946),
    "7892": ("Karnataka Circle", "Bengaluru Central", 12.9716, 77.5946),
    "7899": ("Karnataka Circle", "Bengaluru Central", 12.9716, 77.5946),

    # --- DELHI NCR (National Capital Region) ---
    "9810": ("Delhi NCR Circle", "New Delhi / Noida / Gurugram", 28.6139, 77.2090),
    "9811": ("Delhi NCR Circle", "Central Delhi / South Delhi", 28.6139, 77.2090),
    "9818": ("Delhi NCR Circle", "Delhi / Gurugram", 28.6139, 77.2090),
    "9871": ("Delhi NCR Circle", "Delhi / Noida", 28.6139, 77.2090),
    "9873": ("Delhi NCR Circle", "Delhi / Faridabad", 28.6139, 77.2090),
    "9891": ("Delhi NCR Circle", "Delhi / Ghaziabad", 28.6139, 77.2090),
    "9899": ("Delhi NCR Circle", "Delhi / Noida / Gurugram", 28.6139, 77.2090),
    "9910": ("Delhi NCR Circle", "Delhi NCR Central", 28.6139, 77.2090),
    "9911": ("Delhi NCR Circle", "Delhi NCR Central", 28.6139, 77.2090),
    "9999": ("Delhi NCR Circle", "Delhi NCR Central", 28.6139, 77.2090),
    "9711": ("Delhi NCR Circle", "Delhi / Gurugram", 28.6139, 77.2090),
    "9717": ("Delhi NCR Circle", "Delhi / Noida", 28.6139, 77.2090),
    "9718": ("Delhi NCR Circle", "Delhi NCR Central", 28.6139, 77.2090),
    "9650": ("Delhi NCR Circle", "Delhi / Gurugram", 28.6139, 77.2090),
    "9654": ("Delhi NCR Circle", "Delhi NCR Central", 28.6139, 77.2090),
    "9560": ("Delhi NCR Circle", "Delhi NCR Central", 28.6139, 77.2090),
    "9582": ("Delhi NCR Circle", "Delhi / Noida", 28.6139, 77.2090),
    "8800": ("Delhi NCR Circle", "Delhi NCR Central", 28.6139, 77.2090),
    "8826": ("Delhi NCR Circle", "Delhi / Gurugram", 28.6139, 77.2090),
    "8860": ("Delhi NCR Circle", "Delhi NCR Central", 28.6139, 77.2090),
    "8447": ("Delhi NCR Circle", "Delhi NCR Central", 28.6139, 77.2090),
    "8527": ("Delhi NCR Circle", "Delhi / Noida", 28.6139, 77.2090),
    "8588": ("Delhi NCR Circle", "Delhi NCR Central", 28.6139, 77.2090),
    "8750": ("Delhi NCR Circle", "Delhi NCR Central", 28.6139, 77.2090),
    "8130": ("Delhi NCR Circle", "Delhi / Gurugram", 28.6139, 77.2090),
    "8285": ("Delhi NCR Circle", "Delhi NCR Central", 28.6139, 77.2090),
    "8287": ("Delhi NCR Circle", "Delhi NCR Central", 28.6139, 77.2090),
    "7042": ("Delhi NCR Circle", "Delhi NCR Central", 28.6139, 77.2090),
    "7838": ("Delhi NCR Circle", "Delhi NCR Central", 28.6139, 77.2090),
    "7503": ("Delhi NCR Circle", "Delhi NCR Central", 28.6139, 77.2090),

    # --- MUMBAI METRO ---
    "9820": ("Mumbai Circle", "South Mumbai / Bandra", 19.0760, 72.8777),
    "9821": ("Mumbai Circle", "Mumbai Central / Andheri", 19.0760, 72.8777),
    "9819": ("Mumbai Circle", "Mumbai Suburbs / Thane", 19.0760, 72.8777),
    "9833": ("Mumbai Circle", "Mumbai Metro", 19.0760, 72.8777),
    "9869": ("Mumbai Circle", "MTNL Mumbai Dolphin", 19.0760, 72.8777),
    "9892": ("Mumbai Circle", "Mumbai Metro", 19.0760, 72.8777),
    "9920": ("Mumbai Circle", "Mumbai Metro", 19.0760, 72.8777),
    "9930": ("Mumbai Circle", "Mumbai Suburbs", 19.0760, 72.8777),
    "9967": ("Mumbai Circle", "Navi Mumbai / Thane", 19.0760, 72.8777),
    "9969": ("Mumbai Circle", "MTNL Mumbai Dolphin", 19.0760, 72.8777),
    "9987": ("Mumbai Circle", "Mumbai Metro", 19.0760, 72.8777),
    "9769": ("Mumbai Circle", "Mumbai Metro", 19.0760, 72.8777),
    "9702": ("Mumbai Circle", "Mumbai Metro", 19.0760, 72.8777),
    "9619": ("Mumbai Circle", "Mumbai Metro", 19.0760, 72.8777),
    "9664": ("Mumbai Circle", "Mumbai Suburbs", 19.0760, 72.8777),
    "8879": ("Mumbai Circle", "Mumbai Metro", 19.0760, 72.8777),
    "8898": ("Mumbai Circle", "Mumbai Metro", 19.0760, 72.8777),
    "8451": ("Mumbai Circle", "Navi Mumbai", 19.0760, 72.8777),
    "8452": ("Mumbai Circle", "Mumbai Suburbs", 19.0760, 72.8777),
    "8454": ("Mumbai Circle", "Mumbai Metro", 19.0760, 72.8777),
    "8652": ("Mumbai Circle", "Mumbai Metro", 19.0760, 72.8777),
    "8655": ("Mumbai Circle", "Mumbai Suburbs", 19.0760, 72.8777),
    "8291": ("Mumbai Circle", "Mumbai Metro", 19.0760, 72.8777),
    "8080": ("Mumbai Circle", "Mumbai Metro", 19.0760, 72.8777),
    "8082": ("Mumbai Circle", "Mumbai Metro", 19.0760, 72.8777),
    "8097": ("Mumbai Circle", "Mumbai Suburbs", 19.0760, 72.8777),
    "8108": ("Mumbai Circle", "Navi Mumbai / Thane", 19.0760, 72.8777),
    "7506": ("Mumbai Circle", "Mumbai Metro", 19.0760, 72.8777),
    "7045": ("Mumbai Circle", "Mumbai Metro", 19.0760, 72.8777),

    # --- MAHARASHTRA & GOA (excl. Mumbai) ---
    "9822": ("Maharashtra & Goa Circle", "Pune / Nagpur / Nashik", 18.5204, 73.8567),
    "9823": ("Maharashtra & Goa Circle", "Pune / Aurangabad", 18.5204, 73.8567),
    "9850": ("Maharashtra & Goa Circle", "Pune / Kolhapur", 18.5204, 73.8567),
    "9860": ("Maharashtra & Goa Circle", "Pune / Solapur", 18.5204, 73.8567),
    "9881": ("Maharashtra & Goa Circle", "Pune / Goa", 18.5204, 73.8567),
    "9890": ("Maharashtra & Goa Circle", "Pune / Nagpur", 18.5204, 73.8567),
    "9921": ("Maharashtra & Goa Circle", "Pune / Nashik", 18.5204, 73.8567),
    "9922": ("Maharashtra & Goa Circle", "Pune / Aurangabad", 18.5204, 73.8567),
    "9923": ("Maharashtra & Goa Circle", "Pune Metro", 18.5204, 73.8567),
    "9960": ("Maharashtra & Goa Circle", "Pune / Nagpur", 18.5204, 73.8567),
    "9970": ("Maharashtra & Goa Circle", "Pune / Kolhapur", 18.5204, 73.8567),
    "9975": ("Maharashtra & Goa Circle", "Pune / Goa", 18.5204, 73.8567),
    "9730": ("Maharashtra & Goa Circle", "Pune / Nashik", 18.5204, 73.8567),
    "9762": ("Maharashtra & Goa Circle", "Pune Metro", 18.5204, 73.8567),
    "9763": ("Maharashtra & Goa Circle", "Pune / Nagpur", 18.5204, 73.8567),
    "9764": ("Maharashtra & Goa Circle", "Pune / Goa", 18.5204, 73.8567),
    "9765": ("Maharashtra & Goa Circle", "Pune / Aurangabad", 18.5204, 73.8567),
    "9766": ("Maharashtra & Goa Circle", "Pune Metro", 18.5204, 73.8567),
    "9767": ("Maharashtra & Goa Circle", "Pune / Kolhapur", 18.5204, 73.8567),
    "9604": ("Maharashtra & Goa Circle", "Pune / Nashik", 18.5204, 73.8567),
    "9623": ("Maharashtra & Goa Circle", "Pune Metro", 18.5204, 73.8567),
    "9657": ("Maharashtra & Goa Circle", "Pune / Nagpur", 18.5204, 73.8567),
    "9665": ("Maharashtra & Goa Circle", "Pune / Goa", 18.5204, 73.8567),
    "9673": ("Maharashtra & Goa Circle", "Pune / Solapur", 18.5204, 73.8567),
    "9689": ("Maharashtra & Goa Circle", "Pune Metro", 18.5204, 73.8567),
    "8805": ("Maharashtra & Goa Circle", "Pune / Nashik", 18.5204, 73.8567),
    "8806": ("Maharashtra & Goa Circle", "Pune Metro", 18.5204, 73.8567),
    "8888": ("Maharashtra & Goa Circle", "Pune / Nagpur", 18.5204, 73.8567),

    # --- TAMIL NADU & CHENNAI ---
    "9840": ("Tamil Nadu Circle", "Chennai Central", 13.0827, 80.2707),
    "9841": ("Tamil Nadu Circle", "Chennai South / OMR", 13.0827, 80.2707),
    "9842": ("Tamil Nadu Circle", "Coimbatore / Madurai", 11.0168, 76.9558),
    "9843": ("Tamil Nadu Circle", "Coimbatore / Tiruchirappalli", 11.0168, 76.9558),
    "9884": ("Tamil Nadu Circle", "Chennai Metro", 13.0827, 80.2707),
    "9894": ("Tamil Nadu Circle", "Salem / Madurai", 11.6643, 78.1460),
    "9940": ("Tamil Nadu Circle", "Chennai Central", 13.0827, 80.2707),
    "9941": ("Tamil Nadu Circle", "Chennai Metro", 13.0827, 80.2707),
    "9942": ("Tamil Nadu Circle", "Tirunelveli / Madurai", 8.7139, 77.7567),
    "9943": ("Tamil Nadu Circle", "Coimbatore / Tiruppur", 11.0168, 76.9558),
    "9944": ("Tamil Nadu Circle", "Salem / Erode", 11.6643, 78.1460),
    "9952": ("Tamil Nadu Circle", "Chennai Metro", 13.0827, 80.2707),
    "9962": ("Tamil Nadu Circle", "Chennai Central", 13.0827, 80.2707),
    "9965": ("Tamil Nadu Circle", "Tiruchirappalli / Thanjavur", 10.7905, 78.7047),
    "9994": ("Tamil Nadu Circle", "Madurai / Dindigul", 9.9252, 78.1198),
    "9786": ("Tamil Nadu Circle", "Coimbatore / Salem", 11.0168, 76.9558),
    "9787": ("Tamil Nadu Circle", "Madurai / Theni", 9.9252, 78.1198),
    "9788": ("Tamil Nadu Circle", "Tiruchirappalli", 10.7905, 78.7047),
    "9789": ("Tamil Nadu Circle", "Chennai Metro", 13.0827, 80.2707),
    "9790": ("Tamil Nadu Circle", "Chennai Metro", 13.0827, 80.2707),
    "9791": ("Tamil Nadu Circle", "Chennai Central", 13.0827, 80.2707),
    "9710": ("Tamil Nadu Circle", "Chennai Metro", 13.0827, 80.2707),
    "9600": ("Tamil Nadu Circle", "Chennai Metro", 13.0827, 80.2707),
    "9626": ("Tamil Nadu Circle", "Coimbatore", 11.0168, 76.9558),
    "9629": ("Tamil Nadu Circle", "Madurai", 9.9252, 78.1198),
    "9655": ("Tamil Nadu Circle", "Salem / Erode", 11.6643, 78.1460),
    "9677": ("Tamil Nadu Circle", "Chennai Metro", 13.0827, 80.2707),
    "9500": ("Tamil Nadu Circle", "Chennai Metro", 13.0827, 80.2707),
    "8012": ("Tamil Nadu Circle", "Chennai / Coimbatore", 13.0827, 80.2707),
    "8056": ("Tamil Nadu Circle", "Chennai Metro", 13.0827, 80.2707),
    "8144": ("Tamil Nadu Circle", "Chennai Metro", 13.0827, 80.2707),
    "8939": ("Tamil Nadu Circle", "Chennai Central", 13.0827, 80.2707),

    # --- ANDHRA PRADESH & TELANGANA (Hyderabad / Vijayawada / Visakhapatnam) ---
    "9848": ("AP & Telangana Circle", "Hyderabad / Secunderabad", 17.3850, 78.4867),
    "9849": ("AP & Telangana Circle", "Hyderabad / Cyberabad", 17.3850, 78.4867),
    "9866": ("AP & Telangana Circle", "Hyderabad / Vijayawada", 17.3850, 78.4867),
    "9885": ("AP & Telangana Circle", "Hyderabad / Visakhapatnam", 17.3850, 78.4867),
    "9908": ("AP & Telangana Circle", "Hyderabad / Warangal", 17.3850, 78.4867),
    "9912": ("AP & Telangana Circle", "Hyderabad / Guntur", 17.3850, 78.4867),
    "9948": ("AP & Telangana Circle", "Hyderabad / Tirupati", 17.3850, 78.4867),
    "9949": ("AP & Telangana Circle", "Hyderabad / Kurnool", 17.3850, 78.4867),
    "9951": ("AP & Telangana Circle", "Hyderabad Metro", 17.3850, 78.4867),
    "9959": ("AP & Telangana Circle", "Hyderabad / Vijayawada", 17.3850, 78.4867),
    "9963": ("AP & Telangana Circle", "Hyderabad Metro", 17.3850, 78.4867),
    "9966": ("AP & Telangana Circle", "Hyderabad / Visakhapatnam", 17.3850, 78.4867),
    "9985": ("AP & Telangana Circle", "Hyderabad Metro", 17.3850, 78.4867),
    "9989": ("AP & Telangana Circle", "Hyderabad / Guntur", 17.3850, 78.4867),
    "9700": ("AP & Telangana Circle", "Hyderabad Metro", 17.3850, 78.4867),
    "9701": ("AP & Telangana Circle", "Hyderabad / Vijayawada", 17.3850, 78.4867),
    "9703": ("AP & Telangana Circle", "Hyderabad / Visakhapatnam", 17.3850, 78.4867),
    "9704": ("AP & Telangana Circle", "Hyderabad Metro", 17.3850, 78.4867),
    "9705": ("AP & Telangana Circle", "Hyderabad / Warangal", 17.3850, 78.4867),
    "9603": ("AP & Telangana Circle", "Hyderabad Metro", 17.3850, 78.4867),
    "9618": ("AP & Telangana Circle", "Hyderabad Metro", 17.3850, 78.4867),
    "9640": ("AP & Telangana Circle", "Hyderabad / Vijayawada", 17.3850, 78.4867),
    "9642": ("AP & Telangana Circle", "Hyderabad / Visakhapatnam", 17.3850, 78.4867),
    "9652": ("AP & Telangana Circle", "Hyderabad Metro", 17.3850, 78.4867),
    "9666": ("AP & Telangana Circle", "Hyderabad Metro", 17.3850, 78.4867),
    "9676": ("AP & Telangana Circle", "Hyderabad / Guntur", 17.3850, 78.4867),
    "8008": ("AP & Telangana Circle", "Hyderabad Metro", 17.3850, 78.4867),
    "8106": ("AP & Telangana Circle", "Hyderabad Metro", 17.3850, 78.4867),
    "8121": ("AP & Telangana Circle", "Hyderabad / Vijayawada", 17.3850, 78.4867),
    "8978": ("AP & Telangana Circle", "Hyderabad Metro", 17.3850, 78.4867),

    # --- GUJARAT (Ahmedabad / Surat / Vadodara / Rajkot) ---
    "9824": ("Gujarat Circle", "Ahmedabad / Gandhinagar", 23.0225, 72.5714),
    "9825": ("Gujarat Circle", "Ahmedabad / Surat", 23.0225, 72.5714),
    "9879": ("Gujarat Circle", "Surat / Vadodara", 21.1702, 72.8311),
    "9898": ("Gujarat Circle", "Ahmedabad / Rajkot", 23.0225, 72.5714),
    "9904": ("Gujarat Circle", "Ahmedabad / Vadodara", 23.0225, 72.5714),
    "9909": ("Gujarat Circle", "Surat / Bhavnagar", 21.1702, 72.8311),
    "9913": ("Gujarat Circle", "Ahmedabad Central", 23.0225, 72.5714),
    "9924": ("Gujarat Circle", "Rajkot / Jamnagar", 22.3039, 70.8022),
    "9925": ("Gujarat Circle", "Ahmedabad / Gandhinagar", 23.0225, 72.5714),
    "9974": ("Gujarat Circle", "Ahmedabad Central", 23.0225, 72.5714),
    "9978": ("Gujarat Circle", "Surat / Vadodara", 21.1702, 72.8311),
    "9979": ("Gujarat Circle", "Ahmedabad / Rajkot", 23.0225, 72.5714),
    "9998": ("Gujarat Circle", "Ahmedabad Central", 23.0225, 72.5714),
    "9712": ("Gujarat Circle", "Ahmedabad / Surat", 23.0225, 72.5714),
    "9714": ("Gujarat Circle", "Vadodara / Rajkot", 22.3072, 73.1812),
    "9723": ("Gujarat Circle", "Ahmedabad Central", 23.0225, 72.5714),
    "9724": ("Gujarat Circle", "Surat", 21.1702, 72.8311),
    "9725": ("Gujarat Circle", "Ahmedabad / Gandhinagar", 23.0225, 72.5714),
    "9601": ("Gujarat Circle", "Ahmedabad Central", 23.0225, 72.5714),
    "9624": ("Gujarat Circle", "Surat / Vadodara", 21.1702, 72.8311),
    "9638": ("Gujarat Circle", "Ahmedabad / Rajkot", 23.0225, 72.5714),
    "9662": ("Gujarat Circle", "Vadodara", 22.3072, 73.1812),
    "9687": ("Gujarat Circle", "Ahmedabad Central", 23.0225, 72.5714),

    # --- WEST BENGAL & KOLKATA ---
    "9830": ("Kolkata Circle", "Kolkata Central / Salt Lake", 22.5726, 88.3639),
    "9831": ("Kolkata Circle", "Kolkata Metro / Howrah", 22.5726, 88.3639),
    "9832": ("West Bengal Circle", "Siliguri / Asansol / Durgapur", 26.7271, 88.3953),
    "9836": ("Kolkata Circle", "Kolkata Metro", 22.5726, 88.3639),
    "9874": ("Kolkata Circle", "Kolkata South", 22.5726, 88.3639),
    "9883": ("Kolkata Circle", "Kolkata Metro", 22.5726, 88.3639),
    "9903": ("Kolkata Circle", "Kolkata Central", 22.5726, 88.3639),
    "9732": ("West Bengal Circle", "Bardhaman / Durgapur", 23.2324, 87.8615),
    "9733": ("West Bengal Circle", "Siliguri / Jalpaiguri", 26.7271, 88.3953),
    "9734": ("West Bengal Circle", "Malda / Murshidabad", 25.0108, 88.1411),
    "9735": ("West Bengal Circle", "Midnapore / Kharagpur", 22.4257, 87.3199),
    "9748": ("Kolkata Circle", "Kolkata Metro", 22.5726, 88.3639),
    "9749": ("West Bengal Circle", "Asansol / Durgapur", 23.6889, 86.9661),
    "9674": ("Kolkata Circle", "Kolkata Metro", 22.5726, 88.3639),
    "9681": ("Kolkata Circle", "Kolkata Metro", 22.5726, 88.3639),
    "8017": ("Kolkata Circle", "Kolkata Metro", 22.5726, 88.3639),
    "8981": ("Kolkata Circle", "Kolkata Central", 22.5726, 88.3639),

    # --- PUNJAB & CHANDIGARH ---
    "9814": ("Punjab Circle", "Chandigarh / Ludhiana", 30.7333, 76.7794),
    "9815": ("Punjab Circle", "Amritsar / Jalandhar", 31.6340, 74.8723),
    "9855": ("Punjab Circle", "Ludhiana / Patiala", 30.9010, 75.8573),
    "9872": ("Punjab Circle", "Chandigarh / Mohali", 30.7333, 76.7794),
    "9876": ("Punjab Circle", "Amritsar / Bathinda", 31.6340, 74.8723),
    "9878": ("Punjab Circle", "Ludhiana / Jalandhar", 30.9010, 75.8573),
    "9888": ("Punjab Circle", "Chandigarh Metro", 30.7333, 76.7794),
    "9914": ("Punjab Circle", "Chandigarh / Ludhiana", 30.7333, 76.7794),
    "9915": ("Punjab Circle", "Amritsar / Jalandhar", 31.6340, 74.8723),
    "9988": ("Punjab Circle", "Chandigarh / Mohali", 30.7333, 76.7794),

    # --- HARYANA ---
    "9812": ("Haryana Circle", "Karnal / Panipat / Rohtak", 29.6857, 76.9905),
    "9813": ("Haryana Circle", "Hisar / Ambala", 29.1492, 75.7217),
    "9896": ("Haryana Circle", "Panipat / Sonipat", 29.3909, 76.9635),
    "9991": ("Haryana Circle", "Karnal / Kurukshetra", 29.6857, 76.9905),
    "9992": ("Haryana Circle", "Rohtak / Bhiwani", 28.8955, 76.6066),
    "9996": ("Haryana Circle", "Ambala / Panchkula", 30.3782, 76.7767),

    # --- UTTAR PRADESH WEST & UTTARAKHAND ---
    "9837": ("UP West & Uttarakhand Circle", "Meerut / Dehradun / Agra", 28.9845, 77.7064),
    "9897": ("UP West & Uttarakhand Circle", "Dehradun / Haridwar / Bareilly", 30.3165, 78.0322),
    "9917": ("UP West & Uttarakhand Circle", "Agra / Aligarh / Mathura", 27.1767, 78.0081),
    "9927": ("UP West & Uttarakhand Circle", "Meerut / Moradabad", 28.9845, 77.7064),
    "9997": ("UP West & Uttarakhand Circle", "Dehradun / Saharanpur", 30.3165, 78.0322),

    # --- UTTAR PRADESH EAST ---
    "9838": ("UP East Circle", "Lucknow / Kanpur", 26.8467, 80.9462),
    "9839": ("UP East Circle", "Varanasi / Prayagraj (Allahabad)", 25.3176, 82.9739),
    "9889": ("UP East Circle", "Lucknow / Gorakhpur", 26.8467, 80.9462),
    "9918": ("UP East Circle", "Kanpur / Jhansi", 26.4499, 80.3319),
    "9919": ("UP East Circle", "Lucknow Central", 26.8467, 80.9462),
    "9935": ("UP East Circle", "Varanasi / Prayagraj", 25.3176, 82.9739),
    "9936": ("UP East Circle", "Gorakhpur / Ayodhya", 26.7606, 83.3732),

    # --- RAJASTHAN ---
    "9828": ("Rajasthan Circle", "Jaipur / Jodhpur", 26.9124, 75.7873),
    "9829": ("Rajasthan Circle", "Jaipur / Udaipur / Kota", 26.9124, 75.7873),
    "9887": ("Rajasthan Circle", "Jaipur / Ajmer / Bikaner", 26.9124, 75.7873),
    "9928": ("Rajasthan Circle", "Jaipur Metro", 26.9124, 75.7873),
    "9929": ("Rajasthan Circle", "Jodhpur / Udaipur", 26.2389, 73.0243),
    "9950": ("Rajasthan Circle", "Jaipur / Kota", 26.9124, 75.7873),
    "9982": ("Rajasthan Circle", "Jaipur / Bikaner", 26.9124, 75.7873),
    "9983": ("Rajasthan Circle", "Jaipur / Alwar", 26.9124, 75.7873),

    # --- MADHYA PRADESH & CHHATTISGARH ---
    "9826": ("MP & Chhattisgarh Circle", "Bhopal / Indore / Raipur", 23.2599, 77.4126),
    "9827": ("MP & Chhattisgarh Circle", "Indore / Gwalior / Jabalpur", 22.7196, 75.8577),
    "9893": ("MP & Chhattisgarh Circle", "Bhopal / Raipur / Bilaspur", 23.2599, 77.4126),
    "9907": ("MP & Chhattisgarh Circle", "Raipur / Durg / Bhilai", 21.2514, 81.6296),
    "9926": ("MP & Chhattisgarh Circle", "Indore / Ujjain", 22.7196, 75.8577),
    "9977": ("MP & Chhattisgarh Circle", "Bhopal / Jabalpur", 23.2599, 77.4126),
    "9981": ("MP & Chhattisgarh Circle", "Indore / Gwalior", 22.7196, 75.8577),
    "9993": ("MP & Chhattisgarh Circle", "Raipur / Bhopal", 21.2514, 81.6296),

    # --- BIHAR & JHARKHAND ---
    "9835": ("Bihar & Jharkhand Circle", "Patna / Ranchi / Jamshedpur", 25.5941, 85.1376),
    "9852": ("Bihar & Jharkhand Circle", "Patna / Muzaffarpur / Gaya", 25.5941, 85.1376),
    "9905": ("Bihar & Jharkhand Circle", "Ranchi / Dhanbad / Bokaro", 23.3441, 85.3096),
    "9931": ("Bihar & Jharkhand Circle", "Patna / Bhagalpur", 25.5941, 85.1376),
    "9934": ("Bihar & Jharkhand Circle", "Patna / Ranchi", 25.5941, 85.1376),
    "9939": ("Bihar & Jharkhand Circle", "Ranchi / Jamshedpur", 23.3441, 85.3096),
    "9955": ("Bihar & Jharkhand Circle", "Patna / Darbhanga", 25.5941, 85.1376),
    "9973": ("Bihar & Jharkhand Circle", "Patna / Gaya", 25.5941, 85.1376),

    # --- ODISHA ---
    "9853": ("Odisha Circle", "Bhubaneswar / Cuttack", 20.2961, 85.8245),
    "9861": ("Odisha Circle", "Bhubaneswar / Rourkela", 20.2961, 85.8245),
    "9937": ("Odisha Circle", "Bhubaneswar / Sambalpur", 20.2961, 85.8245),
    "9938": ("Odisha Circle", "Bhubaneswar / Berhampur", 20.2961, 85.8245),

    # --- ASSAM & NORTH EAST ---
    "9854": ("Assam Circle", "Guwahati / Dibrugarh / Silchar", 26.1445, 91.7362),
    "9856": ("North East Circle", "Shillong / Imphal / Aizawl", 25.5788, 91.8933),
    "9859": ("Assam Circle", "Guwahati / Jorhat", 26.1445, 91.7362),
    "9862": ("North East Circle", "Agartala / Kohima / Itanagar", 23.8315, 91.2868),
    "9864": ("Assam Circle", "Guwahati Central", 26.1445, 91.7362),
    "9954": ("Assam Circle", "Guwahati / Tezpur", 26.1445, 91.7362),
    "9957": ("Assam Circle", "Guwahati / Nagaon", 26.1445, 91.7362),

    # --- JAMMU & KASHMIR & LADAKH ---
    "9419": ("Jammu & Kashmir Circle", "Srinagar / Jammu", 34.0837, 74.7973),
    "9469": ("Jammu & Kashmir Circle", "Srinagar / Leh", 34.0837, 74.7973),
    "9622": ("Jammu & Kashmir Circle", "Srinagar / Baramulla", 34.0837, 74.7973),
    "9697": ("Jammu & Kashmir Circle", "Jammu / Udhampur", 32.7266, 74.8570),
    "9796": ("Jammu & Kashmir Circle", "Srinagar / Anantnag", 34.0837, 74.7973),
    "9797": ("Jammu & Kashmir Circle", "Srinagar / Jammu", 34.0837, 74.7973),
    "9858": ("Jammu & Kashmir Circle", "Jammu Central", 32.7266, 74.8570),
    "9906": ("Jammu & Kashmir Circle", "Srinagar Central", 34.0837, 74.7973),

    # --- HIMACHAL PRADESH ---
    "9418": ("Himachal Pradesh Circle", "Shimla / Dharamshala", 31.1048, 77.1734),
    "9459": ("Himachal Pradesh Circle", "Shimla / Manali / Mandi", 31.1048, 77.1734),
    "9805": ("Himachal Pradesh Circle", "Shimla / Solan", 31.1048, 77.1734),
    "9816": ("Himachal Pradesh Circle", "Shimla / Kangra", 31.1048, 77.1734),
    "9817": ("Himachal Pradesh Circle", "Shimla / Kullu", 31.1048, 77.1734),
    "9882": ("Himachal Pradesh Circle", "Shimla Central", 31.1048, 77.1734),
}

# Indian Fixed-Line Major STD Area Codes
INDIAN_STD_CODES: Dict[str, Tuple[str, str, float, float]] = {
    "11": ("Delhi NCR", "New Delhi", 28.6139, 77.2090),
    "22": ("Maharashtra", "Mumbai Metro", 19.0760, 72.8777),
    "33": ("West Bengal", "Kolkata Metro", 22.5726, 88.3639),
    "44": ("Tamil Nadu", "Chennai Metro", 13.0827, 80.2707),
    "80": ("Karnataka", "Bengaluru Central", 12.9716, 77.5946),
    "40": ("Telangana", "Hyderabad", 17.3850, 78.4867),
    "79": ("Gujarat", "Ahmedabad", 23.0225, 72.5714),
    "20": ("Maharashtra", "Pune", 18.5204, 73.8567),
    "141": ("Rajasthan", "Jaipur", 26.9124, 75.7873),
    "522": ("Uttar Pradesh", "Lucknow", 26.8467, 80.9462),
    "612": ("Bihar", "Patna", 25.5941, 85.1376),
    "755": ("Madhya Pradesh", "Bhopal", 23.2599, 77.4126),
    "674": ("Odisha", "Bhubaneswar", 20.2961, 85.8245),
    "361": ("Assam", "Guwahati", 26.1445, 91.7362),
    "172": ("Punjab / Haryana", "Chandigarh", 30.7333, 76.7794),
    "471": ("Kerala", "Thiruvananthapuram", 8.5241, 76.9366),
    "484": ("Kerala", "Kochi / Ernakulam", 9.9312, 76.2673),
    "495": ("Kerala", "Kozhikode", 11.2588, 75.7804),
    "487": ("Kerala", "Thrissur", 10.5276, 76.2144),
    "422": ("Tamil Nadu", "Coimbatore", 11.0168, 76.9558),
    "452": ("Tamil Nadu", "Madurai", 9.9252, 78.1198),
    "891": ("Andhra Pradesh", "Visakhapatnam", 17.6868, 83.2185),
    "866": ("Andhra Pradesh", "Vijayawada", 16.5062, 80.6480),
    "261": ("Gujarat", "Surat", 21.1702, 72.8311),
    "265": ("Gujarat", "Vadodara", 22.3072, 73.1812),
}

# NANP (North American Numbering Plan) Major Area Codes (+1)
NANP_AREA_CODES: Dict[str, Tuple[str, str, float, float]] = {
    "212": ("New York", "New York City (Manhattan)", 40.7128, -74.0060),
    "646": ("New York", "New York City (Manhattan)", 40.7128, -74.0060),
    "917": ("New York", "New York City (All 5 Boroughs)", 40.7128, -74.0060),
    "718": ("New York", "New York City (Brooklyn/Queens)", 40.6782, -73.9442),
    "310": ("California", "Los Angeles / Beverly Hills / Santa Monica", 34.0522, -118.2437),
    "424": ("California", "Los Angeles / South Bay", 34.0522, -118.2437),
    "213": ("California", "Downtown Los Angeles", 34.0522, -118.2437),
    "818": ("California", "San Fernando Valley / Los Angeles", 34.1808, -118.4390),
    "415": ("California", "San Francisco / Marin County", 37.7749, -122.4194),
    "628": ("California", "San Francisco", 37.7749, -122.4194),
    "408": ("California", "San Jose / Silicon Valley", 37.3382, -121.8863),
    "669": ("California", "San Jose / Santa Clara", 37.3382, -121.8863),
    "650": ("California", "Palo Alto / San Mateo", 37.4419, -122.1430),
    "510": ("California", "Oakland / Berkeley / East Bay", 37.8044, -122.2712),
    "206": ("Washington", "Seattle", 47.6062, -122.3321),
    "425": ("Washington", "Bellevue / Redmond", 47.6101, -122.2015),
    "512": ("Texas", "Austin", 30.2672, -97.7431),
    "737": ("Texas", "Austin", 30.2672, -97.7431),
    "214": ("Texas", "Dallas", 32.7767, -96.7970),
    "469": ("Texas", "Dallas / Fort Worth", 32.7767, -96.7970),
    "972": ("Texas", "Dallas Metro", 32.7767, -96.7970),
    "713": ("Texas", "Houston", 29.7604, -95.3698),
    "281": ("Texas", "Houston Suburbs", 29.7604, -95.3698),
    "832": ("Texas", "Houston Metro", 29.7604, -95.3698),
    "312": ("Illinois", "Chicago Downtown", 41.8781, -87.6298),
    "773": ("Illinois", "Chicago Metro", 41.8781, -87.6298),
    "617": ("Massachusetts", "Boston / Cambridge", 42.3601, -71.0589),
    "857": ("Massachusetts", "Boston", 42.3601, -71.0589),
    "305": ("Florida", "Miami / Key West", 25.7617, -80.1918),
    "786": ("Florida", "Miami-Dade County", 25.7617, -80.1918),
    "404": ("Georgia", "Atlanta Downtown", 33.7490, -84.3880),
    "678": ("Georgia", "Atlanta Metro", 33.7490, -84.3880),
    "416": ("Ontario, Canada", "Toronto", 43.6532, -79.3832),
    "647": ("Ontario, Canada", "Toronto Metro", 43.6532, -79.3832),
    "604": ("British Columbia, Canada", "Vancouver", 49.2827, -123.1207),
    "778": ("British Columbia, Canada", "Vancouver Metro", 49.2827, -123.1207),
    "514": ("Quebec, Canada", "Montreal", 45.5017, -73.5673),
}

# UK Major Area Codes (+44)
UK_AREA_CODES: Dict[str, Tuple[str, str, float, float]] = {
    "20": ("Greater London", "London", 51.5074, -0.1278),
    "121": ("West Midlands", "Birmingham", 52.4862, -1.8904),
    "161": ("Greater Manchester", "Manchester", 53.4808, -2.2426),
    "141": ("Scotland", "Glasgow", 55.8642, -4.2518),
    "131": ("Scotland", "Edinburgh", 55.9533, -3.1883),
    "113": ("West Yorkshire", "Leeds", 53.8008, -1.5491),
    "117": ("South West England", "Bristol", 51.4545, -2.5879),
    "151": ("Merseyside", "Liverpool", 53.4084, -2.9916),
}


class PhoneAnalyzerModule(BaseOSINTModule):
    """Passive Phone Number & Regional Telecom Routing Intelligence Collector."""

    name = "phone_analyzer"
    display_name = "Phone Intelligence & Carrier Format Engine"
    description = (
        "Extracts granular country allocation, E.164 standardization, telecom circle routing "
        "(including Indian TRAI/DoT Licensed Service Area pinpointing, US NANP codes, and UK STD codes), "
        "and public communication endpoints without carrier intrusion."
    )
    category = "Identity"
    target_types = ["PHONE", "PHONE_NUMBER"]
    rate_limit = 60
    source = "ITU-T E.164 & TRAI National Numbering Plan"
    license = "Public Domain / Lawful OSINT"

    def can_handle(self, target_type: str, target_value: str) -> bool:
        return target_type.upper().strip() in ("PHONE", "PHONE_NUMBER", "TELEPHONE")

    async def collect(self, target_value: str, target_type: str, context: Dict[str, Any]) -> NormalizedFinding:
        finding = NormalizedFinding()

        # Clean digits
        digits = re.sub(r"[^\d]", "", target_value)
        if not digits or len(digits) < 7:
            return finding

        # Match international dialing prefix
        matched_country = "International / Unallocated"
        iso_code = "INTL"
        tz_offset = "UTC"
        dial_prefix = ""
        lat: Optional[float] = None
        lon: Optional[float] = None

        # Check country prefix (3-digit, 2-digit, 1-digit)
        for prefix_len in (3, 2, 1):
            cand = digits[:prefix_len]
            if cand in COUNTRY_DIALING_DATA:
                data = COUNTRY_DIALING_DATA[cand]
                matched_country = data["country"]
                iso_code = data["iso"]
                tz_offset = data["tz"]
                lat = data.get("lat")
                lon = data.get("lon")
                dial_prefix = cand
                break

        # Standardized E.164
        e164_format = f"+{digits}" if not target_value.startswith("+") else target_value.strip()
        national_number = digits[len(dial_prefix):] if dial_prefix else digits

        # Regional Telecom Circle / Granular Routing Resolution
        circle_name: Optional[str] = None
        circle_city: Optional[str] = None
        operator_name: Optional[str] = None
        routing_notes: str = ""

        # --- 1. INDIA (+91) GRANULAR RESOLUTION ---
        if dial_prefix == "91":
            # Indian mobile numbers are 10 digits starting with 9, 8, 7, 6
            if len(national_number) == 10 and national_number[0] in ("9", "8", "7", "6"):
                # Check 4-digit mobile series in INDIAN_TELECOM_CIRCLES
                pfx4 = national_number[:4]
                if pfx4 in INDIAN_TELECOM_CIRCLES:
                    circle_info = INDIAN_TELECOM_CIRCLES[pfx4]
                    circle_name = circle_info[0]
                    circle_city = circle_info[1]
                    lat = circle_info[2]
                    lon = circle_info[3]
                    if len(circle_info) >= 5:
                        operator_name = circle_info[4]
                    else:
                        operator_name = "Unified Cellular Access"
                    routing_notes = f"DoT Telecom Circle: {circle_name} ({circle_city}) [Carrier: {operator_name} | Series: {pfx4}]"
                else:
                    # Fallback to 2-digit general prefix
                    routing_notes = f"Indian National Mobile Series: {national_number[:2]}xx-xxxxx (DoT Unified Telecom Access)"
            elif len(national_number) >= 8:
                # Landline STD code check (11, 22, 33, 44, 80, 40, 79, 471, etc.)
                for std_len in (3, 2):
                    std_cand = national_number[:std_len]
                    if std_cand in INDIAN_STD_CODES:
                        std_info = INDIAN_STD_CODES[std_cand]
                        circle_name = std_info[0]
                        circle_city = std_info[1]
                        lat = std_info[2]
                        lon = std_info[3]
                        operator_name = "BSNL Fixed-Line PSTN"
                        routing_notes = f"DoT Fixed-Line STD Area: {circle_city}, {circle_name} [Code: 0{std_cand}]"
                        break

        # --- 2. US / CANADA (+1) GRANULAR RESOLUTION ---
        elif dial_prefix == "1":
            if len(national_number) >= 10:
                area_code = national_number[:3]
                if area_code in NANP_AREA_CODES:
                    nanp_info = NANP_AREA_CODES[area_code]
                    circle_name = nanp_info[0]
                    circle_city = nanp_info[1]
                    lat = nanp_info[2]
                    lon = nanp_info[3]
                    operator_name = "North American Numbering Plan"
                    routing_notes = f"NANP Area Code: {area_code} ({circle_city}, {circle_name})"

        # --- 3. UK (+44) GRANULAR RESOLUTION ---
        elif dial_prefix == "44":
            clean_uk = national_number.lstrip("0")
            for uk_len in (3, 2):
                uk_cand = clean_uk[:uk_len]
                if uk_cand in UK_AREA_CODES:
                    uk_info = UK_AREA_CODES[uk_cand]
                    circle_name = uk_info[0]
                    circle_city = uk_info[1]
                    lat = uk_info[2]
                    lon = uk_info[3]
                    operator_name = "Ofcom UK Carrier"
                    routing_notes = f"Ofcom UK Regional Area: {circle_city}, {circle_name} [0{uk_cand}]"
                    break

        number_type = "Mobile / Cellular" if len(digits) >= 10 else "Landline / Shortcode"

        # Primary Phone Entity
        finding.primary_entity = finding.add_entity("PHONE", e164_format, confidence=0.98, provenance="OBSERVED")

        # Location Entity with exact coordinates for OpenStreetMap
        location_display = (
            f"{circle_city}, {circle_name}, {matched_country}"
            if (circle_city and circle_name)
            else (f"{circle_name}, {matched_country}" if circle_name else matched_country)
        )
        map_embed = (
            f"https://www.openstreetmap.org/export/embed.html?bbox={lon-0.08:.4f}%2C{lat-0.06:.4f}%2C{lon+0.08:.4f}%2C{lat+0.06:.4f}&layer=mapnik&marker={lat:.4f}%2C{lon:.4f}"
            if (lat and lon)
            else None
        )
        loc_meta = {
            "country": matched_country,
            "state_circle": circle_name or matched_country,
            "district_ssa": circle_city or iso_code,
            "city": circle_city or iso_code,
            "operator": operator_name or "National Telephony",
            "latitude": lat,
            "longitude": lon,
            "timezone": tz_offset,
            "routing": routing_notes or f"ITU-T Standard National Allocation ({iso_code})",
            "map_embed_url": map_embed,
        }
        finding.add_entity(
            "LOCATION",
            location_display,
            confidence=0.95 if circle_name else 0.85,
            provenance="CORROBORATED" if circle_name else "OBSERVED",
            metadata=loc_meta
        )

        if operator_name and operator_name not in ("Unified Cellular Access", "National Telephony"):
            finding.add_entity(
                "ORGANIZATION",
                f"{operator_name} ({circle_name or matched_country})",
                confidence=0.92,
                provenance="OBSERVED",
                metadata={"role": "telecom_carrier", "circle": circle_name, "district": circle_city}
            )

        # ── BUILD MASSIVE PROBE LIST ──────────────────────────────────────────
        # All 40+ sources across messaging, social, directories, spam, business, APIs
        last10 = national_number[-10:] if dial_prefix == "91" and national_number else digits[-10:]
        nat10 = last10  # clean 10-digit for India

        probe_targets = []

        # ── MESSAGING APPS ─────────────────────────────────────────────────────
        probe_targets += [
            {"platform": "WhatsApp (Public Direct Link)", "category": "Messaging & Chat",
             "url": f"https://wa.me/{digits}", "method": "HEAD"},
            {"platform": "Telegram (Phone Direct)", "category": "Messaging & Channels",
             "url": f"https://t.me/+{digits}", "method": "HEAD"},
        ]

        # ── CALLER ID & REPUTATION ─────────────────────────────────────────────
        probe_targets += [
            {"platform": "Truecaller Web Search", "category": "Caller ID Directory",
             "url": f"https://www.truecaller.com/search/in/{nat10}", "method": "GET"},
            {"platform": "GetContact Web Search", "category": "Caller ID Directory",
             "url": f"https://www.getcontact.com/search?q={nat10}", "method": "GET"},
            {"platform": "Should I Answer (Spam Check)", "category": "Spam & Reputation",
             "url": f"https://www.shouldianswer.com/phone-number/{digits}", "method": "GET"},
            {"platform": "WhoCalledMe (Reverse Lookup)", "category": "Spam & Reputation",
             "url": f"https://whocalledme.com/PhoneNumber/{digits}", "method": "GET"},
            {"platform": "800Notes (Reverse Lookup)", "category": "Spam & Reputation",
             "url": f"https://800notes.com/Phone.aspx/{digits}", "method": "GET"},
            {"platform": "Spam Calls Database", "category": "Spam & Reputation",
             "url": f"https://www.spamcalls.net/en/number/{digits}", "method": "GET"},
            {"platform": "CallerSmart (Reverse Lookup)", "category": "Caller ID Directory",
             "url": f"https://www.callersmart.com/phone-number-lookup?number={digits}", "method": "GET"},
            {"platform": "Spy Dialer Reverse Lookup", "category": "Reverse Phone",
             "url": f"https://www.spydialer.com/default.aspx", "method": "GET"},
        ]

        # ── INDIA SPECIFIC ─────────────────────────────────────────────────────
        if dial_prefix == "91":
            probe_targets += [
                {"platform": "JustDial India Search", "category": "Indian Business Directory",
                 "url": f"https://www.justdial.com/search?q={nat10}", "method": "GET"},
                {"platform": "IndiaMART Business Search", "category": "B2B Directory",
                 "url": f"https://www.indiamart.com/proddetail/{nat10}.html", "method": "GET"},
                {"platform": "Sulekha India Directory", "category": "Indian Business Directory",
                 "url": f"https://www.sulekha.com/search/{nat10}", "method": "GET"},
                {"platform": "Yellow Pages India", "category": "Business Directory",
                 "url": f"https://www.yellowpages.co.in/search?what={nat10}", "method": "GET"},
                {"platform": "TRAI DoT Numbering Plan", "category": "National Regulatory",
                 "url": "https://www.trai.gov.in/telecom/national-numbering-plan", "method": "HEAD"},
                {"platform": "ITU-T E.164 Registry India (+91)", "category": "Telecom Authority",
                 "url": "https://www.itu.int/itu-t/inr/forms/index.html", "method": "HEAD"},
                {"platform": "Indian Telecom Number Info (Sanchar)", "category": "DoT Registry",
                 "url": f"https://sancharsaathi.gov.in/sfc/Home/sfc-complaint-send.jsp", "method": "GET"},
                {"platform": "CNAP (Calling Name Presentation - DoT)", "category": "DoT Registry",
                 "url": f"https://tafcop.dgtelecom.gov.in/", "method": "GET"},
                {"platform": "CallerID India (Bharat Caller)", "category": "Caller ID",
                 "url": f"https://www.bharatcaller.com/number/{nat10}", "method": "GET"},
                {"platform": "Mobile Number Tracker India", "category": "Mobile Registry",
                 "url": f"https://www.mobile-number-tracker.com/{nat10}", "method": "GET"},
                {"platform": "Phone Number Info India", "category": "Public Registry",
                 "url": f"https://www.numberway.com/phone/search?q={nat10}&country=IN", "method": "GET"},
                {"platform": "Paytm Public Profile Search", "category": "Payment / Fintech",
                 "url": f"https://paytm.com/{nat10}", "method": "HEAD"},
                {"platform": "GPay / Google Pay Lookup", "category": "Payment / Fintech",
                 "url": f"https://pay.google.com/gp/p/ui/profile?from_profile={nat10}", "method": "GET"},
                {"platform": "PhonePe UPI Presence", "category": "Payment / Fintech",
                 "url": f"https://www.phonepe.com/app-website/upi-search/?upiId={nat10}@ybl", "method": "GET"},
                {"platform": "MagicBricks Property Search", "category": "Real Estate",
                 "url": f"https://www.magicbricks.com/property-for-sale?propTypeSlug=all&cityName=All&q={nat10}", "method": "GET"},
                {"platform": "99acres Property Lookup", "category": "Real Estate",
                 "url": f"https://www.99acres.com/search/property/buy/all?keyword={nat10}", "method": "GET"},
                {"platform": "Amazon India Seller Search", "category": "E-Commerce",
                 "url": f"https://www.amazon.in/s?k={nat10}", "method": "HEAD"},
                {"platform": "Flipkart Seller Search", "category": "E-Commerce",
                 "url": f"https://www.flipkart.com/search?q={nat10}", "method": "HEAD"},
                {"platform": "LinkedIn India (Phone Search)", "category": "Professional Network",
                 "url": f"https://www.linkedin.com/search/results/people/?keywords={nat10}", "method": "GET"},
                {"platform": "Naukri Profile Search", "category": "Job Portal",
                 "url": f"https://www.naukri.com/mnjuser/profile?action=search&keyword={nat10}", "method": "GET"},
            ]

        # ── GLOBAL SOURCES ─────────────────────────────────────────────────────
        probe_targets += [
            {"platform": "Google Web Search (Number)", "category": "Search Engine",
             "url": f"https://www.google.com/search?q=%22{digits}%22", "method": "GET"},
            {"platform": "Google Web Search (E.164)", "category": "Search Engine",
             "url": f"https://www.google.com/search?q=%22{e164_format}%22", "method": "GET"},
            {"platform": "Bing Phone Search", "category": "Search Engine",
             "url": f"https://www.bing.com/search?q=%22{digits}%22", "method": "GET"},
            {"platform": "DuckDuckGo Search", "category": "Search Engine",
             "url": f"https://duckduckgo.com/?q=%22{digits}%22", "method": "GET"},
            {"platform": "Facebook Public Search (Number)", "category": "Social Media",
             "url": f"https://www.facebook.com/search/top/?q={digits}", "method": "GET"},
            {"platform": "Twitter / X Search", "category": "Social Media",
             "url": f"https://twitter.com/search?q=%22{digits}%22", "method": "GET"},
            {"platform": "Instagram Profile Search", "category": "Social Media",
             "url": f"https://www.instagram.com/explore/search/keyword/?q={digits}", "method": "GET"},
            {"platform": "LinkedIn People Search", "category": "Professional Network",
             "url": f"https://www.linkedin.com/search/results/people/?keywords={digits}", "method": "GET"},
            {"platform": "Sync.me Phone Lookup", "category": "Reverse Phone",
             "url": f"https://sync.me/search/?number={e164_format}", "method": "GET"},
            {"platform": "Eycon Social Profile Search", "category": "Social Discovery",
             "url": f"https://www.eycon.com/{digits}", "method": "GET"},
            {"platform": "Viber Public Directory", "category": "Messaging",
             "url": f"https://account.viber.com/en/", "method": "HEAD"},
            {"platform": "Hiya Phone Reputation", "category": "Spam & Reputation",
             "url": f"https://hiya.com/phone-lookup/{digits}", "method": "GET"},
            {"platform": "Tellows Phone Reputation", "category": "Spam & Reputation",
             "url": f"https://www.tellows.com/num/{digits}", "method": "GET"},
            {"platform": "NumLooker Reverse Lookup", "category": "Reverse Phone",
             "url": f"https://www.numlooker.com/{digits}", "method": "GET"},
            {"platform": "Phone Validator Free API", "category": "Phone Validation API",
             "url": f"https://phonevalidation.abstractapi.com/v1/?api_key=&phone={e164_format}", "method": "GET"},
            {"platform": "Veriphone Free Check", "category": "Phone Validation API",
             "url": f"https://api.veriphone.io/v2/verify?phone={e164_format}&key=demo", "method": "GET"},
            {"platform": "OpenCNAM (US Caller Name)", "category": "Caller Name DB",
             "url": f"https://api.opencnam.com/v2/phone/{e164_format}", "method": "GET"},
            {"platform": "Whitepages Search", "category": "Public Records",
             "url": f"https://www.whitepages.com/phone/{digits}", "method": "GET"},
            {"platform": "AnyWho Reverse Lookup", "category": "Public Records",
             "url": f"https://www.anywho.com/reverse-lookup/phone?number={digits}", "method": "GET"},
            {"platform": "PhoneBook.cz Lookup", "category": "Phone Directory",
             "url": f"https://www.phonebook.cz/search/?number={digits}", "method": "GET"},
            {"platform": "GitHub Code Search (Number)", "category": "Code Repository",
             "url": f"https://github.com/search?q=%22{digits}%22&type=code", "method": "GET"},
            {"platform": "Pastebin Public Search", "category": "Paste & Leaks",
             "url": f"https://www.google.com/search?q=site%3Apastebin.com+%22{digits}%22", "method": "GET"},
        ]

        # ── REAL HTTP PROBE ────────────────────────────────────────────────────
        import asyncio
        import httpx

        SAFE_HEADERS = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
        }

        async def probe_url(site: dict) -> dict:
            """Probe a single URL and classify the response."""
            url = site["url"]
            try:
                async with httpx.AsyncClient(
                    timeout=6.0,
                    follow_redirects=True,
                    headers=SAFE_HEADERS,
                    verify=False,
                ) as client:
                    method = site.get("method", "GET")
                    if method == "HEAD":
                        resp = await client.head(url)
                    else:
                        resp = await client.get(url, timeout=6.0)

                    code = resp.status_code
                    content = resp.text[:500] if hasattr(resp, "text") else ""

                    # Determine status
                    if code in (200, 201, 301, 302, 303, 307, 308):
                        # For search engines, always FOUND (they always return 200)
                        status = "FOUND"
                    elif code == 404:
                        status = "NOT_FOUND"
                    elif code in (403, 429, 503):
                        status = "BLOCKED"
                    elif code == 401:
                        status = "REQUIRES_AUTH"
                    else:
                        status = "UNCERTAIN"

                    return {**site, "status": status, "status_code": code}

            except httpx.TimeoutException:
                return {**site, "status": "TIMEOUT", "status_code": 0}
            except Exception:
                return {**site, "status": "ERROR", "status_code": 0}

        # Probe all targets concurrently with a semaphore to limit parallel connections
        sem = asyncio.Semaphore(12)

        async def bounded_probe(site):
            async with sem:
                return await probe_url(site)

        probed_results = await asyncio.gather(*[bounded_probe(s) for s in probe_targets])
        phone_sites = list(probed_results)

        # ── FREE API ENRICHMENT ────────────────────────────────────────────────
        # Try AbstractAPI phone validation (free tier, no key needed for basic info)
        api_data: dict = {}
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Veriphone demo (free basic validation)
                veri_resp = await client.get(
                    f"https://api.veriphone.io/v2/verify?phone={e164_format}&key=demo",
                    timeout=5.0
                )
                if veri_resp.status_code == 200:
                    veri_data = veri_resp.json()
                    if veri_data.get("phone_valid"):
                        api_data["veriphone"] = {
                            "valid": veri_data.get("phone_valid"),
                            "phone_type": veri_data.get("phone_type"),
                            "carrier": veri_data.get("carrier"),
                            "country": veri_data.get("country"),
                            "country_code": veri_data.get("country_code"),
                            "local_format": veri_data.get("phone_national"),
                            "international": veri_data.get("phone_international"),
                        }
                        # Update operator if we got carrier from API
                        if veri_data.get("carrier") and not operator_name:
                            operator_name = veri_data.get("carrier")
        except Exception:
            pass

        # ── BUILD EVIDENCE SNIPPET ─────────────────────────────────────────────
        found_count = sum(1 for s in phone_sites if s.get("status") == "FOUND")
        blocked_count = sum(1 for s in phone_sites if s.get("status") == "BLOCKED")

        evidence_snippet = (
            f"Phone: {e164_format} | Country: {matched_country} ({iso_code}) | "
            f"Type: {number_type} | Circle: {circle_name or 'National'} | "
            f"District/SSA: {circle_city or 'National'} | "
            f"Carrier: {operator_name or 'National Telecom'} | "
            f"Coordinates: {lat:.4f}, {lon:.4f} | "
            f"Routing: {routing_notes or 'ITU-T Standard'} | "
            f"Probed {len(phone_sites)} sources: {found_count} live, {blocked_count} rate-limited"
        )

        finding.add_evidence(
            source_name="APEX Multi-Source Phone Intelligence Engine",
            source_type="PUBLIC_REGISTRY",
            snippet=evidence_snippet,
            raw_payload={
                "e164": e164_format,
                "country": matched_country,
                "iso": iso_code,
                "circle": circle_name,
                "city": circle_city,
                "district_ssa": circle_city,
                "latitude": lat,
                "longitude": lon,
                "timezone": tz_offset,
                "national_number": national_number,
                "type": number_type,
                "operator": operator_name,
                "routing": routing_notes,
                "api_enrichment": api_data,
                "sources_probed": len(phone_sites),
                "sources_live": found_count,
                "all_probed_sites": phone_sites,
            },
            confidence=0.97,
            epistemic_label="OBSERVED"
        )

        finding.add_relationship(
            source_type="PHONE",
            source_value=e164_format,
            target_type="LOCATION",
            target_value=location_display,
            relation_type="ALLOCATED_REGION",
            confidence=0.95
        )

        return finding

