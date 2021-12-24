import random, pprint
import string
from shapely.geometry import shape, GeometryCollection
import pyproj
from shapely.geometry import Point
import matplotlib as mpl
import geopandas as gp
from shapely.ops import transform
from enum import Enum
from collections import namedtuple
from ordnance_survey_grid import grid_squares_for_rectangle
from lookup import landcover, soiltypes, biodiversity, naturenetworks
import numpy as np
import base64
import io 
from matplotlib_scalebar.scalebar import ScaleBar
import contextily as cx
from mpl_toolkits.axes_grid1 import make_axes_locatable
from matplotlib.patches import Patch
from matplotlib.colors import ListedColormap, BoundaryNorm

pyproj.datadir.get_data_dir()

FileType = namedtuple("FileType", "path name")
class Files(Enum):
    Landcover = FileType("stocks/landcover/","LCmap.tif")
    CarbonStorageTopsoil = FileType("es_flows/carbon_storage_topsoils/","gsoc.tif")
    FloodRisk = FileType("es_flows/veg_contribution_flood_risk/","water.tif")
    SoilErosion = FileType("es_flows/veg_contribution_soil_stabilisation/","E_scen-curr.tif")
    CarbonSeqNonWoodlands = FileType("es_flows/carbon_sequestration_nonwoodlands/","C_seq_nonforest.tif")
    CarbonSeqWoodlands = FileType("es_flows/carbon_sequestration_woodlands/","C_seq_forest.tif")
    CarbonStorageNonWoodlands = FileType("es_flows/carbon_storage_nonwoodlands/","C_stock_nonforest.tif")
    CarbonStorageWoodlands = FileType("es_flows/carbon_storage_woodlands/","C_stock_forest.tif")
    NatureNetworks = FileType("es_flows/important_vegetation_movement_biodiversity/","movement_bio.tif")
    Biodiversity = FileType("es_flows/important_habitat_for_biodiversity/","bio.tif")
    Pollination = FileType("es_flows/important_habitat_insect_pollinators/","PollinationService.tif")
    Recreation = FileType("es_flows/important_areas_recreation/","Recreation.tif")
    SoilTypes = FileType("stocks/soil_types/", "soiltype.tif")
    CanopyHeight = FileType("stocks/canopy_height/","Canopy_height.tif")
    Slope = FileType("stocks/slope/","slope.tif")
    Elevation = FileType("stocks/elevation/","DEM.tif")

data_path = "s3://ncr-geotiff-data/gb/v2/"

def addColourBar(ax, plt, data, title=None, highlow=False, hotspots=False):
    if np.isnan(data).all():
        patches = []
        patches.append(Patch(color="white", label="No Data"))
        ax.legend(handles=patches,
            bbox_to_anchor=(1, 1),
            loc=2,
            facecolor="white",
            frameon=False,
            fontsize=4)
        return ax
    min=np.nanmin(data)
    max=np.nanmax(data)
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="2%", pad=0.05)
    
    if highlow:
        if hotspots:
            ticks = [0,8]
            min = 0
            max = 8
        else:    
            ticks = [min, max]
        norm = mpl.colors.Normalize(vmin=min, vmax=max)
        cbar = plt.colorbar(mpl.cm.ScalarMappable(norm=norm, cmap='viridis_r'), cax=cax, ticks=ticks)
        cbar.ax.set_yticklabels(['Low','High'])
    else:
        ticks = [min, max]
        norm = mpl.colors.Normalize(vmin=min, vmax=max)
        cbar = plt.colorbar(mpl.cm.ScalarMappable(norm=norm, cmap='viridis_r'), cax=cax)
        cbar.ax.tick_params(labelsize=5)
    if title:
        cbar.ax.set_ylabel(title, labelpad=6, rotation=270, fontsize=5) 
    cbar.outline.set_visible(False)
    return ax

def addLegend(ax, values, colours, names, water=False, ncols=3):
    bands = []
    patches = []
    cols = []
    for count, i in enumerate(values):
        bands.append(i)
        colour = colours[count]
        name = names[count] 
        patches.append(Patch(color=colour,label=name))
        cols.append(colour)
    bands.append(9999999)
    cmap = ListedColormap(cols)
    norm = BoundaryNorm(bands, len(bands))
    if water:
        patches.append(Patch(color="#1F77B2", label="Waterways"))
    sorted_patches = sorted(patches, key=lambda x: x.get_label())
    ax.legend(handles=sorted_patches,
        loc="upper left",
        bbox_to_anchor=(0, -0), 
        ncol= ncols,
        facecolor="white",
        frameon=False,
        fontsize=6)
    return ax, cmap, norm

def addBasemap(ax):
    #baseimage = cx.providers.CartoDB.Positron
    baseimage = cx.providers.Esri.WorldImagery
    cx.add_basemap(ax, source=baseimage, crs="EPSG:27700", zorder=1, alpha=0.3, attribution_size=2)
    return ax

def addGeoJSON(ax, geojson):
    df = gp.GeoDataFrame.from_features(geojson, crs=4326)
    df.to_crs(crs=27700, inplace=True)
    df.plot(ax=ax)
    return ax

def generateReportId():
    length = 5
    letters = string.ascii_lowercase
    result_str = ''.join(random.choice(letters) for i in range(length))
    return result_str

def addScalebar(ax):
    scalebar = ScaleBar(1, "m", length_fraction=0.25, font_properties={'size': 6}, border_pad=0.3)
    ax.add_artist(scalebar)
    return ax

def processGeoJSON(geojson):
    featuresWGS84 = [feature["geometry"] for feature in geojson["features"]]  
    shapesWGS84 = GeometryCollection([shape(feature) for feature in featuresWGS84])
    boundsWGS84 = shapesWGS84.bounds
    wgs84 = pyproj.CRS('EPSG:4326')
    osgb = pyproj.CRS('EPSG:27700')
    project = pyproj.Transformer.from_crs(wgs84, osgb, always_xy=True).transform
    shapesOSGB = transform(project, shapesWGS84)
    boundsOSGB = shapesOSGB.bounds
    areaOSGB = shapesOSGB.area
    grids = list(grid_squares_for_rectangle(boundsOSGB))
    return shapesOSGB, boundsOSGB, areaOSGB, boundsWGS84, grids

def getData(datatype, grids, bounds, geom):
    data = Files[datatype]
    file = data.value
    tiffs = []
    for grid in grids:
        filename = F"{data_path}{file.path}{grid}/{file.name}"
        print("loading ", filename)
        tiffs.append(filename)
    out_array, out_transform = merge.merge(tiffs, bounds=bounds, nodata=-9999)
    masked_array = features.geometry_mask(geom[0], out_array[0].shape , out_transform, all_touched=False, invert=False)
    final_data = np.ma.array(out_array[0], mask = masked_array, fill_value=-9999)
    final_data = final_data.filled()
    shapes = features.shapes(final_data, mask=mask, transform=out_transform)
    pprint.pprint(next(shapes))
    return final_data.astype(float)

def toBase64(plt):
    pic_IObytes = io.BytesIO()
    plt.savefig(pic_IObytes, format='jpg', bbox_inches='tight', dpi=150)
    pic_IObytes.seek(0)
    pic_hash = base64.b64encode(pic_IObytes.getvalue()).decode("utf-8").replace("\n", "")
    return pic_hash

def landcoverNameFromId(id, lookup=None):
    codes = [id]
    filtered_values = lookup.query('id in @codes & type == "landcover"')
    print(filtered_values)
    if filtered_values.iloc[0]['name']:
        return filtered_values.iloc[0]['name']
    else:
        return None

def landcoverValuesFromId(id):
    return landcover.get(id, {}).get('values',{})

def landcoverColourFromId(id):
    return landcover.get(id, {}).get('colour',{})

def soiltypeNameFromId(id):
    return soiltypes.get(id, {}).get('name', '')

def soiltypeColourFromId(id):
    return soiltypes.get(id, {}).get('colour', '')

def bioClassNameFromId(id):
    return biodiversity.get(id, {}).get('name', '')

def bioClassColourFromId(id):
    return biodiversity.get(id, {}).get('colour', '') 

def natureNetworkNameFromId(id):
    return naturenetworks.get(id, {}).get('name', '')

def natureNetworkColourFromId(id):
    return naturenetworks.get(id, {}).get('colour', '') 
        

def getPixelAreaInHectares(count):
    return (count * 25) / 10000

def getPixelAreaInM2(count):
    return (count * 25) 