
import geopandas as gpd 
import pandas as pd
import numpy as np
import requests
import json
import os
import sys 
import matplotlib.pyplot as plt
from openrouteservice import client
import folium
import shapely
import contextily as cx
from matplotlib_scalebar.scalebar import ScaleBar
import streamlit as st
import streamlit_folium


st.set_page_config(layout="wide", page_icon= 'house')

c1, c2, c3 = st.columns((1, 1, 1))
with c2:
        st.image('logo.png')
st.header('Isochrome Mapping')


form = st.form(key="annotation")
with form:
    cols = st.columns((3,1))
    address = cols[0].text_input('Please enter the address:', 'london eye')
    time = cols[1].slider("Travel time:", 1, 30, 10)
    bool_car= st.checkbox('Return Vehicle Catchment', True, help='Tick if you want car catchment')
    bool_walk = st.checkbox('Return Walking Catchment', True, help='Tick if you want walk catchment')
    bool_bike = st.checkbox('Return Cycling Catchment', True, help='Tick if you want bike catchment')
    submitted = st.form_submit_button(label="Submit")



#Geocoding
key = '5b3ce3597851110001cf624896366d86ef2d40439d52f50412724477'
ORS = client.Client(key=key)

location = ORS.pelias_search(text=address, size= 1, country='GBR', sources=['osm'])


mode = ["driving-car", "driving-hgv", "foot-walking",
        "foot-hiking", "cycling-regular", "cycling-road", "cycling-mountain",
        "cycling-electric"]


#json to geopandas
address_gdf =  gpd.GeoDataFrame(location['features'][0]['properties'], index=[0])

#ISO
iso_car = ORS.isochrones(
        locations= [location['features'][0]['geometry']['coordinates']], 
        range = [time*60], 
        range_type='time', 
        smoothing=1, 
        attributes=['reachfactor'],
        profile= mode[0]
)

iso_walk = ORS.isochrones(
        locations= [location['features'][0]['geometry']['coordinates']], 
        range = [time*60], 
        range_type='time', 
        smoothing=1, 
        attributes=['reachfactor'],
        profile= mode[2]
)

iso_bike = ORS.isochrones(
        locations= [location['features'][0]['geometry']['coordinates']], 
        range = [time*60], 
        range_type='time', 
        smoothing=1, 
        attributes=['reachfactor'],
        profile= mode[4]
)


#params

coords = location['features'][0]['geometry']['coordinates']
coords_r = list(reversed(location['features'][0]['geometry']['coordinates']))
name = location['features'][0]['properties']['label']


st.markdown(str('**Address Found:** '+ name))
st.markdown(str('**Travel time selected:** '+ str(time))+' minutes')



#Folim plot

st.subheader('Catchment Area Map')

with st.spinner('Processing...'):
        draw = folium.plugins.Draw(export=True)
        minimap = folium.plugins.MiniMap()


        map1 = folium.Map(tiles='https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', 
                location= coords_r, zoom_start=13 , title= 'Map',control_scale = True, 
                attr='NVTP | © openrouteservice.org by HeiGIT | Map data © OpenStreetMap contributors')
        #draw.add_to(map1)
        map1.add_child(minimap)


        if bool_car:
                folium.features.GeoJson(iso_car, name= iso_car['metadata']['query']['profile'],
                style_function=lambda feature: {
                        'fillColor': 'blue',
                        'color' :'blue' },).add_to(map1) # Add GeoJson to map
        
        if bool_walk:
                folium.features.GeoJson(iso_walk, name= iso_walk['metadata']['query']['profile'],
                style_function=lambda feature: {
                        'fillColor': 'green',
                        'color' :'green' }).add_to(map1) # Add GeoJson to map

        if bool_bike:
                folium.features.GeoJson(iso_bike, name= iso_bike['metadata']['query']['profile'],
                style_function=lambda feature: {
                        'fillColor': 'orange',
                        'color' :'orange' }).add_to(map1) # Add GeoJson to map

        folium.map.Marker(coords_r,  # reverse coords due to weird folium lat/lon syntax
                        icon=folium.Icon(color='lightgray',
                                        icon_color='#cc0000',
                                        icon='home',
                                        prefix='fa',
                                        ),
                        popup=name,
                        ).add_to(map1)


        loc = name+' - Isochrome Catchment '+str(time)+'mins'
        title_html = '''
                <h3 align="center" style="font-size:16px"><b>{}</b></h3>
                '''.format(loc)   


        map1.get_root().html.add_child(folium.Element(title_html))


        folium.LayerControl().add_to(map1)
        c1, c2, c3 = st.columns((1, 1, 1))
        with c1:
                streamlit_folium.folium_static(map1,height= 900, width=1300)

