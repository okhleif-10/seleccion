import pandas as pd
import requests
from urllib.parse import quote
import re
from bs4 import BeautifulSoup
import pycountry
from collections import defaultdict

# Load FIFA rankings dataset from assets folder
def load_fifa_rankings():
    return pd.read_csv("assets/fifa_rankings.csv")

# Load FIFA rankings dataset and add row to label confederations
def get_federations():
    df = pd.read_csv("assets/fifa_rankings.csv")

    confed = defaultdict(dict)
    for _, row in df.iterrows():
        confed[row["confederation"]][row["Country"]] = row["Display"]

    return confed

# Load FIFA Rankings dataset and return the ordered rankings
def get_rankings():
    df = pd.read_csv("assets/fifa_rankings.csv")
    table = pd.DataFrame(df)
    table.sort_values(by='rank', inplace=True)
    rankings = table["country_full"].to_list()

    return rankings

# Get country flag with pycountry when given country name
def get_flag(country_name):
    manual_flags = {
        "England": "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
        "Scotland": "🏴󠁧󠁢󠁳󠁣󠁴󠁿",
        "Wales": "🏴󠁧󠁢󠁷󠁬󠁳󠁿",
        "Northern Ireland": "🇬🇧",
        "Cape Verde": "🇨🇻",
        "DR Congo": "🇨🇩",
        "Ivory Coast": "🇨🇮",
        "US Virgin Islands": "🇻🇮",
        "Macau": "🇲🇴",
        "Niger": "🇳🇪",
        "Kosovo": "🇽🇰",
        "Palestine": "🇵🇸",
        "Taiwan": "🇹🇼",
        "Türkiye": "🇹🇷",
        "Turkey": "🇹🇷",
        "Tahiti": "🇵🇫",
        "United Kingdom": "🇬🇧"
    }

    if country_name in manual_flags:
        return manual_flags[country_name]
    else:
        try:
            country = pycountry.countries.search_fuzzy(country_name)[0]
            return chr(127397 + ord(country.alpha_2[0])) + chr(127397 + ord(country.alpha_2[1]))
        except:
            return "🌍"

# Format each country name with [Flag] [Country Name]
def format_country_with_flag(rankings):
    return [f"{get_flag(country)} {country}" for country in rankings]

# Translates html flag from wiki table to emoji flag (for club flags)
def get_flag_from_img(cell):
    flag_span = cell.find("span", class_="flagicon")
    if flag_span and flag_span.img and flag_span.img.has_attr("alt"):
        return get_flag(flag_span.img["alt"])
    return "🌍"

# Alternative function to get the flag from the club cell
def extract_club_with_flag(cell):
    flag_img = cell.find("img")
    flag_html = ""
    if flag_img and flag_img.has_attr("src"):
        src = flag_img["src"]
        flag_url = f"https:{src}" if src.startswith("//") else src
        flag_html = f'<img src="{flag_url}" width="20" style="vertical-align: middle; margin-right: 6px;">'

    club_name = cell.get_text(strip=True)
    return f"{flag_html}{club_name}"

# Gets the wiki table that contains squad
def find_squad_table(tables):
    for table in tables:
        # Flatten MultiIndex if needed
        if isinstance(table.columns, pd.MultiIndex):
            table.columns = [' '.join(col).strip() for col in table.columns.values]

        cols = table.columns.astype(str).str.lower()
        if any("player" in col for col in cols) and any("caps" in col for col in cols):
            return table
    return None

# Fetches the correct wikipedia link for a given nation
def fetch_wikipedia_page(team):
    team_encoded = quote(team.replace(" ", "_"))
    if team == "United States" or team == "Australia":
        url = f'https://en.wikipedia.org/wiki/{team_encoded}_men\'s_national_soccer_team'
    elif team == "Sweden":
        url = f'https://en.wikipedia.org/wiki/Sweden_men\'s_national_football_team'
    else:
        url = f'https://en.wikipedia.org/wiki/{team_encoded}_national_football_team'
    response = requests.get(url)
    if response.status_code != 200:
        return None, None
    return response.text, BeautifulSoup(response.text, 'html.parser')

# Convert found squad table into pandas dataframe
def extract_squad_table(soup):
    html_tables = soup.find_all("table")
    df = None
    matched_table = None

    for table in html_tables:
        try:
            temp_df = pd.read_html(str(table))[0]
            if find_squad_table([temp_df]) is not None:
                df = temp_df
                matched_table = table
                break
        except Exception:
            continue

    return df, matched_table

# Add national flags for each club in the dataframe
def add_club_flags(df, matched_table):
    if matched_table and "Club" in df.columns:
        club_cells = []
        rows = matched_table.find_all("tr")[1:]

        for i, row in enumerate(rows):
            if i >= len(df):
                break
            cells = row.find_all(["td", "th"])
            if not cells:
                continue
            club_cell = cells[-1]
            flag = get_flag_from_img(club_cell)
            name = club_cell.get_text(strip=True)
            club_cells.append(f"{flag} {name}")

        df["Club"] = club_cells
    return df

# Get squad description context
def extract_squad_description(soup):
    section = soup.find(id="Current_squad") or soup.find(id="Players")
    if not section:
        return "<em>No squad context found for this team.</em>"

    heading = section.parent
    if not heading:
        return "<em>Section marker found but heading not located.</em>"

    content_parts = []
    for sibling in heading.find_next_siblings():
        if sibling.name == 'table':
            break
        if sibling.name in ['h2', 'h3', 'h4']:
            break
        if sibling.name in ['p', 'ul', 'ol', 'dl']:
            content_parts.append(str(sibling))
    description = "\n".join(content_parts)
    description = re.sub(r'\[[^\]]*?\]', '', description)
    return description

# Puts everything together
# Fetches wikipedia page, finds squad table, converts to dataframe, and formats
def fetch_team_squad(team):
    html, soup = fetch_wikipedia_page(team)
    if soup is None:
        return None, None

    df, matched_table = extract_squad_table(soup)
    if df is None:
        return None, None

    df = add_club_flags(df, matched_table)
    description = extract_squad_description(soup)

    # Clean the table
    df.dropna(how='all', inplace=True)
    df = df[~df.apply(lambda row: row.astype(str).str.strip().eq('').all(), axis=1)]
    if 'Player' in df.columns:
        df = df[df['Player'].notna() & df['Player'].astype(str).str.strip().ne('')]
    df.reset_index(drop=True, inplace=True)
    df.index += 1
    df.reset_index(drop=True, inplace=True)
    df.index += 1

    return df, description
