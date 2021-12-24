from data import getLookupScotland, reportData, mapData, dataList, getLookup, saveTableData
from tables import getTable
from utils import bioClassNameFromId, landcoverNameFromId, soiltypeNameFromId
from map import coverImage, getMap
import os, time, jinja2, boto3, json, data_sources
import data_sources_nts as data_sources
from datetime import datetime
import numpy as np
from weasyprint import HTML
from dotenv import load_dotenv

s3 = boto3.client('s3')
ses = boto3.client('ses')

def lambda_handler(event, context):   
    load_dotenv()
    report_id = event["geom_id"]
    if not report_id:
        return
    
    df_datalist = dataList()
    df_reportdata = reportData(report_id)
    email = df_reportdata["email"][0] 
    area = int(df_reportdata.area) / 10000
    grids = df_reportdata["grids"][0]
    bounds = tuple(df_reportdata.total_bounds)
    report_title = df_reportdata["name"][0]
    template_filename = df_reportdata["template_filename"][0]
    map_ids = df_reportdata["map_ids"][0]
    data_ids = df_reportdata["data_ids"][0]
    geom = df_reportdata.geom
    area_coef = 0.0025
    templateDict = {}
    if template_filename == 'scottish-water':
        print("Using Scottish LandCover")
        df_lookup = getLookupScotland()
    if template_filename == 'nts':
        print("Using Scottish LandCover")
        df_lookup = getLookupScotland()
    else:
        print("Using GB LandCover")
        df_lookup = getLookup()
    print("Processing Report for:", report_title, "using template", template_filename)

    coverImage(df_reportdata)

    df_alldata = mapData(df_datalist, grids, bounds, geom, df_lookup, data_ids)
    ## Create Maps
    emtotal = 0
    for map in map_ids:
        response = getMap(df_reportdata, df_alldata, df_lookup, map, format='jpg')
        if map == 'deframetric':
            templateDict['biodiversitymetrics'] = response
        if map == 'scottishsoil':
            scot_soil = response
        if map == 'nts-peatemissions':
            emissions = []
            templateDict["emissiontable"] = response
            for item in response:
                emissions.append(item['total'])
            emtotal = sum(emissions)
            templateDict["table2emissions"] = {
                "total": emtotal,
                "avg": emtotal/area
            }

    ################
    #### TABLES ####
    ################
    lc_data = df_alldata.loc["landcover"].data
    lc_values, lc_counts = np.unique(lc_data[~np.isnan(lc_data)], return_counts=True)
    elevation_data = df_alldata.loc["elevation"].data
    slope_data = df_alldata.loc["slope"].data
    if template_filename != 'nts':
        soil_data = df_alldata.loc["soiltypes"].data
        soil_values, soil_counts = np.unique(soil_data[~np.isnan(soil_data)], return_counts=True)
    canopy_data = df_alldata.loc["canopyheight"].data
    cstores_data = df_alldata.loc["carbonstoragetopsoil"].data
    cstores_data[cstores_data <= 0] = np.nan
    cstores_values, cstores_counts = np.unique(cstores_data[~np.isnan(cstores_data)], return_counts=True)
    cstorew_data = df_alldata.loc["carbonstoragewoodlands"].data
    cstorenw_data = df_alldata.loc["carbonstoragenonwoodlands"].data
    cseqw_data = df_alldata.loc["carbonseqwoodlands"].data
    cseqnw_data = df_alldata.loc["carbonseqnonwoodlands"].data
    se_data = df_alldata.loc["soilerosion"].data
    fp_data = df_alldata.loc["floodrisk"].data
    rec_data = df_alldata.loc["recreation"].data
    pol_data = df_alldata.loc["pollination"].data
    pol_data[pol_data < 0.1] = np.nan
    bio_data = df_alldata.loc["biodiversity"].data
    bio_data[bio_data <= 0] = np.nan
    bio_values, bio_counts = np.unique(bio_data[~np.isnan(bio_data)], return_counts=True)
    nn_data = df_alldata.loc["naturenetworks"].data
    nn_values, nn_counts = np.unique(nn_data[~np.isnan(nn_data)], return_counts=True)

    filtered_list = df_lookup.query('iswoodland == 1 & type == "landcover"')
    woodland_values = filtered_list['id'].tolist()
    if len(woodland_values) < 1:
        woodland_values =  [5,6]


    filtered_list = df_lookup.query('iswater == 1 & type == "landcover"')
    water_values = filtered_list['id'].tolist()
    if len(water_values) < 1:
        water_values = [12,13,14,17,18,19]
    mask = np.isin(lc_data, water_values)
    water_array = np.ma.masked_array(lc_data, ~mask, fill_value=-9999)
    water_array = water_array.filled()
    water_array[water_array <= 0] = np.nan
    

    lc_total_area = 0
    lc_array = []
    table = {}
    lc_data = df_alldata.loc["landcover"].data
    lc_values, lc_counts = np.unique(lc_data[~np.isnan(lc_data)], return_counts=True)
    for count, i in enumerate(lc_values):
        lc_area = (lc_counts[count] * 25 )/ 10000
        lc_total_area = lc_total_area + lc_area
        name = landcoverNameFromId(i, df_lookup)
        lc_array.append({
            "id": i,
            "name": name,
            "amount": lc_area
        })
    table["landcover"] = sorted(lc_array, key = lambda i: i["name"])
   
    ### water
    table["water"] = [i for i in table["landcover"] if i["id"] in water_values]
    table["landcover"] = [i for i in table["landcover"] if i["id"] not in water_values]
    table["landcover_total_area"] = lc_total_area
    #### Topography ####
    average_elevation = np.nanmean(elevation_data)
    slope_data[slope_data <= 0] = np.nan
    average_slope = np.nanmean(slope_data)
    table["topography"] = [
        {"name": "Elevation", "amount": average_elevation, "unit": "m"},
        {"name": "Slope", "amount": average_slope, "unit": "%"}
    ]


    if template_filename == 'nts':
        table["soil"] = scot_soil
    else:
        soil_array = []
        for count, i in enumerate(soil_values):
            name = soiltypeNameFromId(i)
            st_area = (soil_counts[count] * 25) / 10000
            soil_array.append({
                "name":name,
                "amount":st_area
            })
        table["soil"] = sorted(soil_array, key = lambda i: i["name"])
    
    templateDict["table1"] = table



    
    #### Table A2

    array1 = []
    for canopy_class in woodland_values:
        sub_array = np.where(lc_data == canopy_class)
        ch_area = (len(sub_array[0]) * 25)/ 10000
        class_array = canopy_data[sub_array[0], sub_array[1]]
        if class_array.size:
            class_avg = np.nanmean(class_array)
            array1.append({ 
                "name": landcoverNameFromId(canopy_class, df_lookup),
                "area": ch_area,
                "avg_height": class_avg
            })
    templateDict["tableA2"] = sorted(array1, key = lambda i: i["name"])

    #### Table B1

    table = {}
    array1 = []
    array2 = []

    carbonstorwoodlands_area = 0
    carbonstorwoodlands_total = 0
    carbonstornonwoodlands_area = 0
    carbonstornonwoodlands_total = 0
    carbonstorwoodlands_avg = []
    carbonstornonwoodlands_avg = []

    for count, i in enumerate(lc_values):
        if i in woodland_values:
            name = landcoverNameFromId(i, df_lookup)
            sub_array = np.where(lc_data == i)
            class_array = cstorew_data[sub_array[0], sub_array[1]]
            csw_area = (lc_counts[count] * 25) / 10000
            carbonstorwoodlands_area = carbonstorwoodlands_area + csw_area
            total_co2 = (np.nansum(class_array) * 25) / 10000
            carbonstorwoodlands_total = carbonstorwoodlands_total + total_co2
            average_co2 = total_co2 / csw_area
            carbonstorwoodlands_avg.append(average_co2)
            array1.append({"name": name, "area": csw_area, "total": total_co2, "avg": average_co2})
        else:
            name = landcoverNameFromId(i, df_lookup)
            sub_array = np.where(lc_data == i)
            class_array = cstorenw_data[sub_array[0], sub_array[1]]
            csnw_area = (lc_counts[count] * 25 ) / 10000
            carbonstornonwoodlands_area = carbonstornonwoodlands_area + csnw_area
            total_co2 = (np.nansum(class_array) * 25) / 10000
            carbonstornonwoodlands_total = carbonstornonwoodlands_total + total_co2
            average_co2 = total_co2 / csnw_area
            carbonstornonwoodlands_avg.append(average_co2)
            array2.append({"name": name, "area": csnw_area, "total": total_co2, "avg": average_co2})

        table["carbstorwoodland"] = sorted(array1, key = lambda i: i["name"])
        table["carbstornonwoodland"] = sorted(array2, key = lambda i: i["name"])
        
        ##### SOIL #####
        total_soil = (np.nansum(cstores_data) * 25)  / 10000
        #area_soil = (cstores_counts[count] * 25)/10000
        #area_soil = np.count_nonzero(~np.isnan(cstores_data)) * 25 / 10000
        area_soil = (np.nansum(cstores_counts) * 25)  / 10000
        average_soil = total_soil/area_soil
        table["carbstorsoils"] = {"name": "Top 30cm of soil", "area": area_soil, "total": total_soil, "avg": average_soil}
        templateDict["tableB1"] = table
    
        # ############### table 2 ####################
        table = {}
        table["carbonstorage"] = [
            {"name": "Carbon storage in woodlands and forests", "total": carbonstorwoodlands_total, "average": carbonstorwoodlands_total/area},
            {"name": "Carbon storage in trees and vegetation outside of woodlands", "total": carbonstornonwoodlands_total, "average": carbonstornonwoodlands_total/area},
            {"name": "Carbon storage in topsoil", "total":total_soil, "average": total_soil/area}
        ]
        
        carbonstore_total = carbonstorwoodlands_total + carbonstornonwoodlands_total + total_soil
        table["carbonstoragetotal"] = {"name": "Carbon storage in vegetation and soils" ,"total": carbonstore_total, "average":carbonstore_total/area}
        templateDict["table2cstor"] = table

    #### Table B2

    ### get data
    
    table = {}
    array1 = []
    array2 = []
    carbonseqwoodlands_total = 0
    carbonseqwoodlands_area = 0
    carbonseqwoodlands_avg = []
    carbonseqnonwoodlands_total = 0
    carbonseqnonwoodlands_area = 0
    carbonseqnonwoodlands_avg = [] 
        
    for count, i in enumerate(lc_values):
        if i in  woodland_values:
            name = landcoverNameFromId(i,df_lookup)
            sub_array = np.where(lc_data == i)
            cseq_area = (lc_counts[count] * 25) / 10000
            carbonseqwoodlands_area = carbonseqwoodlands_area + cseq_area
            class_array = cseqw_data[sub_array[0], sub_array[1]]
            total_co2 = (np.nansum(class_array) * 25) / 10000
            carbonseqwoodlands_total = carbonseqwoodlands_total + total_co2
            average_co2 = total_co2 / cseq_area
            carbonseqwoodlands_avg.append(average_co2)
            array1.append({"name": name, "area": cseq_area, "total": total_co2, "avg": average_co2})
        else:
            name = landcoverNameFromId(i,df_lookup)
            sub_array = np.where(lc_data == i)
            class_array = cseqnw_data[sub_array[0], sub_array[1]]
            total_co2 = (np.nansum(class_array) * 25) / 10000
            cseq_area = (lc_counts[count] * 25 ) / 10000
            carbonseqnonwoodlands_area = carbonseqnonwoodlands_area + cseq_area
            carbonseqnonwoodlands_total = carbonseqnonwoodlands_total + total_co2
            average_co2 = total_co2 / cseq_area
            carbonseqnonwoodlands_avg.append(average_co2)
            array2.append({"name": name, "area": cseq_area, "total": total_co2, "avg": average_co2})
            
    table["carbseqwoodland"] = sorted(array1, key = lambda i: i["name"])
    table["carbseqnonwoodland"] = sorted(array2, key = lambda i: i["name"])
    table["carbonseqtotal"] = {
        "area":carbonseqnonwoodlands_area + carbonseqwoodlands_area, 
        "tonnes": carbonseqnonwoodlands_total + carbonseqwoodlands_total, 
        "average": carbonseqnonwoodlands_total/area + carbonseqwoodlands_total/area
    }
    templateDict["tableB2"] = table

    #### table 2
    ### sequestration
    table = {}
    table["carbonseq"] = [
        {"name": "Carbon sequestration in woodlands and forests",
        "total": carbonseqwoodlands_total,
        "average": carbonseqwoodlands_total/area
        },
        {"name": "Carbon sequestration in trees and vegetation outside of woodlands",
        "total": carbonseqnonwoodlands_total,
        "average": carbonseqnonwoodlands_total/area
        }
    ]
    table["carbonseqtotal"] = {
        "name": "Carbon sequestration in vegetation and soils",
        "total": carbonseqwoodlands_total + carbonseqnonwoodlands_total + emtotal,
        "average": carbonseqnonwoodlands_total/area + carbonseqwoodlands_total/area + emtotal/area
    }
    
    templateDict["table2cseq"] = table




    #### Table b3

    table = {}
    array1 = []
    total_tonnes = 0
    names = []
    areas = []
    tonnes = []
    averages = []
    percentages = []

    for count, i in enumerate(lc_values):
        name = landcoverNameFromId(i,df_lookup)
        names.append(name)
        se_area = (lc_counts[count] * 25) / 10000
        areas.append(se_area)
        sub_array = np.where(lc_data == i)
        class_array = se_data[sub_array[0], sub_array[1]]
        tonne = np.nansum(class_array) * area_coef
        tonnes.append(tonne)
        total_tonnes = total_tonnes + tonne
        averages.append(tonne / se_area)

    for i in tonnes:
        percentages.append((i/total_tonnes) * 100)
        
    arraylist = list(zip(names, areas, tonnes, averages, percentages))

    for i in arraylist:
        array1.append({"name": i[0], "area": i[1], "total": i[2], "avg": i[3], "percent":i[4]})
    total_avg = 0 if (sum(areas) == 0) else sum(tonnes)/sum(areas)
    table["soilerosion"] = sorted(array1, key = lambda i: i["name"])
    table["soiltotal"] = {"area": sum(areas), "tonnes": sum(tonnes), "percent": sum(percentages), "average": total_avg  }
    templateDict["tableB3"] = table
        

    #### table b4
    table = {}
    array1 = []
    names = []
    areas = []
    runoffs = []
    percentages = []
    
    for count, i in enumerate(lc_values):
        name = landcoverNameFromId(i,df_lookup)
        names.append(name)
        fp_sub_array = np.where(lc_data == i)
        fp_class_array = fp_data[fp_sub_array[0], fp_sub_array[1]]
        runoff = (np.nansum(fp_class_array) * 25) / 10000
        if i not in woodland_values:
        #     runoffs.append(0)
        #     areas.append(0)
        #     averages.append(0)
        # else:
            fp_area = (fp_class_array.shape[0] * 25) / 10000
            #fp_area = (np.count_nonzero(~np.isnan(class_array)) * 25) / 10000
            areas.append(fp_area)
            runoffs.append(runoff)
            average = runoff/fp_area 
            averages.append(average)

    for i in runoffs:
        percentages.append((i/sum(runoffs)) * 100)

    arraylist = list(zip(names, areas, runoffs, averages, percentages))
        
    for i in arraylist:
        array1.append({"name": i[0], "area": i[1], "total": i[2], "avg": i[2]/i[1], "percent":i[4]})
    
    avg = 0 if (sum(areas) == 0) else sum(runoffs)/sum(areas)
    table["floodprevention"] = sorted(array1, key = lambda i: i["name"])
    table["floodtotal"] = {"area": sum(areas), "tonnes": sum(runoffs), "percent": sum(percentages), "average": avg}
    templateDict["tableB4"] = table



    ###### table b5
    pol_data[pol_data < 0.1] = np.nan
    table = {}
    array1 = []
    areas = []
    percentages = []
    percentages = []
    for count, i in enumerate(lc_values):
        name = landcoverNameFromId(i,df_lookup)
        sub_array = np.where(lc_data == i)
        class_array = pol_data[sub_array[0], sub_array[1]]
        pol_area = (np.count_nonzero(~np.isnan(class_array)) * 25) / 10000
        percent = (pol_area/area) * 100
        percentages.append(percent)
        areas.append(pol_area)
        array1.append(
            {"name": name, "area": pol_area, "percent": (pol_area/area) * 100}
        )

    table['pollination'] = array1
    table["pollinationtotal"] = {
        "area": float(sum(areas)),
        "percent": float(sum(percentages))
    }
   
    templateDict["tableB5"] = table

    ###### table b6

    table = {}
    array1 = []
    bio_areas = []
    percentages = []
    for count, i in enumerate(bio_values):

        name = bioClassNameFromId(i)
        bio_area = (bio_counts[count] * 25) / 10000
        bio_areas.append(bio_area)
        total_area = area
        percent = (bio_area/total_area) * 100
        percentages.append(percent)
        array1.append({"name": name, "area": bio_area, "percent": percent })


    table["biodiversity"] = sorted(array1, key = lambda i: i["name"])
    table["totals"] = {
        "area": sum(bio_areas),
        "percent": sum(percentages)
    }

    templateDict["tableB6"] = table

        
    
    if template_filename == 'scottish-water':
        #### distinctiveness table
        distinctiveness_data = df_alldata.loc['distinctiveness'].data
        array = []
        for count, i in enumerate(lc_values):
            name = landcoverNameFromId(i,df_lookup)
            sub_array = np.where(lc_data == i)
            sub_area = (lc_counts[count] * 25) / 10000
            class_array = distinctiveness_data[sub_array[0], sub_array[1]]
            average = np.nanmean(class_array)
            array.append({
                "name": name,
                "area": sub_area,
                "amount": average
            })
        templateDict["distinctivenesstable"] = array


        #### sssi table
        sssi_data = df_alldata.loc['sssi'].data
        sssi_values, sssi_counts = np.unique(sssi_data[~np.isnan(sssi_data)], return_counts=True)
        sssi_array = []
        sssi_total_area = (sum(sssi_counts)) * 25 / 10000
        for count, i in enumerate(sssi_values):
            name = "None"
            if i == 0:
                name = "Not Assessed/Not SSSI"
            if i == 1:
                name = "Unfavourable"
            if i == 2:
                name = "Recovering"
            if i == 3:
                name = "Favourable"
            sssi_array.append({
                "name": name,
                "area": (sssi_counts[count] * 25) / 10000,
                "amount": (((sssi_counts[count] * 25) / 10000) / sssi_total_area) * 100,
                "avg": ((sssi_counts[count] * 25) / 10000)/(((sssi_counts[count] * 25) / 10000) / sssi_total_area) * 100
            })
        templateDict["sssitable"] = sssi_array

        #### protectedspecies table
        distinctiveness_data = df_alldata.loc['vulnspecies'].data
        array = []
        for count, i in enumerate(lc_values):
            name = landcoverNameFromId(i,df_lookup)
            sub_array = np.where(lc_data == i)
            sub_area = (lc_counts[count] * 25) / 10000
            class_array = distinctiveness_data[sub_array[0], sub_array[1]]
            average = np.nanmean(class_array)
            array.append({
                "name": name,
                "area": sub_area,
                "amount": average
            })
        templateDict["vulnspeciestable"] = array


        #### connectivity table
        connectivity_data = df_alldata.loc['connectivity'].data
        array = []
        for count, i in enumerate(lc_values):
            name = landcoverNameFromId(i,df_lookup)
            sub_array = np.where(lc_data == i)
            sub_area = (lc_counts[count] * 25) / 10000
            class_array = connectivity_data[sub_array[0], sub_array[1]]
            average = np.nanmean(class_array) if np.nanmean(class_array) else 0
            array.append({
                "name": name,
                "area": sub_area,
                "avg": average
            })
        templateDict["connectivitytable"] = array

        ### Make PDF
    

    templateDict["total_visitors"] = round((np.nansum(rec_data) * 0.04), -2) 
    templateDict["visitor_text"] = None
    templateDict["peatland_data"] = None
    if template_filename == 'nts':
        visitornumber = df_reportdata["recreation"][0]
        if visitornumber == None or visitornumber == 0:
            templateDict["total_visitors"] = round((np.nansum(rec_data) * 0.04), -2) 
        else:    
            templateDict["total_visitors"] = visitornumber
            templateDict["visitor_text"] = "Data provided by NTS"
    

    
    templateDict["report_title"] = report_title
    templateDict["report_area"] = area
    now = datetime.now() 
    templateDict["report_date"] = now.strftime("%d/%m/%Y")
    #saveTableData(report_id, templateDict)
    templateDict["data_sources"] = data_sources
        
    # save table data to database
    
    path=os.path.join(os.path.dirname(__file__),'./templates')
    templateLoader = jinja2.FileSystemLoader(searchpath=path)
    templateEnv = jinja2.Environment(loader=templateLoader)

    def processNumber(number):
        rounded = round(float(number),1)
        if rounded <= 1 and rounded > 0:
            return '<span class="number"><1</span>'
        else:
            if rounded % 1 == 0.0:
                rounded = int(rounded)
            return f'<span class="number">{rounded:,}</span>'


    templateEnv.filters["processNumber"] = processNumber
    TEMPLATE_FILE = f'{df_reportdata["template_filename"][0]}.jinja'
    template = templateEnv.get_template(TEMPLATE_FILE)
    outputText = template.render(templateDict)  # this is where to put args to the template renderer
    HTML(string=outputText, base_url=path).write_pdf(f"/tmp/report.pdf")  


    ### upload report ###
    s3_name = report_title.replace(' ', '-')
    s3_name = s3_name.replace('/', '-')
    s3_key = f"{email}/{report_id}-{s3_name}.pdf"
    s3.upload_file(f"/tmp/report.pdf", "ncr-baseline-reports", s3_key)
    s3_url = s3.generate_presigned_url('get_object', Params = {'Bucket': 'ncr-baseline-reports', 'Key': s3_key}, ExpiresIn = 604800)
    print(s3_url)
    ses = boto3.client('ses')
    template_data = {"report_url":s3_url}
    response = ses.send_templated_email(
    Source='info@natcapresearch.com',
    Destination={
        'ToAddresses': [
        email
        ],
        'BccAddresses': [
        'jamie.dunbar@natcapresearch.com',
        ]
    },
    ReplyToAddresses=[
        'info@natcapresearch.com',
    ],
    Template='ReportEmail',
    TemplateData=json.dumps(template_data)
    )
    return

# if __name__ == '__main__':
#     lambda_handler('','')
