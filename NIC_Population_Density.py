# -*- coding: utf-8 -*-

# A choropleth map of the population density in Nicaragua broken down by 
# departments (provinces). 
# The map is done using python's basemap library. Shapefiles for the administrative
# units of Nicaragua are taken down from the GADM website (http://www.gadm.org/). 
# The code to # manipulate the shapefiles is largely taken from this blog.  
#http://www.geophysique.be/2013/02/12/matplotlib-basemap-tutorial-10-shapefiles-unleached-continued/

import numpy as np
import pandas as pd

import matplotlib as mpl
import matplotlib.cm as cm
from matplotlib.colors import Normalize
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
from matplotlib.collections import LineCollection
from matplotlib import cm
from pysal.esda.mapclassify import Fisher_Jenks as fj
import shapefile

# === DATA =====================================================================
# http://www.pronicaragua.org/es/descubre-nicaragua/poblacion
# http://www.inide.gob.ni/compendio/pdf/inec112.pdf
# The first column contains the name of the Department (Province). We'll keep 
# the name in the original form, with the spanish accent marks. Note the first 
# line in the file (# -*- coding: utf-8 -*-) that makes possible to read a
# non-ASCII character. 
# The reason for keeping the original version is that the names in the shapefile
# we will be using are written the same way. Thus, it will be easy to select 
# and manage the data. 
# Second and third column contains number of people and surface area in km^2 for 
# the respective province. 

NIC_DATA=[ ['Managua',        1480270,   3465.10  ], 
           ['Matagalpa',      547500,    6803.86  ],
           ['Atlántico Norte',476298,    32819.68 ],
           ['Jinotega',       438412,    9222.40  ],
           ['Chinandega',     419753,    4822.42  ],
           ['León',           399879,    5138.03  ],
           ['Atlántico Sur',  380121,    27546.32 ],
           ['Masaya',         361914,    610.78   ],
           ['Nueva Segovia',  249376,    3491.28  ],
           ['Estelí',         223356,    2229.69  ],
           ['Granada',        201993,    1039.68  ],
           ['Chontales',      191127,    6481.27  ],
           ['Carazo',         186438,    1081.40  ],
           ['Rivas',          172289,    2161.82  ],
           ['Boaco',          160711,    4176.68  ],
           ['Madriz',         158705,    1708.23  ],
           ['Río San Juan',   119095,    7540.90  ] ]

#Convert the data to Pandas Data Frame           
DF = pd.DataFrame(NIC_DATA,columns = ['Department', 'Population', 'Area'])

# Add the values of the population density per department
DF['Density'] = DF['Population']/DF['Area']
nd = len(DF) # number of departments in Nicaragua
PopDensity = DF['Density'].values.copy()

# We will also need the SHAPEFILES for each province. These can be freely 
# obtained from the GADM database selecting Nicaragua as the country
# http://www.gadm.org/
r = shapefile.Reader(r"NIC_adm1")
shapes = r.shapes()
records = r.records()

# === POPULATION DENSITY =======================================================
# There are only 17 departments (provinces). We can chose to represent pop. 
# density of each province with different color. It's going to look nice, but 
# colorbar might look a bit overcrowded. The second option it to group close 
# values of the population density into one group and thus reduce the number 
# of colors on the colormap. I'll go forward with the second option.
# There are only 17 values and we can group them manually. Otherwise, the map 
# classification  method (for future maps) can be found in pysal library 
# (class pysal.esda.mapclassify.Map_Classifier)

# We'll create the following list of bin limits [(1,20),(20,50),(50,90) ...]
BinsLim = [1,20,50,90,150,200,400,600] 
nbins = len(BinsLim)

Bins = [(i1,i2) for i1,i2 in zip(BinsLim[0:nbins],BinsLim[1:nbins+1])]

# Associate value of the pop. density with the corresponding bin
grouped = np.digitize(PopDensity,BinsLim[1::]) 

# Add to the data frame we defined above
DF['BinsIndx'] = grouped
DF['BinGroup'] = [Bins[i] for i in grouped]

# Define bin labels to be put on the colorbar
BinLabels = ["(%s - %s)/km$^2$" % (i1[0],i1[1]) for i1 in Bins]

# === MAP ======================================================================

fig, ax = plt.subplots()
ax.axis("off") 
# Choose the colormap
cmap = plt.cm.YlOrRd #Blues #plt.cm.YlOrBr
# We only need 7 values from this colormap
cmaplist = [cmap(i) for i in range(cmap.N)]
NumColors = np.int(np.ceil(cmap.N/float(nbins-1)))
MapColors = cmaplist[0::NumColors] # WHAT IF 9 BINS
len_MapColors = len(MapColors)

# ---Define the BASEMAP ------------------------

u2 = 10.50 
u1 = -88.00 
p2 = 15.33 
p1 = -81.89

n_map = Basemap(projection='merc', lat_0=-85., lon_0=13.,
    resolution = 'l', area_thresh = 1500.0,
    llcrnrlon = u1, llcrnrlat = u2,
    urcrnrlon = p1, urcrnrlat = p2)
n_map.drawmapboundary()
n_map.drawmapscale(-87.423,10.93,-87.297,10.93,100,barstyle='fancy',
                   fontcolor = '0.3', fillcolor2 = '0.3')

# --- Extract lat. and long. data from the GADM shapefile
#     and assign a facecolor to each department  
for record, shape in zip(records,shapes):
    lons,lats = zip(*shape.points)
    data = np.array(n_map(lons, lats)).T
    name = DF.loc[DF['Department'] == record[4]]
    if name.empty:
        ncolor = 0
    else:
        ncolor = name['BinsIndx'].values.copy()
        if len(shape.parts) == 1:
            segs = [data,]
        else:
            segs = []
            for i in range(1,len(shape.parts)):
                index = shape.parts[i-1]
                index2 = shape.parts[i]
                segs.append(data[index:index2])
            segs.append(data[index2:])
 
        lines = LineCollection(segs,antialiaseds=(1,))
        
        color = MapColors[ncolor[0]] 
        lines.set_facecolors(color)
        lines.set_edgecolors('k')
        lines.set_linewidth(0.1)
        ax.add_collection(lines)

# === COLORBAR =================================================================

#Define a color map from the 7 colors we used in the plot
CustomCMap = cmap.from_list('Custom cmap', MapColors, N = len_MapColors)
#Add the axis for the colorbar
ax_cb = fig.add_axes([0.87, 0.1, 0.03, 0.8])

cb = mpl.colorbar.ColorbarBase(ax_cb, cmap=CustomCMap,spacing = 'proportional')
#Position the tick labels in the middle of the respective colorbar part
delta = 1./(2*len_MapColors)
TickSpacing = 1./len_MapColors
xticks = [TickSpacing*x-delta for x in range(1,len_MapColors+1)]
cb.set_ticks(xticks)
cb.ax.tick_params(color='0.3',labelcolor='0.3')
cb.set_ticklabels(BinLabels,update_ticks=True)

cb.outline.set_edgecolor('0.3')

# ---Add a name ------------------------
ax.text(0.03,.95 , 'Nicaragua \nPopulation Density', transform=ax.transAxes,
  fontsize=12, fontweight='bold', color='0.3',va='top')
  
# === SAVE THE PLOT ============================================================
plt.savefig('NIC_Population_Density.png',bbox_inches='tight',dpi=150)

