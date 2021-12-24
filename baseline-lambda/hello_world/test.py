from matplotlib.pyplot import legend
import psycopg2
import geopandas as gpd

from data import getLookupScotland, reportData
from map import getMap
from tables import getTable

conn = psycopg2.connect("postgres://postgres:S3vgvCA2fQdCccg@pg-1.ctnxr0jdghs2.eu-west-1.rds.amazonaws.com/mapapp")

df_reportdata = reportData(207)
df_lookup = getLookupScotland()
soildata = getMap(df_reportdata, None, df_lookup, 'nts-peatemissions')
print(soildata)