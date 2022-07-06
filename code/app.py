
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


draw = folium.plugins.Draw(export=True)
minimap = folium.plugins.MiniMap()


map1 = folium.Map(tiles='https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', 
        location= coords_r, zoom_start=13 , title= 'Map',control_scale = True, 
        attr='NVTP | © openrouteservice.org by HeiGIT | Map data © OpenStreetMap contributors')
#draw.add_to(map1)
map1.add_child(minimap)

folium.features.GeoJson(iso_car, name= iso_car['metadata']['query']['profile'],
style_function=lambda feature: {
        'fillColor': 'blue',
        'color' :'blue' },).add_to(map1) # Add GeoJson to map

folium.features.GeoJson(iso_walk, name= iso_walk['metadata']['query']['profile'],
style_function=lambda feature: {
        'fillColor': 'green',
        'color' :'green' }).add_to(map1) # Add GeoJson to map

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
streamlit_folium.folium_static(map1,height= 700)


#Geopandas plot

#Points to shalpely point 
points_Car= []
for i in iso_car['features'][0]['geometry']['coordinates'][0]:
    points_Car.append(shapely.geometry.Point(i[0], i[1]))

points_walk= []
for i in iso_walk['features'][0]['geometry']['coordinates'][0]:
    points_walk.append(shapely.geometry.Point(i[0], i[1]))

points_bike= []
for i in iso_bike['features'][0]['geometry']['coordinates'][0]:
    points_bike.append(shapely.geometry.Point(i[0], i[1]))

#json to geopandas

car = address_gdf
walk = address_gdf
bike = address_gdf

car['geometry'] = shapely.geometry.Polygon([[p.x, p.y] for p in points_Car])
car = car.set_crs(4326)
car = car.to_crs(3857)

walk['geometry'] = shapely.geometry.Polygon([[p.x, p.y] for p in points_walk])
walk = walk.set_crs(4326)
walk = walk.to_crs(3857)

bike['geometry'] = shapely.geometry.Polygon([[p.x, p.y] for p in points_bike])
bike = bike.set_crs(4326)
bike = bike.to_crs(3857)


location_df = gpd.GeoDataFrame(location['features'][0]['properties'], index=[0])
location_df['geometry'] = shapely.geometry.Point(coords[0],coords[1])
location_df.set_crs(4326, inplace=True)
location_df.to_crs(3857, inplace=True)


#Plot
st.subheader('Report Map')
with st.spinner('Processing...'):


        fig, ax = plt.subplots(figsize = (10,10), facecolor='white')

        if bool_car:
                car.plot(ax=ax ,alpha=0.2, edgecolor='blue', lw=4,color = 'blue' )
                location_df.plot(ax=ax, edgecolor='k', markersize=50, label='Car', color = 'blue')

        if bool_walk:
                walk.plot(ax=ax ,alpha=0.2, edgecolor='green', lw=4, color='green' )
                location_df.plot(ax=ax, edgecolor='k', markersize=50, label='Walk', color='green')

        if bool_bike:
                bike.plot(ax=ax ,alpha=0.2, edgecolor='orange', lw=4, color = 'orange')
                location_df.plot(ax=ax, edgecolor='k', markersize=50, label='Bike', color='orange')


        location_df.plot(ax=ax, color='red', edgecolor='k', markersize=70, label='Location')

        cx.add_basemap(ax, url = cx.providers.OpenStreetMap.Mapnik, reset_extent=True, interpolation='sinc')


        props = dict(boxstyle='round', facecolor='white', alpha=0.8)
        cx.add_attribution(text='Nene Valley Transport Planning | \n© openrouteservice.org by HeiGIT | Map data © OpenStreetMap contributors ', 
        ax=ax,bbox=props)

        plt.title(name+' - Isochrome Catchment '+str(time)+'mins', fontweight='bold')

        ax.add_artist(
        ScaleBar(1, dimension="si-length", 
        units="m",location='lower right',
        color='k', 
        box_color='white',
        box_alpha=0.8)
        )

        #Now making a nice legend
        ax.legend(loc='upper left', prop={'size': 10})

        st.pyplot(fig)


