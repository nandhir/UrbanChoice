import geopandas as gpd

gdf = gpd.read_file("dados/Hospitais.gpkg")

print(gdf.geom_type.value_counts())
print(gdf.total_bounds)