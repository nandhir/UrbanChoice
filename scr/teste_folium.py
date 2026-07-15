import folium

m = folium.Map(
    location=[-23.55, -46.63],
    zoom_start=12
)

m.save("teste.html")