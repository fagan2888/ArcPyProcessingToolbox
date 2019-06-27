# Import Requried Libraries
import arcpy
from arcpy.sa import *
import os, sys, string
from fnmatch import fnmatch

# Get user defined variables from ArcGIS tool GUI

root = arcpy.GetParameterAsText(0)      # Input Folder
ptshp = arcpy.GetParameterAsText(1)     # Input Point Shapefile
ptvf = arcpy.GetParameterAsText(2)      # Point Value Field
ptinter = arcpy.GetParameter(3)         # Interpolate values at point locations
pgshp = arcpy.GetParameterAsText(4)     # Input Polygon Shapefile
pgvf = arcpy.GetParameterAsText(5)      # Polygon Value Field

# Define local variables for calculating statistics
if ptinter == True:
    ptinterval = "INTERPOLATE"
else:
    ptinterval = "NONE"

# Enforce the value field selection for each shapefile (if defined)

if ptshp:
    if not ptvf:
        arcpy.AddMessage("ERROR: Please select a unique values field from point shapefile")
        arcpy.AddMessage("ERROR: Process will now terminate")
        quit()

if pgshp:
    if not pgvf:
        arcpy.AddMessage("ERROR: Please select a unique values field from Polygon shapefile")
        arcpy.AddMessage("ERROR: Process will now terminate")
        quit()

# Define variables
pattern = "prate_*.tif"                 # Pattern that will be used to find & prepare a list of raster files
lTIFs = []                              # Create a blank list that would be populated by input geotiff files later

# Prepare a list of geotiff files matching the defined pattern from input folder

for path, subdirs, files in os.walk(root):
    for name in files:
        if fnmatch(name, pattern):
            TIF = os.path.join(path, name)
            lTIFs.append(TIF)            
            
# Loop through each raster file and calculate statistics
for tif in lTIFs:
    tifpath, tifname = os.path.split(tif)       # Split filenames and paths

    ###################################################################
    ## Definition of variables related to Point Shapefile Processing ##
    ###################################################################
    
    ptout = tif.replace('.tif', '.shp')         # Full name & Path of temp output point shp
    ptcsv = tifname.replace('.tif', '_pt.csv')  # Define output csv file (add _pt after filename)
    ptcsv = ptcsv.replace('prate_', '')         # Finalize CSV name by stripping "prate_"
    tbloutfield = ptcsv.split('.')[0]           # Get output csv filname without extension
    tbloutfield = tbloutfield.replace('_pt', '')# Strip _pt from name
    tbloutfield = "d"+tbloutfield[1:]           # Replace first char of date(year) by "d" to overrule a restriction
    
    if ptshp:

        # Delete temporary point shapefile if already exists
        if os.path.exists(ptout):
            arcpy.Delete_management(ptout)

        # Compute statistics only if output CSV file doesn't exist
        if not os.path.exists(os.path.join(tifpath, ptcsv)):
            arcpy.AddMessage('Calculating point statistics for ' + tifname)
            arcpy.sa.ExtractValuesToPoints(ptshp, tif, ptout,
                              ptinterval, "VALUE_ONLY")

            # Delete unnecessary fields and rename the statistics field to date
            arcpy.AddMessage("  Dropping and renaming fields")
            fieldList = arcpy.ListFields(ptout)  #get a list of temp point shp fields 
            for field in fieldList: #loop through each field
                if field.name == 'RASTERVALU':  #look for the name RASTERVALU                    
                    arcpy.AddField_management(ptout, tbloutfield, "DOUBLE", "", "", "", "", "NULLABLE")                     
                    arcpy.CalculateField_management(ptout, tbloutfield, "!RASTERVALU!", "PYTHON")
                    arcpy.DeleteField_management(ptout, "RASTERVALU")
                else:
                    if not (field.name == ptvf or field.name == "FID" or field.name == "Shape"):
                        try:
                            arcpy.DeleteField_management(ptout, field.name)
                        except:
                            arcpy.AddMessage("Error Deleting Field " + field.name)

            # Convert shapefile to CSV
            arcpy.AddMessage("  Writing " + ptcsv)
            arcpy.TableToTable_conversion(ptout, tifpath, ptcsv)
            arcpy.Delete_management(ptout)            
        else:
            arcpy.AddMessage('Output already exists. Skipping ' + tifname)
        del ptcsv, tbloutfield
        

    
       
