
import streamlit as st
import streamlit_folium
from openrouteservice import client
import folium




st.image('logo.png', width = 500)
st.header('Isochrome Mapping')


form = st.form(key="annotation")
with form:
    cols = st.columns((1,1))
    address = cols[0].text_input('Please enter the address:')
    time = cols[1].slider("Travel time:", 1, 30, 10)
    submitted = st.form_submit_button(label="Submit")



#Geocoding
key = '5b3ce3597851110001cf624896366d86ef2d40439d52f50412724477'
ORS = client.Client(key=key)

location = ORS.pelias_search(text=address, size= 1, country='GBR', sources=['osm'])


mode = ["driving-car", "driving-hgv", "foot-walking",
        "foot-hiking", "cycling-regular", "cycling-road", "cycling-mountain",
        "cycling-electric"]


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

c1, c2, c3 = st.beta_columns((1, 3, 1))
c2.title('Catchment Area Map')

map1 = folium.Map(tiles='OpenStreetMap', location= coords_r, zoom_start=13 , title= 'Map',control_scale = True, attr='Nene Valley Transport Planning', width=1200, height=700)


folium.features.GeoJson(iso_car, name= iso_car['metadata']['query']['profile'],
style_function=lambda feature: {
        'fillColor': 'blue',
        'color' :'blue' }).add_to(map1) # Add GeoJson to map

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

with c2:
    streamlit_folium.folium_static(map1,width=8000, height=2000)
