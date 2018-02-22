import arcpy


class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "Tools For Creating Random Samples"
        self.alias = ""

        # List of tool classes associated with this toolbox
        self.tools = [RND]


class RND(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Make a Random Stratified Sample"
        self.description = ""
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(displayName = 'Feature Class',
        name = 'Feature Class',
        datatype = 'GPFeatureLayer',
        parameterType ="Required",
        direction ="Input")
        
        param1 = arcpy.Parameter(displayName = 'Unique ID Field',
        name = 'Uniquefield',
        datatype = 'Field',
        parameterType ="Required",
        direction ="Input")
        param1.parameterDependencies = [param0.name]

        param2 = arcpy.Parameter(displayName = 'Field For Stratification',
        name = 'Stratfield',
        datatype = 'Field',
        parameterType ="Required",
        direction ="Input")
        param2.parameterDependencies = [param0.name]
        
        param3 = arcpy.Parameter(displayName = 'Sample Size',
        name = 'Samplesize',
        datatype = 'GPLong',
        parameterType ="Required",
        direction ="Input")
        
        param4 = arcpy.Parameter(displayName = 'Optional SQL Query',
        name = 'Feature class for random LFM selections',
        datatype = "GPSQLExpression",
        parameterType ="Optional",
        direction ="Input")

        param4.parameterDependencies = [param0.name]
        
        param5 = arcpy.Parameter(displayName = 'Output Name and Location of Output',
        name = 'Output Feature Class',
        datatype = 'GPFeatureLayer',
        parameterType ="Required",
        direction ="Output")
        
        params =[param0,param1,param2,param3,param4,param5]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        import os 
        from random import sample

        inp = parameters[0].valueAsText
        unique = parameters[1].valueAsText
        strata = parameters[2].valueAsText
        selection = parameters[3].valueAsText
        sql = parameters[4].valueAsText
        outname = parameters[5].valueAsText
        outname = outname.replace('\\','/')
        selection = int(selection)
        
        arcpy.env.overwriteOutput= True
        
        # Read in the data
        arcpy.MakeFeatureLayer_management(inp, "temp") 
        arcpy.MakeTableView_management("temp", "table")

        fields  = [f.name for f in arcpy.ListFields("table")]
        if "RND" in fields:
            arcpy.DeleteField_management("table", "RND")
            arcpy.AddField_management("table", "RND", "LONG")
        else:
            arcpy.AddField_management("table", "RND", "LONG")

        #arcpy.CreateFeatureclass_management(os.path.split(outname)[0], os.path.split(outname)[1],'#',inp,'#','#',inp)    
        arcpy.AddMessage('Reading the Data')
               
        valueDi ={}
        if sql is None:
            arcpy.AddMessage('message is none')
            cursor = arcpy.da.SearchCursor(inp,[unique,strata])
        else:
            arcpy.AddMessage('there is sql')
            cursor = arcpy.da.SearchCursor(inp,[unique,strata], where_clause = sql)
        for row in cursor:
            if row[1] not in valueDi:
                valueDi[row[1]]=[]
                valueDi[row[1]].append(row[0])
            else:
                valueDi[row[1]].append(row[0])
        
        values = list(valueDi.keys())
        actual_values = []
        selection_dict = {} 
        for v in values:
            if len(valueDi[v]) < selection:
                pass
            else:
                actual_values.append(v)
                a= sample(xrange(len(valueDi[v])),selection)
                b=valueDi[v]
                if type(b[0])==int:
                	temp = [b[i] for i in a]
                else:
                	temp = [str(b[i]) for i in a]
                selection_dict[v]=temp

        for v in actual_values:
            aa =tuple(selection_dict[v])
            aa = str(aa)
            arcpy.SelectLayerByAttribute_management("temp", "NEW_SELECTION", unique  + " IN " + aa )
            arcpy.CalculateField_management ("temp", "RND", 1,"PYTHON")
            arcpy.SelectLayerByAttribute_management("temp", "CLEAR_SELECTION")
               
        
    	arcpy.SelectLayerByAttribute_management("temp", "NEW_SELECTION",'"RND" = 1')
    	arcpy.CopyFeatures_management("temp",outname)

        mxd = arcpy.mapping.MapDocument("CURRENT")
        df = arcpy.mapping.ListDataFrames(mxd)[0]
        addLayer = arcpy.mapping.Layer(outname)
        arcpy.mapping.AddLayer(df, addLayer, "BOTTOM")