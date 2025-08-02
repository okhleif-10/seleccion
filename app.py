# streamlit run app.py

import streamlit as st
from PIL import Image
import base64
from io import BytesIO
from logic import *


# --- Page setup
st.set_page_config(
    page_title="FIFA NT Squad Viewer",
    layout="wide",
    initial_sidebar_state="expanded"
)


fifa_logo = Image.open("assets/FIFA_logo_without_slogan.svg.png")

seleccion_logo = Image.open("assets/seleccion.png")
seleccion_logo = seleccion_logo.crop(seleccion_logo.getbbox())

# Helper to convert image to base64
def image_to_base64(img):
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

# Encode images
fifa_b64 = image_to_base64(fifa_logo)
seleccion_b64 = image_to_base64(seleccion_logo)

# Custom CSS to align logos and tighten layout
st.markdown("""
    <style>
    .logo-row {
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 20px;
        margin-bottom: 20px;
        margin-top: 30px;
    }
    h1 {
        margin-top: 5px !important;  /* 🔧 tighten space above title */
    }

    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

# Logos side by side
st.markdown(f"""
    <div class="logo-row">
        <img src="data:image/png;base64,{fifa_b64}" style="height:70px;" />
        <img src="data:image/png;base64,{seleccion_b64}" style="height:70px; margin-top:0px; margin-bottom:0px;" />
    </div>
""", unsafe_allow_html=True)

# Title centered below
st.markdown("<h1 style='text-align: center;'>National Football Team Squad Viewer</h1>", unsafe_allow_html=True)



if __name__ == '__main__':
    left, center, right = st.columns([2, 5, 2])


    with center:
        fifa_df = load_fifa_rankings()

        # --- Sorting Option ---
        sort_option = st.radio(
            "🔀 Sort teams by:",
            ["FIFA Ranking", "Alphabetical", "Federation"],
            horizontal=True
        )

        # --- Build Display List Based on Sorting ---
        if sort_option == "Federation":
            display_list = []
            option_to_country = {}

            for confed in sorted(fifa_df["confederation"].unique()):
                display_list.append(f"--{confed.upper()}--")
                confed_df = fifa_df[fifa_df["confederation"] == confed].sort_values("country_full")
                for _, row in confed_df.iterrows():
                    display_list.append(row["display"])
                    option_to_country[row["display"]] = row["country_full"]

        elif sort_option == "Alphabetical":
            display_list = fifa_df.sort_values("country_full")["display"].tolist()

        elif sort_option == "FIFA Ranking":
            display_list = fifa_df.sort_values("rank")["display"].tolist()

        selected_display = st.selectbox("Select a country", display_list, index=display_list.index("🇦🇷 Argentina"))

        # Skip if user selects a header
        if selected_display.startswith("--"):
            st.warning("Please select a country, not a header.")
            st.stop()

        # Extract country name from "🇪🇸 Spain"
        team = selected_display.split(" ", 1)[1]
        if team:
            df, context = fetch_team_squad(team)
            if df is not None:
                flag = get_flag(team)

                # Format numeric columns to remove decimals
                # Format numeric columns
                for col in ['No.', 'Caps', 'Goals']:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

                df.reset_index(drop=True, inplace=True)
                df.index += 1

                # --- Centering using columns ---
                left_col, center_col, right_col = st.columns([2, 5, 2])

                row_height = 34
                header_height = 38
                extra_padding = 30
                visible_height = df.shape[0] * row_height + header_height + extra_padding


            st.markdown(f"# {selected_display} National Football Team")

            if context:
                st.markdown("### 📝 Squad Context")
                st.markdown(context, unsafe_allow_html=True)
            st.dataframe(
                df.style
                    .format({
                    "No.": "{:.0f}",
                    "Caps": "{:.0f}",
                    "Goals": "{:.0f}"
                })
                    .set_properties(**{
                    'font-size': '14px',
                    'text-align': 'center'
                })
                    .set_table_styles([
                    {"selector": "th", "props": [("font-size", "15px"), ("text-align", "center")]},
                    {"selector": "td", "props": [("text-align", "center")]}
                ]),
                use_container_width=False,  # keep the fixed width
                height = visible_height
            )
            # Export option
            csv = df.to_csv().encode("utf-8")
            st.download_button("📥 Download CSV", csv, f"{team}_squad.csv", "text/csv")
        else:
            st.warning("Could not load squad for that country.")
