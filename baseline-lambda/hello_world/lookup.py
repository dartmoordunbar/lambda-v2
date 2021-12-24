from enum import Enum

datatypes = []
landcover = {
    1: {
        "name": "Neutral grassland",
        "category": "Neutral_Grassland",
        "colour": "#bfde4f",
        "values": [1000000,1000283,1000516,1000524,1000525,1000526,1300000,1300016,1300017,1300522,1300527,1310000,1315000,1320000,1325000,1330523,1336523,6150166,7119000,7130000,7135000]
    },
    2: {
        "name": "Arable and horticulture",
        "category": "Arable_And_Horticulture",
        "colour": "#ffee88",
        "values": [2000512, 2100021,5000000,5000017,5000277,5000470,5000471,5100475,5100476,5100508,5100509,5100513,5100514,5100515,5110000,5130000,5130400,
5130401,5130402,5130403,5130404,5130405,5130406,5130407,5130408,5130409,5130410,5130411,5130412,5130413,5130414,5130415,5130416,5130417,5130418,5130419,5130420,5130421,5130422,5130423,5130424,5130425,5130426,5130427,5130428,5130429,5130430,5130431,5130432,5130433,5130434,5130435,5130436,5130437,5130438,5130439,5130440,5130441,5130442,5130443,5130444,5130445,5130446,5130447,5130448,5130449,5130450,5130451,5130452,5130453,5130454,5137510,5147000,5148455,5148456,5148457,5148458,5148459,5148460,5148461,5148462,5148463,5148464,5148465,5148466,5148467,5148468,5148469,5150000,5150511,7000474]
    },
    3: {
        "name": "Acid grassland",
        "category": "Acid_Grassland",
        "colour": "#88bbaa",
        "values": [1100000, 1100522, 1100523, 1100528, 1100529, 1110000, 1120000, 1125000, 1130000, 1130012]
    },
    4: {
        "Category": "Hedgerows",
        "name": "Hedgerows and trees outside of woodlands",
        "colour": "#5a00eb",
        "values": [2176000,2176303,3200000,3200075,3200077,3200302,3210075,3210306]
    },
    5: {
        "name": "Broadleaved mixed and yew woodland",
        "colour": "#55aa22",
        "woodland": True,
        "category": "Broadleaved_Mixed_And_Yew_Woodland",
        "values": [2000000,2180000,2000020,2000285,2000400,2000551,2000751,2000951,2100000,2100020,2100036,2100037,2100051,2100052,2100053,2100200,2100251,2100252,2100400,2100451,2100452,2110000,2110400,2120000,2120400,2130000,2140000,2140400,2145000,2146000,2146400,2150000,2150400,2160000,2160400,2180020,2180036,2180037,2180053,2180400,2185217,2185417,2185617,2186217,2186417,2186617,2300400,2300551,2300751,2300951,2400000,2400051,2400052,2400200,2400251,2400252,2400400,2400451,2400452,2410200,2410400,2420200,2420400,2440200,2440400,2450200,2450400,2460200,2460400,2480200,2480400,2485217,2485417,2485617,2486217,2486417,2486617,2600551,2600751,2600951,2700000,2700051,2700052,2700200,2700251,2700252,2700400,2700451,2700452,2710200,2710400,2720200,2720400,2740200,2740400,2750200,2750400,2760200,2760400,2780200,2780400,2785217,2785417,2785617,2786217,2786417,2786617]},
    6: {
        "name": "Coniferous woodland",
        "category": "Coniferous_Woodland",
        "colour": "#117733",
        "woodland": True,
        "values": [2000053,2000054,2000056,2000253,2000254,2000256,2000453,2000454,2000456,2200000,2200020,2200036,2200037,2200053,2200200,2200400,2200436,2210000,2210400,2300053,2300054,2300056,2300200,2300253,2300254,2300256,2300453,2300454,2300456,2500000,2500200,2500400,2500436,2510200,2510400,2600053,2600054,2600056,2600200,2600253,2600254,2600256,2600400,2600453,2600454,2600456,2800000,2800200,2800400,2810200,2810400]
    },
    7: {
        "name": "Builtup areas and gardens",
        "category": "Built_Up_Areas_And_Gardens",
        "colour": "#bb0011",
        "values": [6120000,6000000,6000044,6000087,6000088,6000111,6000113,6000502,6000506,6000507,6100000,6100200,6110000,6125000,6125501,6126505,6150000,6150071,6150072,6150549,6150550,7000044]
    },
    8: {
        "name": "Sparcely vegetated land",
        "category": "Sparsely_Vegetated_Land",
        "colour": "#cdcdcd",
        "values": [7000000,7000063,7000073,7000102,7000105,7000115,7000116,7000124,7000500,7000504,7000548]
    },
    9: {
        "name": "Dense scrub",
        "category": "Dense_scrub",
        "colour": "#44aa66",
        "values": [3000010,3000477,3000517,3000518,3136000,3300000,3300010,3300521,3310000,3360000,3380000]
    },
    10: {
        "name": "Dwarf shrub heath",
        "category": "Dwarf_Shrub_Heath",
        "colour": "#a08ec3",
        "values": [3000000,3100000,3100013,3100120,3100134,3100135,3110000,3110027,3116000,3117000,3120000,3125000,3126000,3130000,3135000]
    },
    11: {
        "name": "Modified grassland",
        "category": "Modified_Grassland",
        "colour": "#dfc13b",
        "values": [1000241,1000473,1400000,1400523]
    },
    12: {
        "category": "Fen_Marsh_And_Swamp",
        "name": "Fen marsh and swamp",
        "colour": "#3ec2b7",
        "values": [4000000,4000172,4000176,4000179,4000180,4000185,4000186,4000520,4000533,4000534,4000535,4000536,4000537,4000538,4200000,4210000,4217000,4220000,4225000,4230000,4235000,4236000,4236142,4237000,4238000,4240000,4240122,4250000,4260000,8000025]
    },
    13: {
        "name": "Rivers and lakes",
        "category": "Rivers_And_Streams",
        "colour": "#00ebeb",
        "values": [8000000,8100000,8100108,8100138,8110000,8110539,8115000,8120000,8120540,8125000,8130000,8130541,8130542,8135000,8136000,8140000,8200000,8200131,8200539,8200540,8200541,8200542,8210000,8215000]
    },
    14: {
        "name": "Bog",
        "category": "Bog",
        "values": [4100000,4100531,4100532,4110000,4115000,4120000,4120530,4125000,4126000,7000127],
        "colour": "#dd7ac0"
    },
    15: {
        "category": "Calcareous_Grassland",
        "name": "Calcareous grassland",
        "colour": "#99bb55",
        "values": [1000026,1130472,1200000,1200522,1200523,1210000,1220000,1225000,1226000,1227000]
    },
    16: {
        "category": "Inland_rock",
        "name": "Inland rock",
        "colour": "#959595",
        "values": [7100000,7100134,7100135,7100156,7110000,7110176,7115000,7116000,7117000,7118000,7120000,7125000,7140000]
    },
    17: {
        "category": "Littoral_Rock",
        "name": "Coastal rock",
        "values":  [9100000,9100543,9100544,9110000,9120000,9130000,9140000],
        "colour": "#669cb1"
    },
    18: {
        "category": "Littoral_Sediment",
        "name": "Coastal saltmarsh, lagoons and beaches",
        "colour": "#aaddcc",
        "values": [9000000,9000030,9000031,9000032,9000104,9000543,9000544,9000546,9200000,9200543,9200544,9200545,9210000,9215000,9216000,9217000,9218000,9220000,9230000,9240000,9250000,9260000,9270000,9275000]
    },
    19: {
        "category": "Open_Saline_Water",
        "name": "Open saline water",
        "colour": "#3a579c",
        "values": [9000230]
    },
    20: {
        "category": "Supralittoral_Rock",
        "name": "Maritime cliffs",
        "colour": "#bcceae",
        "values": [7200000,7210000,7210547,7215000,7216000]
    },
    21: {
        "category": "Supralittoral_Sediment",
        "name": "Coastal sand dunes and shingle",
        "colour": "#ffceae",
        "values": [7300519,7310000,7310010,7313000,7314000,7315000,7316000,7317000,7318000,7319000,7320000,7325000,7326000]
    },
    30: {
        "category": "Standing open water and canals",
        "name": "Standing open water and canals",
        "colour": "#89CFF0",
        "values": [8000040,8100000,8100108,8110000,8116000]
    },
    -9999: {
        "category": "None",
        "name": "",
        "colour": "#00000000",
        "values": [-9999]
    }
}


soiltypes = {
    8: {
        "name": "Silt Loam",
        "colour": "#a7bd75",
        "values": [8]
    },
    9: {
        "name": "Loam",
        "colour": "#A08EC3",
        "values": [9]
    },
    1: {
        "name": "Clay",
        "colour": "#80acdd",
        "values": [1]
    },
    2: {
        "name": "Silty Clay",
        "colour": "#6bc4a6",
        "values": [2]
    },
    3: {
        "name": "Silty Clay Loam",
        "colour": "#8baa67",
        "values": [3]
    },
    4: {
        "name": "Sandy Clay",
        "colour": "#9faeb3",
        "values": [4]
    },
    5: {
        "name": "Sandy Clay Loam",
        "colour": "#dfe396",
        "values": [5]
    },
    6: {
        "name": "Clay Loam",
        "colour": "#c2d2ec",
        "values": [6]
    },
    7: {
        "name": "Silt",
        "colour": "#A08EC3",
        "values": [7]
    },
    10: {
        "name": "Sand",
        "colour": "#cd9a96",
        "values": [10]
    },
    11: {
        "name": "Loamy Sand",
        "colour": "#dba780",
        "values": [11]
    },
    12: {
        "name": "Sandy Loam",
        "colour": "#f3d189",
        "values": [12]
    },
    13: {
        "name": "Organic",
        "colour": "#A08EC3",
        "values": [13]
    },
    -9999: {
        "category": "None",
        "name": "",
        "colour": "#00000000",
        "values": [-9999]
    }
}

naturenetworks = {
    1: {"name": "Low Importance", "colour": "#FDE725FF"},
    2: {"name": "Medium Importance", "colour": "#55C667FF"},
    3: {"name": "High Importance", "colour": "#238A8DFF"},
    4: {"name": "Hedgerows", "colour": "#440154FF"},
    -9999: {
        "category": "None",
        "name": "",
        "colour": "#00000000",
        "values": [-9999]
    }
}


biodiversity = {
    1: {"name": "International Importance - Statutory Protected", "colour": "#7CA1C5"},
    2: {"name": "National Importance - Statutory Protected", "colour": "#a6edb5"},
    3: {"name": "Local Importance - Statutory Protected", "colour": "#c588eb"},
    4: {"name": "National Importance - Non-Statutory Protected", "colour": "#FAEE90"},
    -9999: {
        "category": "None",
        "name": "",
        "colour": "#00000000",
        "values": [-9999]
    }
}


files = [
    {
        "label": "cleanwater",
        "path": "es_flows/clean_water/",
        "name": "nitrate.tif"
    },
    {
        "label": "carbonstoragetopsoil",
        "path": "es_flows/carbon_storage_topsoils/",
        "name": "gsoc.tif"
    },
    {
        "label": "landcover",
        "path": "stocks/landcover/",
        "name": "LCmap.tif"
    },
    {
        "label": "elevation",
        "path": "stocks/elevation/",
        "name": "DEM.tif"
    },
    {
        "label": "slope",
        "path": "stocks/slope/",
        "name": "slope.tif"
    },
    {
        "label": "canopyheight",
        "path": "stocks/canopy_height/",
        "name": "Canopy_height.tif"
    },
    {
        "label": "soiltypes",
        "path": "stocks/soil_types/",
        "name": "soiltype.tif"
    },
    {
        "label": "recreation",
        "path": "es_flows/important_areas_recreation/",
        "name": "Recreation.tif"
    },
    {
        "label": "pollination",
        "path": "es_flows/important_habitat_insect_pollinators/",
        "name": "PollinationService.tif"
    },
    {
        "label": "biodiversity",
        "path": "es_flows/important_habitat_for_biodiversity/",
        "name": "bio.tif"
    },
    {
        "label": "naturenetworks",
        "path": "es_flows/important_vegetation_movement_biodiversity/",
        "name": "movement_bio.tif"
    },
    {
        "label": "carbonstoragewoodlands",
        "path": "es_flows/carbon_storage_woodlands/",
        "name": "C_stock_forest.tif"
    },
    {
        "label": "carbonstoragenonwoodlands",
        "path": "es_flows/carbon_storage_nonwoodlands/",
        "name": "C_stock_nonforest.tif"
    },
    {
        "label": "carbonseqwoodlands",
        "path": "es_flows/carbon_sequestration_woodlands/",
        "name": "C_seq_forest.tif"
    },
    {
        "label": "carbonseqnonwoodlands",
        "path": "es_flows/carbon_sequestration_nonwoodlands/",
        "name": "C_seq_nonforest.tif"
    },
    {
        "label": "soilerosion",
        "path": "es_flows/veg_contribution_soil_stabilisation/",
        "name": "E_scen-curr.tif"

    },
    {
        "label": "floodprevention",
        "path": "es_flows/veg_contribution_flood_risk/",
        "name": "water.tif"
    }
]


##### Try something New with ENUMS ####
