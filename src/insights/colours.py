"""
Shared colour constants for all insight windows.

Standardized team colours (F1 2025 livery), tyre compound indicators,
and driver code-to-team mappings. Derived from official F1 livery
colours and standardised across the entire insights system.
"""

# ─── F1 Team Livery Colours (2025) ───

TEAM_COLOURS: dict[str, str] = {
    # Red Bull Racing
    "Red Bull Racing": "#3671C6",
    "Red Bull": "#3671C6",
    "RBR": "#3671C6",
    # Ferrari
    "Ferrari": "#E8002D",
    "FER": "#E8002D",
    # McLaren
    "McLaren": "#FF8000",
    "MCL": "#FF8000",
    # Mercedes
    "Mercedes": "#27F4D2",
    "MER": "#27F4D2",
    # Aston Martin
    "Aston Martin": "#225D4B",
    "AM": "#225D4B",
    # Alpine
    "Alpine": "#FF87BC",
    "ALP": "#FF87BC",
    # Williams
    "Williams": "#64C4FF",
    "WIL": "#64C4FF",
    # RB (formerly AlphaTauri)
    "RB": "#6099DA",
    "AlphaTauri": "#6099DA",
    "AT": "#6099DA",
    # Visor by Cash App (formerly Haas)
    "Visa Cash App RB": "#B6BABD",
    "VCARB": "#B6BABD",
    "Haas": "#B6BABD",
    "HAS": "#B6BABD",
    # Stake F1 Team (formerly Kick Sauber)
    "Stake F1 Team": "#52E252",
    "Stake": "#52E252",
    "Kick Sauber": "#52E252",
    "KSV": "#52E252",
    "Sauber": "#52E252",
    # Force India (historic)
    "Force India": "#FF66B2",
    "SAHARA FORCE INDIA": "#FF66B2",
    # Racing Point (historic)
    "Racing Point": "#F44336",
    # Red Bull 2 (Alt)
    "RBR2": "#3671C6",
    # Default / unknown
    "Unknown": "#888888",
}

# ─── Tyre Compound Colours (F1 official) ───

TYRE_COLOURS: dict[str, str] = {
    "S": "#E8002D",     # Soft - red
    "M": "#FFD100",     # Medium - yellow
    "H": "#FFFFFF",     # Hard - white
    "I": "#52E252",     # Intermediate - green
    "W": "#2156FF",     # Wet - blue
    "SOFT": "#E8002D",
    "MEDIUM": "#FFD100",
    "HARD": "#FFFFFF",
    "INTERMEDIATE": "#52E252",
    "WET": "#2156FF",
}

TYRE_LABELS: dict[str, str] = {
    "S": "SOFT",
    "M": "MEDIUM",
    "H": "HARD",
    "I": "INTERMEDIATE",
    "W": "WET",
}

# ─── Driver Code → Team mapping (with livery colour) ───

DRIVER_TEAM_MAP: dict[str, str] = {
    # Max Verstappen
    "VER": "Red Bull Racing",
    "MAX": "Red Bull Racing",
    # Checo Perez
    "PER": "Red Bull Racing",
    "SCOT": "Red Bull Racing",  # alternate mapping
    # Lewis Hamilton
    "HAM": "Ferrari",
    "LEW": "Ferrari",
    # Charles Leclerc
    "LEC": "Ferrari",
    "SHA": "Ferrari",
    # Carlos Sainz
    "SAI": "Ferrari",
    "CAR": "Ferrari",
    # Oscar Piastri
    "PIA": "McLaren",
    "OSCAR": "McLaren",
    # Lando Norris
    "NOR": "McLaren",
    "LANDO": "McLaren",
    # George Russell
    "RUS": "Mercedes",
    "GEORGE": "Mercedes",
    # Esteban Ocon
    "OCO": "Alpine",
    "EST": "Alpine",
    # Pierre Gasly
    "GAS": "Alpine",
    "PIERRE": "Alpine",
    # Fernando Alonso
    "ALO": "Aston Martin",
    "KAR": "Aston Martin",
    # Lance Stroll
    "STR": "Aston Martin",
    "LANCE": "Aston Martin",
    # Alexander Albon
    "ALB": "Williams",
    "ALEX": "Williams",
    # Logan Sargeant
    "SAR": "Williams",
    # Yuki Tsunoda
    "TSU": "RB",
    "YUK": "RB",
    # Daniel Ricciardo
    "RIC": "RB",
    "DAN": "RB",
    # Nico Hulkenberg
    "HUL": "Stake F1 Team",
    "NICO": "Stake F1 Team",
    # Kevin Magnussen
    "MAG": "Visa Cash App RB",
    "KEVIN": "Visa Cash App RB",
    # Oliver Bearman
    "BEA": "Stake F1 Team",
    "OLIVER": "Stake F1 Team",
    # Liam Lawson
    "LAW": "RB",
    "LIAM": "RB",
    # Franco Colapinto
    "COL": "Williams",
    "FRANCO": "Williams",
    # Guanyu Zhou
    "ZHO": "Stake F1 Team",
    "GUANYU": "Stake F1 Team",
    # Valter Bottas
    "BOT": "Stake F1 Team",
    "VALTTER": "Stake F1 Team",
    # Sergio Perez (alias)
    "CHECO": "Red Bull Racing",
}

# ─── Flags and event colours ───

FLAG_MAP: dict[int, str] = {
    0: "🟢",       # green
    4: "🟡",       # yellow
    5: "🔴",       # red
    11: "🟡🟡",    # double yellow
    8: "🟡",       # track limits
    14: "⚪",      # ice / gravel
}

# ─── Default / fallback colours ───

_DEFAULT_COL = "#999999"       # neutral grey for unknown
_LEADER_COLOUR = "#FFD700"     # gold for race leader
_POLE_COLOUR = "#E8002D"       # red for pole position
_DRS_COLOUR = "#00FF00"        # green for DRS active
