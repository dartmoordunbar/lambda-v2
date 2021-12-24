import matplotlib.pyplot as plt
import matplotlib as mpl
import contextily as cx
import geopandas as gpd
import boto3, random, psycopg2, pandas
from numpy.core.fromnumeric import clip
from matplotlib_scalebar.scalebar import ScaleBar
from mpl_toolkits.axes_grid1 import make_axes_locatable
from matplotlib.patches import Patch
from matplotlib.colors import ListedColormap, BoundaryNorm
import numpy as np
from data import getMonuments, getRivers, getScotWaterquality, getWaterquality
from utils import landcoverNameFromId

s3 = boto3.client('s3')
conn = psycopg2.connect("postgres://postgres:S3vgvCA2fQdCccg@pg-1.ctnxr0jdghs2.eu-west-1.rds.amazonaws.com/mapapp")

def coverImage(reportData, lookup=None):
    bounds = tuple(reportData.total_bounds)
    left,bottom,right,top = bounds
    bounds_width = right-left
    bounds_height = top-bottom
    is_tall = True if bounds_height > bounds_width else False
    fig, ax = plt.subplots(dpi=300, figsize=(8, 8))
    plt.axis('off')
    if is_tall:
        pad = (bounds_height-bounds_width) * 0.05
        diff = (bounds_height-bounds_width) / 2
        plt.xlim(bounds[0]-diff-pad, bounds[2]+diff+pad)
        plt.ylim(bounds[1]-pad, bounds[3]+pad)
    else:
        pad = (bounds_width-bounds_height) * 0.05
        diff = (bounds_width-bounds_height) / 2
        plt.ylim(bounds[1]-diff-pad, bounds[3]+diff+pad)
        plt.xlim(bounds[0]-pad, bounds[2]+pad)
    addBasemap(ax, type='sat')
    plt.savefig('/tmp/cover.jpg', format='jpg', bbox_inches='tight', dpi=300)
    plt.close()
    return

def getMap(reportData, allData, lookup, type, format='jpg'):
    print("Generating Map for",type)
    geom_id = reportData['id'][0]
    return_data = None
    dpi = 300
    bounds = tuple(reportData.total_bounds)
    left,bottom,right,top = bounds
    bounds_width = right-left
    bounds_height = top-bottom
    is_tall = True if bounds_height > bounds_width else False
    fig, ax = plt.subplots(dpi=dpi, figsize=(8, 8))
    plt.axis('off')
    if is_tall:
        pad = (bounds_height-bounds_width) * 0.05
        diff = (bounds_height-bounds_width) / 2
        plt.xlim(bounds[0]-diff-pad, bounds[2]+diff+pad)
        plt.ylim(bounds[1]-pad, bounds[3]+pad)
    else:
        pad = (bounds_width-bounds_height) * 0.05
        diff = (bounds_width-bounds_height) / 2
        plt.ylim(bounds[1]-diff-pad, bounds[3]+diff+pad)
        plt.xlim(bounds[0]-pad, bounds[2]+pad)

    
    # map specific
    if type == 'elevation':
        data = allData.loc[type]['data']
        min = allData.loc[type]['min']
        max = allData.loc[type]['max']
        ax.imshow(data, extent=[bounds[0],bounds[2],bounds[1],bounds[3]],cmap='viridis_r',zorder=2, alpha=0.9, interpolation='nearest')
        addColourbar(ax,min,max,title='Elevation MASL(m)',cmaptype="viridis_r")
        addBasemap(ax, type='map')

    if type == 'slope':
        data = allData.loc[type]['data']
        min = allData.loc[type]['min']
        max = allData.loc[type]['max']
        ax.imshow(data, extent=[bounds[0],bounds[2],bounds[1],bounds[3]], cmap='viridis_r',zorder=2, alpha=0.9, interpolation='nearest')
        addColourbar(ax,min,max,title='Slope (%)',cmaptype="viridis_r")
        addBasemap(ax, type='map')

    if type == 'landcover':
        data = allData.loc[type]['data']
        codes = np.unique(data[~np.isnan(data)])
        filtered_list = lookup.query('id in @codes & type == "landcover"').drop_duplicates("name")
        ax, cmap, norm = addLegend(ax, filtered_list, ncols=3, patches=None)
        ax.imshow(data,extent=[bounds[0],bounds[2],bounds[1],bounds[3]],cmap=cmap, norm=norm, zorder=2, alpha=0.9,interpolation='none')
        addBasemap(ax, type='map')



    if type == 'canopyheight':
        data = allData.loc[type]['data']
        min = allData.loc[type]['min']
        max = allData.loc[type]['max']
        data[data <= 0] = np.nan #under zero and nan not needed
        im = ax.imshow(data,extent=[bounds[0],bounds[2],bounds[1],bounds[3]],zorder=2, cmap='viridis_r', alpha=0.9, interpolation='none')
        addColourbar(ax,min,max,title='Canopy Height (m)',cmaptype="viridis_r")
        addBasemap(ax, type='map')


    if type in ['soiltypes','biodiversity']:
        data = allData.loc[type]['data']
        data[data <= 0] = np.nan
        codes = allData.loc[type]['codes']
        filtered_list = lookup.query('id in @codes & type == @type')
        ax, cmap, norm = addLegend(ax, filtered_list, ncols=3, patches=None)
        ax.imshow(data,extent=[bounds[0],bounds[2],bounds[1],bounds[3]],cmap=cmap, norm=norm, zorder=2, alpha=0.9, interpolation='none')
        addBasemap(ax, type='map')


    if type == 'naturenetworks':
        data = allData.loc[type]['data']
        lc_data = allData.loc['landcover']['data']
        hedgerow_count = np.where(lc_data == 4)
        rows = hedgerow_count[0]
        cols = hedgerow_count[1]
        data[rows, cols] = 4.0
        codes = np.unique(data[~np.isnan(data)])
        filtered_list = lookup.query('id in @codes & type == "naturenetworks"')
        patches = None
        if len(filtered_list) == 1:
            cmap = ListedColormap(['white','#5a00eb'])
            norm = BoundaryNorm([9999999999, 4], 1)
            patches = [
                Patch(facecolor="white", linewidth=1 ,edgecolor="grey", label="No Data"),
                Patch(color="#c56d70", label="Hedgerows")
            ]
        ax, cmap, norm = addLegend(ax, filtered_list, ncols=4, patches=patches)
        if len(filtered_list) == 1:
            cmap = ListedColormap(['#5a00eb','white',])
            norm = BoundaryNorm([4.0, 9999999999], 2)
        ax.imshow(data,extent=[bounds[0],bounds[2],bounds[1],bounds[3]],cmap=cmap, norm=norm, zorder=2, alpha=0.9, interpolation='none')
        addBasemap(ax, type='map')


    if type in ['carbonstoragewoodlands','carbonstoragenonwoodlands','carbonstoragetopsoil']:
        data = allData.loc[type]['data']
        min = allData.loc[type]['min']
        max = allData.loc[type]['max']
        data[data <= 0] = np.nan
        im = ax.imshow(data,extent=[bounds[0],bounds[2],bounds[1],bounds[3]],zorder=2, cmap='viridis_r', alpha=0.9, interpolation='none')
        addColourbar(ax,min,max,title='Tonnes CO2e per hectare',cmaptype="viridis_r")
        addBasemap(ax, type='map')


    if type in ['carbonseqwoodlands','carbonseqnonwoodlands']:
        data = allData.loc[type]['data']
        min = allData.loc[type]['min']
        max = allData.loc[type]['max']
        data[data <= 0] = np.nan
        im = ax.imshow(data,extent=[bounds[0],bounds[2],bounds[1],bounds[3]],zorder=2, cmap='viridis_r', alpha=0.9, interpolation='none')
        addColourbar(ax,min,max,title='Tonnes CO2e per hectare per year',cmaptype="viridis_r")
        addBasemap(ax, type='map')
 
    if type == 'soilerosion':
        data = allData.loc[type]['data']
        min = allData.loc[type]['min']
        max = allData.loc[type]['max']
        data[data <= 0] = np.nan
        im = ax.imshow(data,extent=[bounds[0],bounds[2],bounds[1],bounds[3]],zorder=2, cmap='viridis_r', alpha=0.9, interpolation='none')
        addColourbar(ax,min,max,title='Tonnes soil loss avoided per hectare per year',cmaptype="viridis_r")
        addBasemap(ax, type='map')

    if type == 'sssi':
        data = allData.loc[type]['data']
        min = allData.loc[type]['min']
        max = allData.loc[type]['max']
        codes = allData.loc[type]['codes']
        filtered_list = lookup.query('id in @codes & type == @type')
        ax, cmap, norm = addLegend(ax, filtered_list, ncols=3, patches=None)
        im = ax.imshow(data,extent=[bounds[0],bounds[2],bounds[1],bounds[3]],zorder=2, norm=norm, cmap=cmap, alpha=0.9, interpolation='none')
        addBasemap(ax, type='map')
   
    if type == 'distinctiveness':
        data = allData.loc[type]['data']
        min = allData.loc[type]['min']
        max = allData.loc[type]['max']
        im = ax.imshow(data,extent=[bounds[0],bounds[2],bounds[1],bounds[3]],zorder=2, cmap='viridis_r', alpha=0.9, interpolation='none')
        addColourbar(ax,min,max,ticks=[0,2,4,6,8], labels=['Very Low','Low','Medium','High','Very High'], steps=5)
        addBasemap(ax, type='map')

    if type in ['vulnspecies']:
        data = allData.loc[type]['data']
        min = allData.loc[type]['min']
        max = allData.loc[type]['max']
        data[data <= 0] = np.nan
        im = ax.imshow(data,extent=[bounds[0],bounds[2],bounds[1],bounds[3]],zorder=2, cmap='viridis_r', alpha=0.9, interpolation='none')
        addColourbar(ax,min,max,ticks=[0,5], labels=['Low','High'])
        addBasemap(ax, type='map')
    




    if type == 'biocombined':
        distinctiveness = allData.loc['distinctiveness']['data']
        sssi = allData.loc['sssi']['data']
        vulnspecies = allData.loc['vulnspecies']['data']
        connectivity = allData.loc['connectivity']['data']
        lochwater = allData.loc['lochwater']['data']
        combined = []
        for iy, ix in np.ndindex(distinctiveness.shape):
            prod = []
            value = distinctiveness[iy, ix]
            if not np.isnan(value):
                prod.append(value)
            value = sssi[iy, ix]
            if not np.isnan(value):
                prod.append(value)
            value = vulnspecies[iy, ix]
            if not np.isnan(value):
                prod.append(value)
            value = lochwater[iy, ix]
            if not np.isnan(value):
                prod.append(value)
            value = connectivity[iy, ix]
            if not np.isnan(value):
                prod.append(value)
            if len(prod) == 0:
                combined[iy, ix] = np.nan
            else:
                combined[iy, ix] = np.prod(prod)
        #biocombined = distinctiveness * sssi * vulnspecies * connectivity * lochwater
        im = ax.imshow(combined,extent=[bounds[0],bounds[2],bounds[1],bounds[3]],zorder=2, cmap='viridis_r', alpha=0.9, interpolation='none')
        addColourbar(ax,0,100,ticks=[0,100], labels=['Low','High'])
        addBasemap(ax, type='map')


        ## table data
        return_data = []
        lc_data = allData.loc['landcover']['data']
        lc_values, lc_counts = np.unique(lc_data[~np.isnan(lc_data)], return_counts=True)
        return_data = []
        for count, i in enumerate(lc_values):
            name = landcoverNameFromId(i,lookup)
            sub_area = (lc_counts[count] * 25) / 10000
            sub_array = np.where(lc_data == i)
            class_array = biocombined[sub_array[0], sub_array[1]]
            sub_total = np.nansum(class_array) * sub_area
            return_data.append({
                "name": name,
                "area": sub_area,
                "total": sub_total
            })





    if type == 'floodrisk':
        data = allData.loc[type]['data']
        min = allData.loc[type]['min']
        max = allData.loc[type]['max']
        data[data <= 0] = np.nan
        im = ax.imshow(data,extent=[bounds[0],bounds[2],bounds[1],bounds[3]],zorder=2, cmap='viridis_r', alpha=0.9, interpolation='none')
        addColourbar(ax,min,max,title='Average m3 surface runoff avoided per hectare per year',cmaptype="viridis_r")
        addBasemap(ax, type='map')

    if type in ['recreation','pollination','bhrecreation']:
        data = allData.loc[type]['data']
        min = allData.loc[type]['min']
        max = allData.loc[type]['max']
        data[data <= 0] = np.nan
        im = ax.imshow(data,extent=[bounds[0],bounds[2],bounds[1],bounds[3]],zorder=2, cmap='viridis_r', alpha=0.9, interpolation='none')
        addColourbar(ax,min,max,ticks=[min,max], labels=['Low','High'],cmaptype="viridis_r")
        addBasemap(ax, type='map')

    
    if type in ['connectivity']:
        data = allData.loc[type]['data']
        min = allData.loc[type]['min']
        max = allData.loc[type]['max']
        data[data <= 0] = np.nan
        im = ax.imshow(data,extent=[bounds[0],bounds[2],bounds[1],bounds[3]],zorder=2, cmap='viridis_r', alpha=0.9, interpolation='none')
        addColourbar(ax,1,1.15,ticks=[1,1.1,1.15], labels=['Low','Medium','High'], steps=3,cmaptype="viridis_r")
        addBasemap(ax, type='map')

    if type == 'waterwetlands':
        data = allData.loc['landcover'].data
        rivers = getRivers(geom_id)
        filtered_list_ww = lookup.query('iswater == 1 & type == "landcover"')
        water_values = filtered_list_ww['id'].tolist()
        if len(water_values) < 1:
            water_values = [12,13,14,17,18,19]
        mask = np.isin(data, water_values)
        water_array = np.ma.masked_array(data, ~mask, fill_value=-9999)
        water_array = water_array.filled()
        water_array[water_array <= 0] = np.nan
        filtered = lookup.query('id in @water_values & type == "landcover"')
        lc_values = allData.loc['landcover'].codes
        filtered_water = filtered.query('id in @lc_values')
        ax, cmap, norm = addLegend(ax, filtered_water, patches=None, water=True)
        rivers.plot(ax=ax, zorder=20, legend=False, linewidth=1)
        im = ax.imshow(water_array,extent=[bounds[0],bounds[2],bounds[1],bounds[3]],cmap=cmap, norm=norm,zorder=2, alpha=0.9, interpolation='none')
        addBasemap(ax, type='map')

    if type == 'monuments':
        data = getMonuments(geom_id)
        data.plot(ax=ax, legend=False, alpha=1, edgecolor="#eb3471", color="white", facecolor="none", hatch="////")
        patches = [
            Patch(color="#eb3471", label="Scheduled Monuments"),
            Patch(color="#bada55", label="Report Area")
        ]
        ax, cmap, norm = addLegend(ax, None, ncols=2, patches=patches)
        addBasemap(ax, type='map')

    

    if type == 'studyarea':
        addBasemap(ax, type='sat')

    

    if type == 'heatmap':
        cstores_data = allData.loc['carbonstoragetopsoil'].data
        cstores_data[np.isnan(cstores_data)] = 0
        cstorew_data = allData.loc['carbonstoragewoodlands'].data
        cstorew_data[np.isnan(cstorew_data)] = 0
        cstorenw_data = allData.loc['carbonstoragenonwoodlands'].data
        cstorenw_data[np.isnan(cstorenw_data)] = 0
        carbonstore_total = cstorew_data + cstorenw_data + cstores_data
        carbonstore_total[carbonstore_total < 0] = np.nan
        carbonstore_max = np.nanmax(carbonstore_total) 
        carbonstore_std = carbonstore_total/carbonstore_max    ### carbon seq ###
        cseqw_data = allData.loc['carbonseqwoodlands'].data
        cseqw_data[np.isnan(cseqw_data)] = 0
        cseqnw_data = allData.loc['carbonseqnonwoodlands'].data
        cseqnw_data[np.isnan(cseqnw_data)] = 0
        carbonseq_total = cseqw_data + cseqnw_data
        carbonseq_total[carbonseq_total < 0] = 0
        carbonseq_max = np.max(carbonseq_total) 
        carbonseq_std = carbonseq_total/carbonseq_max
        se_data = allData.loc['soilerosion'].data
        se_data[np.isnan(se_data)] = 0
        erosion_max = np.max(se_data)
        erosion_final = se_data/erosion_max
        fp_data = allData.loc['floodrisk'].data
        fp_data[np.isnan(fp_data)] = 0
        flood_max = np.max(fp_data)
        if flood_max == 0:
            flood_final = 0
        else: 
            flood_final = fp_data/flood_max
        rec_data = allData.loc['recreation'].data
        rec_data[np.isnan(rec_data)] = 0
        recreation_max = np.nanmax(rec_data)
        if recreation_max == 0:
            recreation_final = 0
        else:
            recreation_final = rec_data/recreation_max
        pol_data = allData.loc['pollination'].data
        pol_data[np.isnan(pol_data)] = 0
        pollination_max = np.max(pol_data) 
        if pollination_max == 0:
            pollination_final = 0
        else:
            pollination_final = pol_data/pollination_max
        bio_data = allData.loc['biodiversity'].data
        bio_data[np.isnan(bio_data)] = 0
        biodiversity_final = np.where(bio_data > 0,1,0)
        nn_data = allData.loc['naturenetworks'].data
        nn_data[np.isnan(nn_data)] = 0
        connectivity_max = np.max(nn_data) 
        if connectivity_max == 0:
            connectivity_final = 0
        else:
            connectivity_final = nn_data/connectivity_max
        map_array = carbonstore_std + carbonseq_std + biodiversity_final + pollination_final + connectivity_final + flood_final + erosion_final + recreation_final
        map_array[map_array <= 0] = np.nan
        addColourbar(ax,0,8, ticks=[0,8], labels=['Low','High'],cmaptype="viridis_r")
        im = ax.imshow(map_array ,extent=[bounds[0],bounds[2],bounds[1],bounds[3]], cmap='viridis_r',zorder=2, alpha=0.9)
        addBasemap(ax, type='map')

    ############################################
    #####                                   ####
    #####      Water Quality                ####
    #####                                   ####
    ############################################

    if type == 'waterquality_overall':
        data = getWaterquality(geom_id)
        ecodata = data.dissolve(by='ov_class')
        waterPalette = {
            'Bad': '#FF0000',
            'Good': '#0000FF',
            'High': '#00FF00',
            'Moderate': '#FFFF00',
            'Not asses': '#FFFFFF',
            'Poor': '#FFA500'
        }
        patches = []
        for ctype, data in ecodata.groupby('ov_class'):
            color = waterPalette[ctype]
            patches.append(
                Patch(facecolor=color, linewidth=1 ,edgecolor="grey", label=ctype)
            )
            
            data.plot(
                alpha=0.9,
                color=color,
                ax=ax,
                label=ctype
            )
        
        ax, cmap, norm = addLegend(ax, None, ncols=4, patches=patches)
        addBasemap(ax, type='map')

    if type == 'scotwaterquality':
        data = getScotWaterquality(geom_id)
        ecodata = data.dissolve(by='eco_class_')
        waterPalette = {
            'Bad': '#FF0000',
            'Good': '#0000FF',
            'High': '#00FF00',
            'Moderate': '#FFFF00',
            'Not asses': '#FFFFFF',
            'Poor': '#FFA500'
        }
        patches = []
        for ctype, data in ecodata.groupby('eco_class_'):
            color = waterPalette[ctype]
            patches.append(
                Patch(facecolor=color, linewidth=1 ,edgecolor="grey", label=ctype)
            )
            
            data.plot(
                alpha=0.9,
                color=color,
                ax=ax,
                label=ctype
            )
        
        ax, cmap, norm = addLegend(ax, None, ncols=4, patches=patches)
        addBasemap(ax, type='map')


    if type == 'waterquality_eco':
        data = getWaterquality(geom_id)
        ecodata = data.dissolve(by='eco_class')
        waterPalette = {
            'Bad': '#FF0000',
            'Good': '#0000FF',
            'High': '#00FF00',
            'Moderate': '#FFFF00',
            'Not asses': '#FFFFFF',
            'Poor': '#FFA500'
        }
        patches = []
        for ctype, data in ecodata.groupby('eco_class'):
            color = waterPalette[ctype]
            patches.append(
                Patch(facecolor=color, linewidth=1 ,edgecolor="grey", label=ctype)
            )
            
            data.plot(
                alpha=0.9,
                color=color,
                ax=ax,
                label=ctype
            )
        
        ax, cmap, norm = addLegend(ax, None, ncols=4, patches=patches)
        addBasemap(ax, type='map')

    if type == 'waterquality_chem':
        data = getWaterquality(geom_id)
        ecodata = data.dissolve(by='chem_class')
        waterPalette = {
            'Fail': '#FF0000',
            'Good': '#0000FF',
            'High': '#00FF00',
            'Moderate': '#FFFF00',
            'Not asses': '#FFFFFF',
            'Poor': '#FFA500'
        }
        patches = []
        for ctype, data in ecodata.groupby('chem_class'):
            color = waterPalette[ctype]
            patches.append(
                Patch(facecolor=color, linewidth=1 ,edgecolor="grey", label=ctype)
            )
            
            data.plot(
                alpha=0.9,
                color=color,
                ax=ax,
                label=ctype
            )
        
        ax, cmap, norm = addLegend(ax, None, ncols=4, patches=patches)
        addBasemap(ax, type='map')

    ############################################
    #####                                   ####
    #####  Scottish Water - Water Quality   ####
    #####                                   ####
    ############################################
    
    if type == 'sw_waterquality_overall':

        sql= f"""
            select ST_intersection(geom,(select geom from aoi_client where id = {geom_id})) as geom, ov_class20
            from "data-scottishwater-waterquality" pwc
            where ST_intersects(geom, (select geom from aoi_client where id = {geom_id}))
            and ov_class20 is not null
        """
        df = gpd.GeoDataFrame.from_postgis(sql, conn)  
        df["ov_class20"].replace(
            {"Good ecological potential": "Good",
            "Moderate ecological potential": "Moderate",
            "Poor ecological potential": "Poor"
        }, inplace=True)
        waterPalette = {
            'Bad': '#FF0000',
            'Good': '#0000FF',
            'Good ecological potential':'#0000FF',
            'High': '#00FF00',
            'Moderate': '#FFFF00',
            'Moderate ecological potential': '#FFFF00',
            'Not asses': '#FFFFFF',
            'Poor': '#FFA500',
            'Poor ecological potential': '#FFA500'
        }
        patches = []
        for ctype, data in df.groupby('ov_class20'):
            color = waterPalette[ctype]
            patches.append(
                Patch(facecolor=color, linewidth=1 ,edgecolor="grey", label=ctype)
            )
            
            data.plot(
                alpha=0.9,
                color=color,
                ax=ax,
                label=ctype
            )
        
        ax, cmap, norm = addLegend(ax, None, ncols=4, patches=patches)
        addBasemap(ax, type='map')

    
    if type == 'sw_waterquality_eco':
        sql= f"""
            select ST_intersection(geom,(select geom from aoi_client where id = {geom_id})) as geom, eco_class_
            from "data-scottishwater-waterquality" pwc
            where ST_intersects(geom, (select geom from aoi_client where id = {geom_id}))
            and eco_class_ is not null
        """
        df = gpd.GeoDataFrame.from_postgis(sql, conn)  
        ecodata = df.dissolve(by='eco_class_')
        waterPalette = {
            'Bad': '#FF0000',
            'Good': '#0000FF',
            'High': '#00FF00',
            'Moderate': '#FFFF00',
            'Not asses': '#FFFFFF',
            'Poor': '#FFA500'
        }
        patches = []
        for ctype, data in ecodata.groupby('eco_class_'):
            color = waterPalette[ctype]
            patches.append(
                Patch(facecolor=color, linewidth=1 ,edgecolor="grey", label=ctype)
            )
            
            data.plot(
                alpha=0.9,
                color=color,
                ax=ax,
                label=ctype
            )
        
        ax, cmap, norm = addLegend(ax, None, ncols=4, patches=patches)
        addBasemap(ax, type='map')

    if type == 'sw_waterquality_chem':
        sql= f"""
            select ST_intersection(geom,(select geom from aoi_client where id = {geom_id})) as geom, chem_class
            from "data-scottishwater-waterquality" pwc
            where ST_intersects(geom, (select geom from aoi_client where id = {geom_id}))
            and chem_class is not null
        """
        df = gpd.GeoDataFrame.from_postgis(sql, conn)  
        ecodata = df.dissolve(by='chem_class')
        waterPalette = {
            'Fail': '#FF0000',
            'Good': '#0000FF',
            'Pass': '#0000FF',
            'High': '#00FF00',
            'Moderate': '#FFFF00',
            'Not asses': '#FFFFFF',
            'Poor': '#FFA500'
        }
        patches = []
        if not ecodata.empty:
            for ctype, data in ecodata.groupby('chem_class'):
                color = waterPalette[ctype]
                patches.append(
                    Patch(facecolor=color, linewidth=1 ,edgecolor="grey", label=ctype)
                )
                
                data.plot(
                    alpha=0.9,
                    color=color,
                    ax=ax,
                    label=ctype
                )
            
            ax, cmap, norm = addLegend(ax, None, ncols=4, patches=patches)
        addBasemap(ax, type='map')

    if type == 'deframetric':
        data = allData.loc[type]['data']
        data[data <= 0] = np.nan
        im = ax.imshow(data,extent=[bounds[0],bounds[2],bounds[1],bounds[3]],zorder=2,vmin=0,vmax=16, cmap='viridis_r', alpha=0.9, interpolation='none')
        addColourbar(ax, 0, 16, ticks=[0,16], labels=['Low','High'], steps=16)
        addBasemap(ax, type='map')
        ## table data for biodiversity
        lc_data = allData.loc['landcover']['data']
        lc_values, lc_counts = np.unique(lc_data[~np.isnan(lc_data)], return_counts=True)
        return_data = []
        for count, i in enumerate(lc_values):
            name = landcoverNameFromId(i,lookup)
            sub_area = (lc_counts[count] * 25) / 10000
            sub_array = np.where(lc_data == i)
            class_array = data[sub_array[0], sub_array[1]]
            sub_total = np.nansum(class_array) * sub_area
            return_data.append({
                "name": name,
                "area": sub_area,
                "total": sub_total
            })
        
    if type == 'lochwater':
        data = allData.loc[type]['data']
        data[data <= 0] = np.nan
        im = ax.imshow(data,extent=[bounds[0],bounds[2],bounds[1],bounds[3]],zorder=2,vmin=0,vmax=16, cmap='viridis_r', alpha=0.9, interpolation='none')
        addColourbar(ax, 1, 5, ticks=[1,2,3,4,5], labels=['Bad','Poor','Moderate','Good','High'], steps=5)
        addBasemap(ax, type='map')
        ## table data for biodiversity
        # lc_data = allData.loc['landcover']['data']
        # lc_values, lc_counts = np.unique(lc_data[~np.isnan(lc_data)], return_counts=True)
        # return_data = []
        # for count, i in enumerate(lc_values):
        #     name = landcoverNameFromId(i,lookup)
        #     sub_area = (lc_counts[count] * 25) / 10000
        #     sub_array = np.where(lc_data == i)
        #     class_array = data[sub_array[0], sub_array[1]]
        #     sub_total = np.nansum(class_array) * sub_area
        #     return_data.append({
        #         "name": name,
        #         "area": sub_area,
        #         "total": sub_total
        #     })
        
    ############################################
    #####                                   ####
    #####      NTS Maps                     ####
    #####                                   ####
    ############################################


    if type == 'nts-peatextent':
        sql = f"""
            select ST_union(ST_intersection(wkb_geometry,(select geom from aoi_client where id = {geom_id})))  as geom, peat
            from scotland_peatemissions sp
            where ST_intersects(wkb_geometry,(select geom from aoi_client where id = {geom_id}))
            and peat is not null
            group by peat;
        """
        df = gpd.GeoDataFrame.from_postgis(sql, conn) 
        palette = {
            '50.0': '#7CD250',
            '100.0': '#443983'
        }
        patches = []
        for ctype, data in df.groupby('peat'):
            color = palette[str(ctype)]
            label = str(ctype) + ' (CM)'
            patches.append(
                Patch(facecolor=color, linewidth=1 ,edgecolor="grey", label=label)
            )
            
            data.plot(
                alpha=0.9,
                color=color,
                ax=ax,
                label=ctype
            )
            
        ax, cmap, norm = addLegend(ax, None, ncols=4, patches=patches)
        addBasemap(ax, type='map')
        

    if type == 'nts-peatemissions':
        sql = f"""
            select ST_intersection(wkb_geometry,(select geom from aoi_client where id = {geom_id}))  as geom, emission
            from scotland_peatemissions sp
            where ST_intersects(wkb_geometry,(select geom from aoi_client where id = {geom_id}))
            and emission is not null
        """
        df = gpd.GeoDataFrame.from_postgis(sql, conn) 
        df.plot(
            alpha=0.75,
            column='emission',
            ax=ax,
            cmap='magma_r'
        )
        min = df['emission'].min() * -1
        max = df['emission'].max() * -1
        addColourbar(ax, min, max, title='Peatland sequestration (tCO2e/ha/yr)', cmaptype='magma')
        addBasemap(ax, type='map')

        ### table data ####
        sql = f"""
            select ST_area(ST_union(wkb_geometry)) / 10000 as area, avg(emission) as avg, peat_cond
            from scotland_peatemissions sp
            where ST_intersects(ST_intersection(wkb_geometry,(select geom from aoi_client where id = {geom_id})),(select geom from aoi_client where id = {geom_id}))
            and emission is not null
            group by peat_cond
        """
        df = pandas.read_sql(sql, conn)
        return_data = []
        
        for index, row in df.iterrows():
            area = row['area']
            name = row['peat_cond'].replace('_',' ')
            avg = row['avg'] * -1
            return_data.append({
                "name": name,
                "area": area,
                "total": (area * avg),
                "avg": avg
            })

    if type == 'nts-importantlandscapes':
        sql = f"""
            select ST_intersection(geom,(select geom from aoi_client ac where id = {geom_id} )) as geom, 'National Scenic Areas' as name
            from "data-nationalscenicareas" 
            where ST_intersects(geom,(select geom from aoi_client ac where id = {geom_id} ))
            union
            select ST_intersection(geom,(select geom from aoi_client ac where id = {geom_id} )) as geom, 'National Parks' as name
            from "data-nationalparks" 
            where ST_intersects(geom,(select geom from aoi_client ac where id = {geom_id} ))
            union
            select ST_intersection(geom,(select geom from aoi_client ac where id = {geom_id} )) as geom, 'World Heritage Sites' as name
            from "data-worldheritagesites" 
            where ST_intersects(geom,(select geom from aoi_client ac where id = {geom_id} ))
            union
            select ST_intersection(geom,(select geom from aoi_client ac where id = {geom_id} )) as geom, 'Gardens/Designed Landcapes' as name
            from "data-gardensdesignedlandscapes" 
            where ST_intersects(geom,(select geom from aoi_client ac where id = {geom_id} ))
            union
            select ST_intersection(geom,(select geom from aoi_client ac where id = {geom_id} )) as geom, 'Wild Areas' as name
            from "data-wildareas" 
            where ST_intersects(geom,(select geom from aoi_client ac where id = {geom_id} ))
        """

        df = gpd.GeoDataFrame.from_postgis(sql, conn)  
        ######################  facecolor, linecolor, hatch, linestyle
        alpha = 0.4
        palette = {
            'National Parks': ["#9BB460",'#9BB460',None,"-"],
            'National Scenic Areas': ["none",'#aaaaac',"XXXX","solid"],
            'World Heritage Sites': ["#1f1f1f",'#1f1f1f',None,"solid"],
            'Gardens/Designed Landcapes': ["#ead272",'#ead272',None,"solid"],
            'Wild Areas': ["#ead272",'#ead272',None,"solid"],
        }
        patches = []
        mpl.rcParams['hatch.linewidth'] = 0.3
        for ctype, data in df.groupby('name'):
            facecolour = mpl.colors.to_rgba(palette[ctype][0], alpha=alpha)
            edgecolour = mpl.colors.to_rgba(palette[ctype][1], alpha=alpha)
            linestyle = palette[ctype][3]
            hatch = palette[ctype][2]
            patches.append(
                Patch(edgecolor=edgecolour,facecolor=facecolour,linewidth=0.5,linestyle=linestyle ,hatch=hatch, label=ctype)
            )
            data.plot(
                facecolor=facecolour,
                linewidth=0.5,
                edgecolor=edgecolour,
                linestyle=linestyle,
                hatch=hatch,
                ax=ax,
                label=ctype
            )
        if len(patches) == 0:
            patches = False
        ax, cmap, norm = addLegend(ax, None, ncols=4, patches=patches)
        addBasemap(ax, type='map')

    if type == 'nts-protectedareas':
        sql = f"""
            select ST_intersection(geom,(select geom from aoi_client ac where id = {geom_id} )) as geom, 'SSSI' as name
            from "data-scotland-sssi" 
            where ST_intersects(geom,(select geom from aoi_client ac where id = {geom_id} ))
            union
            select ST_intersection(geom,(select geom from aoi_client ac where id = {geom_id} )) as geom, 'SPA' as name
            from "SPA_SCOTLAND"  
            where ST_intersects(geom,(select geom from aoi_client ac where id = {geom_id} ))
            union 
            select ST_intersection(geom,(select geom from aoi_client ac where id = {geom_id} )) as geom, 'SAC' as name
            from "SAC_SCOTLAND" 
            where ST_intersects(geom,(select geom from aoi_client ac where id = {geom_id} ))
            union 
            select ST_intersection(geom,(select geom from aoi_client ac where id = {geom_id} )) as geom, 'Biosphere Reserve' as name
            from "BIOSPH_SCOTLAND" 
            where ST_intersects(geom,(select geom from aoi_client ac where id = {geom_id} ))
            union 
            select ST_intersection(geom,(select geom from aoi_client ac where id = {geom_id} )) as geom, 'RAMSAR' as name
            from "RAMSAR_SCOTLAND" 
            where ST_intersects(geom,(select geom from aoi_client ac where id = {geom_id} ))
            union 
            select ST_intersection(geom,(select geom from aoi_client ac where id = {geom_id} )) as geom, 'LNCR' as name
            from "data-scotland-lncs" 
            where ST_intersects(geom,(select geom from aoi_client ac where id = {geom_id} ))
            union 
            select ST_intersection(geom,(select geom from aoi_client ac where id = {geom_id} )) as geom, 'LNR' as name
            from "data-scotland-lnr" 
            where ST_intersects(geom,(select geom from aoi_client ac where id = {geom_id} ))
            union 
            select ST_intersection(geom,(select geom from aoi_client ac where id = {geom_id} )) as geom, 'Priority Habitat' as name
            from "data-scotland-priorityhabitats" 
            where ST_intersects(geom,(select geom from aoi_client ac where id = {geom_id} ))
            union 
            select ST_intersection(geom,(select geom from aoi_client ac where id = {geom_id} )) as geom, 'Marine Protected' as name
            from "data-scotland-marineprotected" 
            where ST_intersects(geom,(select geom from aoi_client ac where id = {geom_id} ))
            union 
            select ST_intersection(geom,(select geom from aoi_client ac where id = {geom_id} )) as geom, 'Ancient Woodland' as name
            from "data-scotland-ancientwoodland" 
            where ST_intersects(geom,(select geom from aoi_client ac where id = {geom_id} ))
            union
            select ST_intersection(geom,(select geom from aoi_client ac where id = {geom_id} )) as geom, 'Wild Areas' as name
            from "data-wildareas" 
            where ST_intersects(geom,(select geom from aoi_client ac where id = {geom_id} ))
        """
       
        df = gpd.GeoDataFrame.from_postgis(sql, conn)  
        ### name, facecolor, linecolor, hatch
        palette = {
            'SPA': ["none",'#F2A456',None],
            'SAC': ["none",'#D6D6D7','XXX'],
            'Biosphere Reserve': ['#F6DFCD',"none",None],
            'RAMSAR': ["none",'#628FBE','ooo'],
            'LNCR': ["#B8FCAD", "none", None],
            'LNR': ["#CFCFD3", "none", "||||"],
            'SSSI': ["#344adb", "#344adb", None],
            'NNR': ["none", "#64FCEA", None],
            'Priority Habitat': ["none", "#63b662", "////"],
            'Marine Protected': ["#9fddd6", "#9fddd6", None],
            'Ancient Woodland': ["#BFCF50", "#BFCF50", None],
            # 'Gardens/Designed Landcapes': ["#ead272",'#ead272',None,"solid"],
            'Wild Areas': ["#ead272",'#ead272',None,"solid"],
        }
        alpha = 0.4
        patches = []
        mpl.rcParams['hatch.linewidth'] = 0.3
        for ctype, data in df.groupby('name'):
            facecolour = mpl.colors.to_rgba(palette[ctype][0], alpha=alpha)
            edgecolour = mpl.colors.to_rgba(palette[ctype][1], alpha=alpha)
            title = ctype
            hatch = palette[ctype][2]
            patches.append(
                Patch(edgecolor=edgecolour,facecolor=facecolour,linewidth=0.5 ,hatch=hatch, label=title)
            )
            data.plot(
                facecolor=facecolour,
                edgecolor=edgecolour,
                hatch=hatch,
                ax=ax,
                label=title
            )
        if len(patches) == 0:
            patches = None
        ax, cmap, norm = addLegend(ax, None, ncols=4, patches=patches)
        addBasemap(ax, type='map')
        

    if type == 'nts-importantandprotected':
        sql = f"""
            select ST_intersection(geom,(select geom from aoi_client ac where id = {geom_id} )) as geom, 'SSSI' as name
            from "data-scotland-sssi" 
            where ST_intersects(geom,(select geom from aoi_client ac where id = {geom_id} ))
            union
            select ST_intersection(geom,(select geom from aoi_client ac where id = {geom_id} )) as geom, 'SPA' as name
            from "SPA_SCOTLAND"  
            where ST_intersects(geom,(select geom from aoi_client ac where id = {geom_id} ))
            union 
            select ST_intersection(geom,(select geom from aoi_client ac where id = {geom_id} )) as geom, 'SAC' as name
            from "SAC_SCOTLAND" 
            where ST_intersects(geom,(select geom from aoi_client ac where id = {geom_id} ))
            union 
            select ST_intersection(geom,(select geom from aoi_client ac where id = {geom_id} )) as geom, 'Biosphere' as name
            from "BIOSPH_SCOTLAND" 
            where ST_intersects(geom,(select geom from aoi_client ac where id = {geom_id} ))
            union 
            select ST_intersection(geom,(select geom from aoi_client ac where id = {geom_id} )) as geom, 'RAMSAR' as name
            from "RAMSAR_SCOTLAND" 
            where ST_intersects(geom,(select geom from aoi_client ac where id = {geom_id} ))
            union 
            select ST_intersection(geom,(select geom from aoi_client ac where id = {geom_id} )) as geom, 'LNCR' as name
            from "data-scotland-lncs" 
            where ST_intersects(geom,(select geom from aoi_client ac where id = {geom_id} ))
            union 
            select ST_intersection(geom,(select geom from aoi_client ac where id = {geom_id} )) as geom, 'LNR' as name
            from "data-scotland-lnr" 
            where ST_intersects(geom,(select geom from aoi_client ac where id = {geom_id} ))
            union 
            select ST_intersection(geom,(select geom from aoi_client ac where id = {geom_id} )) as geom, 'Priority Habitat' as name
            from "data-scotland-priorityhabitats" 
            where ST_intersects(geom,(select geom from aoi_client ac where id = {geom_id} ))
            union 
            select ST_intersection(geom,(select geom from aoi_client ac where id = {geom_id} )) as geom, 'Marine Protected' as name
            from "data-scotland-marineprotected" 
            where ST_intersects(geom,(select geom from aoi_client ac where id = {geom_id} ))
            union 
            select ST_intersection(geom,(select geom from aoi_client ac where id = {geom_id} )) as geom, 'Ancient Woodland' as name
            from "data-scotland-ancientwoodland" 
            where ST_intersects(geom,(select geom from aoi_client ac where id = {geom_id} ))
            union
            select ST_intersection(geom,(select geom from aoi_client ac where id = {geom_id} )) as geom, 'National Scenic Areas' as name
            from "data-nationalscenicareas" 
            where ST_intersects(geom,(select geom from aoi_client ac where id = {geom_id} ))
            union
            select ST_intersection(geom,(select geom from aoi_client ac where id = {geom_id} )) as geom, 'National Parks' as name
            from "data-nationalparks" 
            where ST_intersects(geom,(select geom from aoi_client ac where id = {geom_id} ))
            union
            select ST_intersection(geom,(select geom from aoi_client ac where id = {geom_id} )) as geom, 'World Heritage Sites' as name
            from "data-worldheritagesites" 
            where ST_intersects(geom,(select geom from aoi_client ac where id = {geom_id} ))
        """
        df = gpd.GeoDataFrame.from_postgis(sql, conn)  
        ### name, facecolor, linecolor, hatch
        palette = {
            'SPA': ["none",'#F2A456',None,'solid'],
            'SAC': ["none",'#D6D6D7','XXX','solid'],
            'Biosphere': ['#F6DFCD',"none",None,'solid'],
            'RAMSAR': ["none",'#628FBE','ooo','solid'],
            'LNCR': ["#B8FCAD", "none", None,'solid'],
            'LNR': ["#CFCFD3", "none", "||||",'solid'],
            'SSSI': ["#344adb", "#344adb", None,'solid'],
            'NNR': ["none", "#64FCEA", None,'solid'],
            'Priority Habitat': ["none", "#63b662", "////",'solid'],
            'Marine Protected': ["#9fddd6", "#9fddd6", None,'solid'],
            'Ancient Woodland': ["#BFCF50", "#BFCF50", None,'solid'],
            'National Parks': ["#9BB460",'#9BB460',None,"-"],
            'National Scenic Areas': ["none",'#aaaaac',"XXXX","solid"],
            'World Heritage Sites': ["#1f1f1f",'#1f1f1f',None,"solid"],
        }
        alpha = 0.4
        patches = []
        mpl.rcParams['hatch.linewidth'] = 0.3
        for ctype, data in df.groupby('name'):
            facecolour = mpl.colors.to_rgba(palette[ctype][0], alpha=alpha)
            edgecolour = mpl.colors.to_rgba(palette[ctype][1], alpha=alpha)
            linestyle = palette[ctype][3]
            hatch = palette[ctype][2]
            patches.append(
                Patch(edgecolor=edgecolour,facecolor=facecolour,linewidth=0.5,linestyle=linestyle ,hatch=hatch, label=ctype)
            )
            data.plot(
                facecolor=facecolour,
                linewidth=0.5,
                edgecolor=edgecolour,
                linestyle=linestyle,
                hatch=hatch,
                ax=ax,
                label=ctype
            )
        if len(patches) == 0:
            patches = None
        ax, cmap, norm = addLegend(ax, None, ncols=4, patches=patches)
        addBasemap(ax, type='map')

    if type == 'scottishsoil':
        sql = f"""
            select mapsymb13, ST_UNION(ST_intersection(geom,(select geom from aoi_client ac where id = {geom_id} ))) as geom, 
            ST_area(ST_UNION(ST_intersection(geom,(select geom from aoi_client ac where id = {geom_id} )))) / 10000 as area
            from "data-scotland-soiltypes" dss 
            where ST_intersects(geom,(select geom from aoi_client ac where id = {geom_id} ))
            group by dss.mapsymb13;
        """
        df = gpd.GeoDataFrame.from_postgis(sql, conn)  
        palette = {
            'ALLU':['Alluvial soils','#FFFE65'],
            'CALC':['Calcareous soils','#B59750'],
            'EART':['Brown soils','#917B4B'],
            'HIP':['Humus-iron podzols','#F3C359'],
            'IMMA':['Immature soils','#5ec9fd'],
            'LOCH':['Lochs','#BDE1F5'],
            'MAGN':['Brown magnesian soils','#317289'],
            'MING':['Mineral gleys','#70D3F0'],
            'MONT':['Montane soils','#A3A0A2'],
            'PEAT':['Peat','#8B4477'],
            'PTYGLEY':['Peaty gleys','#80BD52'],
            'PTYPODZ':['Peaty podzols','#EB504E'],
        }
        alpha = 0.4
        patches = []
        return_data = []
        mpl.rcParams['hatch.linewidth'] = 0.3
        for ctype, data in df.groupby('mapsymb13'):
            facecolour = mpl.colors.to_rgba(palette[ctype][1], alpha=alpha)
            label = palette[ctype][0]
            patches.append(
                Patch(facecolor=facecolour,linewidth=0.5, label=label)
            )
            data.plot(
                facecolor=facecolour,
                linewidth=0.5,
                ax=ax,
                label=label
            )
            return_data.append({
                "name": label,
                "amount": data.iloc[0]['area']
            })
        if len(patches) == 0:
            patches = None
        ax, cmap, norm = addLegend(ax, None, ncols=4, patches=patches)
        addBasemap(ax, type='map')

    # shared final elements and save
    scalebar = ScaleBar(1, "m", length_fraction=0.25, font_properties={'size': 6}, border_pad=0.3)
    ax.add_artist(scalebar)
    reportData.plot(ax=ax,alpha=1, legend=False, zorder=3,  edgecolor="#bada55", facecolor="none")
    plt.savefig(f'/tmp/{type}.{format}', format=format, bbox_inches='tight', dpi=dpi)
    email = reportData['email'][0]
    report_title = reportData['name'][0]
    s3_name = report_title.replace(' ', '-')
    s3_name = s3_name.replace('/', '-')
    s3_key = f"{email}/{s3_name}/images/{type}.{format}"
    s3.upload_file(f"/tmp/{type}.{format}", "ncr-baseline-reports", s3_key)
    plt.close()
    return return_data

def addLegendTest(ax, data, ncols=3, patches=None, title=None, water=False):
    bands = []
    cols = []
    patches = []
    data = data.sort_values(by=['id'])
    for index, row in data.iterrows():
        bands.append(row['id'] - .5)
        cols.append(row['colour'])
        name = row['name']
        patches.append(Patch(fc=row['colour'],label=name,ec="grey",linewidth=0.25))
    cmap = ListedColormap(cols)
    norm = BoundaryNorm(bands, len(bands))
    sorted_patches = sorted(patches, key=lambda x: x.get_label())
    leg = ax.legend(handles=sorted_patches,
        loc="upper left",
        bbox_to_anchor=(0, -0),  
        ncol= ncols,
        frameon=False,
        title = title,
        title_fontsize=7,
        fontsize=6)
    leg._legend_box.align = "left"
    return ax, cmap, norm
    

def addLegend(ax, data, ncols=3, patches=None, title=None, water=False):
    cmap = norm = None
    bands = []
    cols = []
    if patches:
        patches = patches
    else:
        patches = []
        if water:
            patches.append(Patch(facecolor='#2270A0',linewidth=1 ,edgecolor="grey", label="Rivers and streams"))
        if data is None or data.empty or len(data) == 0:
            bands = [0]
            cols = ['white']
            patches.append(Patch(facecolor="white", linewidth=0.25, edgecolor="grey", label="No Data"))
        else:
            data = data.sort_values(by=['id'])
            for index, row in data.iterrows():
                bands.append(row['id'] - 0.5)
                colour = row['colour']
                name = row['name']
                patches.append(Patch(fc=colour,label=name,ec="grey",linewidth=0.25))
                cols.append(colour)
        bands.append(9999999)
        cmap = ListedColormap(cols)
        norm = BoundaryNorm(bands, len(bands))

    sorted_patches = sorted(patches, key=lambda x: x.get_label())
    leg = ax.legend(handles=sorted_patches,
        loc="upper left",
        bbox_to_anchor=(0, -0),  
        ncol= ncols,
        frameon=False,
        title = title,
        title_fontsize=7,
        fontsize=6)
    leg._legend_box.align = "left"
    return ax, cmap, norm
    

def addColourbar(ax, min, max, title=False, ticks=False, labels=False, steps=False, cmaptype=None):
    if cmaptype:
        cmap=cmaptype
    else: 
        cmap="viridis"
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="2%", pad=0.05)
    if steps:
        cmap=plt.cm.get_cmap(cmaptype, steps)
    if labels:
        norm = mpl.colors.Normalize(vmin=min, vmax=max)
        cbar = plt.colorbar(mpl.cm.ScalarMappable(norm=norm, cmap=cmap), cax=cax, ticks=ticks)
        cbar.ax.set_yticklabels(labels)
        cbar.ax.tick_params(labelsize=7) 
    else:
        norm = mpl.colors.Normalize(vmin=min, vmax=max)
        cbar = plt.colorbar(mpl.cm.ScalarMappable(norm=norm, cmap=cmap), cax=cax)
    
    cbar.ax.tick_params(labelsize=7)
    cbar.outline.set_visible(False)

    if title:
        cbar.ax.set_ylabel(title, labelpad=8, rotation=270, fontsize=7) 
    return ax
    




def addBasemap(ax, type='positron'):
    if type == 'sat':
        basemap = cx.providers.Esri.WorldImagery
    else:
        basemap = cx.providers.CartoDB.Positron
    cx.add_basemap(ax, source=basemap, crs="EPSG:27700", zorder=0, alpha=0.8, attribution_size=7)
    return ax

   