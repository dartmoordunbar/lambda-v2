import psycopg
import geopandas as gpd
import rasterio
from rasterio import features, merge, mask
from rasterio.io import MemoryFile
from shapely.geometry import MultiPolygon
import matplotlib.pyplot as plt
import contextily as cx
from matplotlib_scalebar.scalebar import ScaleBar
from mpl_toolkits.axes_grid1 import make_axes_locatable
from matplotlib.patches import Patch
import numpy as np
def create_dataset(data, crs, transform):
    memfile = MemoryFile()
    dataset = memfile.open(driver='GTiff', height=data.shape[0], width=data.shape[1], count=1, crs=crs, 
        transform=transform, dtype=data.dtype)
    dataset.write(data, 1)
    return dataset

def getRaster(df_datalist, grids, bounds, geom, lookup, types):
    data_array = []
    for index, row in df_datalist.iterrows():
        if index in types:
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
                for lookup_idx, lookup_row in df.iterrows():
                    masked_data[np.isin(masked_data, lookup_row["codes"])] = lookup_row["id"]
            return masked_data
def getLandcover(geom_id, aoi):
    data = getr
   
       
