import pydeck as pdk
import streamlit as st

# Ejemplo de datos de ubicación
ubicacion = {"lat": 38.2324, "lon": -103.9996, "alt": 948.6907}  # Datos de ejemplo

# Configuración del mapa en pydeck
view_state = pdk.ViewState(
    latitude=ubicacion["lat"],
    longitude=ubicacion["lon"],
    zoom=11,
    pitch=50,
)

# Capa para mostrar la ubicación como punto en el mapa
layer = pdk.Layer(
    "ScatterplotLayer",
    data=[ubicacion],
    get_position="[lon, lat]",
    get_color="[200, 30, 0, 160]",
    get_radius=200,
)

# Mapa de pydeck
mapa = pdk.Deck(
    layers=[layer],
    initial_view_state=view_state,
    tooltip={"text": "Ubicación: {lat}, {lon}"},
)

# Mostrar el mapa en Streamlit
st.pydeck_chart(mapa)
