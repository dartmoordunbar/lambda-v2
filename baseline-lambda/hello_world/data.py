import geopandas as gpd
import psycopg2, rasterio, pandas,json
from psycopg2.extras import Json
import numpy as np
from rasterio import features, merge, mask
from rasterio.io import MemoryFile
from rasterio.crs import CRS

conn = psycopg2.connect("postgres://postgres:S3vgvCA2fQdCccg@pg-1.ctnxr0jdghs2.eu-west-1.rds.amazonaws.com/mapapp")

def listClients():
    sql = """
        select id, name, client_name from aoi_client
        """
    df_aoilist = pandas.read_sql(sql, conn)
    
    
    
def saveTableData(report_id, data):
    print("Saving Data for report: ", report_id)
    data = str(data)
    newdata = data.replace('\'', '\"')
    cur = conn.cursor()
    sql = """
        insert into report_tabledata(id,report_id, data)
        values (1,%s,'%s')
    """
    values = (report_id, newdata)
    cur.execute(sql, values)
    cur.close()
    conn.close()
    return
def getMonuments(geom_id):
    sql= f"""
            select geom
            from
                palladiumscheduledmonuments
            where 
                ST_intersects(geom, (select geom from aoi_client where id = {geom_id}))
        """
    df = gpd.GeoDataFrame.from_postgis(sql, conn)  
    return df

def getWaterquality(geom_id):
    sql= f"""
        select ST_intersection(geom,(select geom from aoi_client where id = {geom_id})) as geom, wb_name, ov_class, eco_class, chem_class
        from "palladium-wfd-catchments" pwc
        where ST_intersects(geom, (select geom from aoi_client where id = {geom_id}))
    """
    df = gpd.GeoDataFrame.from_postgis(sql, conn)  
    return df

def getWaterquality(geom_id):
    sql= f"""
        select ST_intersection(geom,(select geom from aoi_client where id = {geom_id})) as geom, wb_name, ov_class, eco_class, chem_class
        from "palladium-wfd-catchments" pwc
        where ST_intersects(geom, (select geom from aoi_client where id = {geom_id}))
    """
    df = gpd.GeoDataFrame.from_postgis(sql, conn)  
    return df

def getScotWaterquality(geom_id):
    sql= f"""
        select ST_intersection(geom,(select geom from aoi_client where id = {geom_id})) as geom, ov_class20, eco_class_, chem_class
        from "client-scottishwater-waterquality" pwc
        where ST_intersects(geom, (select geom from aoi_client where id = {geom_id}))
    """
    df = gpd.GeoDataFrame.from_postgis(sql, conn)  
    return df
def getRivers(geom_id):
    sql = f"""
        select geom
        from gb_waterways_vector
        where 
        ST_intersects(geom, (select geom from aoi_client where id = {geom_id}))
    """
    df_rivers = gpd.GeoDataFrame.from_postgis(sql, conn)
    return df_rivers

def dataList():
    sql = "select * from report_data"
    df_maplist = pandas.read_sql(sql, conn)
    df = df_maplist.set_index('name')
    return df

#  select l.id, ll.display_name_ukhab_l3 as name, 'landcover' as type, array_agg(numcode) as codes, colour
# from lookup_landcover_nfnp ll
# left join lookup l on l.name = ll.display_name_ukhab_l3 
# group by l.id, ll.display_name_ukhab_l3, colour



def getLookup():
    lc_lookup_sql = """
  select ll.id, ll.name as name, 'landcover' as type, array_agg(code) as codes, colour, null as iswater, null as iswoodland
         from lookup_landcover ll
         group by ll.id, ll.name, colour
union
select st.id, st.name as name, 'soiltypes' as type, array_agg(code) as codes, colour, null as iswater, null as iswoodland
from lookup_soiltypes st 
group by st.id, st.name, colour
union
select bi.id, bi.name as name, 'biodiversity' as type, array_agg(code) as codes, colour, null as iswater, null as iswoodland
from lookup_biodiversity bi 
group by bi.id, bi.name, colour
union
select nn.id, nn.name as name, 'naturenetworks' as type, array_agg(code) as codes, colour, null as iswater, null as iswoodland
from lookup_naturenetworks nn 
group by nn.id, nn.name, colour
union
select sssi.id, sssi.name as name, 'sssi' as type, array_agg(code) as codes, colour, null as iswater, null as iswoodland
from lookup_sssi sssi 
group by sssi.id, sssi.name, colour;
    """
    # select nb.code as id, lb.name, 'ntsbio' as type, array_agg(numcode) as codes, lb.colour
        # from lookup_biodiversitynew nb 
        # left join lookup_biodiversity lb on nb.code = lb.id
        # group by nb.code, lb.name, colour;
    lc_lookup = pandas.read_sql(lc_lookup_sql, conn)
    return lc_lookup


def getLookupScotland():
    lc_lookup_sql = """
    select sc.id, ls.sw_display as name, 'landcover' as type, array_agg(geotiff_code) as codes, sc.colour as colour,ls.iswater,ls.iswoodland
    from "lookup-scotland-landcover" ls
    left join "lookup-scotland-landcover-colour" sc 
    on sc."name" = ls.sw_display 
    where sc.id is not null and ls.inscotland = 1
    group by ls.sw_display, sc.id, sc.colour,ls.iswater,ls.iswoodland
    union
    select st.id, st.name as name, 'soiltypes' as type, array_agg(code) as codes, colour, null as iswater, null as iswoodland
    from lookup_soiltypes st 
    group by st.id, st.name, colour
    union
    select bi.id, bi.name as name, 'biodiversity' as type, array_agg(code) as codes, colour, null as iswater, null as iswoodland
    from lookup_biodiversity bi 
    group by bi.id, bi.name, colour
    union
    select nn.id, nn.name as name, 'naturenetworks' as type, array_agg(code) as codes, colour, null as iswater, null as iswoodland
    from lookup_naturenetworks nn 
    group by nn.id, nn.name, colour
    union
    select sssi.id, sssi.name as name, 'sssi' as type, array_agg(code) as codes, colour, null as iswater, null as iswoodland
    from lookup_sssi sssi 
    group by sssi.id, sssi.name, colour;
    """
    lc_lookup = pandas.read_sql(lc_lookup_sql, conn)
    return lc_lookup
#######################################
##                                   ##
##    Scottish Water Landcover LU    ##
##                                   ##
#######################################




def reportData(geom_id):
    aoi_sql = f"""
       select 
            ac.*, rt.map_ids, rt.data_ids, rt.file_name as template_filename,
            (select array_agg(tile_name) from os_grid og where ST_intersects(geom, ac.geom)) as grids
        from aoi_client ac 
        left join report_templates rt on rt.id = ac.template_id 
        where ac.id =  {geom_id}
    """
    df_reportdata = gpd.GeoDataFrame.from_postgis(aoi_sql, conn) 
    return df_reportdata

def create_dataset(data, crs, transform):
    memfile = MemoryFile()
    dataset = memfile.open(driver='GTiff', height=data.shape[0], width=data.shape[1], count=1, crs=crs, 
        transform=transform, dtype=data.dtype)
    dataset.write(data, 1)
    return dataset

def mapData(df_datalist, grids, bounds, geom, lookup, data_list):
    min = max = codes = counts = names = colours = mean = None
    data_array = []
    for index, row in df_datalist.iterrows():
        if index in data_list:
            if (row['type'] == 'raster'):
                tiffs = []
                for grid in grids:
                    filename = F"{row['s3_path']}/{row['file_path']}/{grid}/{row['file_name']}"
                    print("Loading ", index, " for grid ", grid)
                    tiffs.append(filename)
                src = rasterio.open(tiffs[0])
                crs = src.crs
                out_array, out_transform = merge.merge(tiffs, bounds=bounds, nodata=-9999, dtype='float32')
                new_data = create_dataset(out_array[0], crs, out_transform)
                masked_data, masked_transform = mask.mask(new_data, geom, pad=False,all_touched=False,nodata=-9999, filled=True, crop=False)
                masked_data[masked_data == -9999] = np.nan #under zero and nan not needed
                if row['magnitude']:
                    print(f"Adjusting {index} using '{row['magnitude']}'")
                    masked_data = masked_data * float(row['magnitude'])
                if row['threshold']:
                    print(f"Applying threshold for  {index} using '{row['threshold']}'")
                    masked_data[masked_data < float(row['threshold'])] = np.nan
                if index in ['naturenetworks','landcover','biodiversity','soiltypes','sssi','ntsbio']: 
                    df = lookup.query('type == @index')
                    for lcindex, lcrow in df.iterrows():
                        masked_data[np.isin(masked_data, lcrow["codes"])] = int(lcrow["id"])
                    codes, counts = np.unique(masked_data[~np.isnan(masked_data)], return_counts=True)
                    filtered = df.query('id in @codes')
                    names = filtered['name'].tolist()
                    colours = filtered['colour'].tolist()


                # if index == 'landcover':
                #     df = lookup.query('type == "landcover"')
                #     print(df)
                #     for lcindex, lcrow in df.iterrows():
                #         masked_data[np.isin(masked_data, lcrow["codes"])] = lcrow["id"]
                #     codes, counts = np.unique(masked_data[~np.isnan(masked_data)], return_counts=True)
                #     filtered = df.query('id in @codes')
                #     names = filtered['name'].tolist()
                #     colours = filtered['colour'].tolist()
                # if index == 'soiltypes':
                #     df = lookup.query('type == "soiltype"')
                #     print(df)
                #     for lcindex, lcrow in df.iterrows():
                #         masked_data[np.isin(masked_data, lcrow["codes"])] = lcrow["id"]
                #     codes, counts = np.unique(masked_data[~np.isnan(masked_data)], return_counts=True)
                #     filtered = df.query('id in @codes')
                #     names = filtered['name'].tolist()
                #     colours = filtered['colour'].tolist()
                # if index == 'biodiversity':
                #     df = lookup.query('type == "biodiversity"')
                #     print(df)
                #     for lcindex, lcrow in df.iterrows():
                #         masked_data[np.isin(masked_data, lcrow["codes"])] = lcrow["id"]
                #     codes, counts = np.unique(masked_data[~np.isnan(masked_data)], return_counts=True)
                #     filtered = df.query('id in @codes')
                #     names = filtered['name'].tolist()
                #     colours = filtered['colour'].tolist()
                
                else:
                    min = np.nanmin(masked_data[0])
                    max = np.nanmax(masked_data[0])
                    mean = np.nanmean(masked_data[0])
                data_array.append({
                    "name": index,
                    "data": masked_data[0],
                    "min": min,
                    "max": max, 
                    "mean": mean,
                    "codes": codes, 
                    "names": names,
                    "counts": counts,
                    "colours": colours
                })
    df = pandas.DataFrame(data_array)
    df = df.set_index('name')
    return df    