"""
$Id$

This file id part of the NAV project.

Contains classes for the status preferences page

Copyright (c) 2003 by NTNU, ITEA nettgruppen
Authors: Hans J�rgen Hoel <hansjorg@orakel.ntnu.no>
"""

#################################################
## Imports

import psycopg, cPickle, re

from StatusSections import *

#################################################
## Constants

DEFAULT_PREFS_FILENAME = 'tmp/default-prefs.pickle'

#################################################
## Classes

class HandleStatusPrefs:
    """ 
    This class displays the prefs page and handles 
    loading and saving of preferences 
    """

    STATUS_PROPERTY = 'statusprefs'

    sectionBoxTypes = []
    editSectionBoxes = []

    addBarTitle = None
    addBarSelectOptions = []
    addBarSelectName = None
    addBarSubmitName = None
    addBarSubmitTitle = None
    addBarSaveName = None
    addBarSaveTitle = None

    actionBarUpName = None
    actionBarDelName = None
    radioButtonName = None

    def __init__(self,req):
        self.editSectionBoxes = []

        self.req = req
        form = req.form       
        self.orgList = req.session['user'].getOrgIds()
        # Make a list of the available SectionBox types
        sectionBoxTypeList = []
        sectionBoxTypeList.append(NetboxSectionBox)
        sectionBoxTypeList.append(ServiceSectionBox)
        sectionBoxTypeList.append(ModuleSectionBox)
        # Make a dictionary of typeId,SectionBox
        self.sectionBoxTypes = dict([(section.typeId,section) for \
        section in sectionBoxTypeList])
       
        # Create the add bar select options
        self.addBarSelectOptions = [] 
        for typeId,section in self.sectionBoxTypes.items():
            self.addBarSelectOptions.append((typeId,section.name))

        # Define the addbar and the action bar
        self.addBarTitle = 'Select a section to add'
        self.addBarSelectName = 'prefs_sel'
        self.addBarSubmitTitle = 'Add'
        self.addBarSubmitName = 'prefs_add'
        self.addBarSaveName = 'prefs_save'
        self.addBarSaveTitle = 'Save'
        self.addBarSaveDefName = 'prefs_save_def'
        self.addBarSaveDefTitle = 'Save default'
        self.actionBarUpName = 'prefs_up'
        self.actionBarDelName = 'prefs_del'
        self.radioButtonName = 'prefs_radio'

        # Parse the form and add the sections that are already present
        # If this is the initial loading of the prefs page, nothing
        # will be present, and the prefs will be loaded further down
        for field in form.list:
            if field:
                control = re.match('([a-zA-Z]*)_([0-9]+)$',field.name)
                if control:
                    if len(control.groups()) == 2:
                        controlType = control.group(1)
                        controlNumber = control.group(2)

                        controlBaseName = control.string
                        
                        if self.sectionBoxTypes.has_key(controlType):
                            # read settings from the form, and pass them on
                            # to recreate the section box
                            settings = []
                            # field.value contains the title
                            settings.append(field.value)

                            # go through the form controls and add the
                            # list of filter options to the settings
                            selectDict = dict()
                            for selectfield in form.list:
                                #select = re.match('([a-zA-Z]*)_(' + \
                                #controlNumber + ')_([a-zA-Z]+)',\
                                #selectfield.name)
                                
                                select = re.match(controlType + '_(' + \
                                controlNumber + ')_([a-zA-Z]+)',\
                                selectfield.name)

                                if select:
                                    if len(select.groups()) == 2:
                                        # regexp matches, this is a select
                                        # control
                                        control = select.string
                                        if not selectDict.has_key(control):
                                            selectDict[control] = []
                                        value = selectfield.value
                                        if not value:
                                            # Nothing is selected
                                            # equals "All" selected
                                            value = FILTER_ALL_SELECTED
                                        selectDict[control].append(value)
                            # append filtersettings
                            settings.append(selectDict)
                            self.addSectionBox(controlType,settings,
                                               controlBaseName)
        
        # Handle all possible actions
        if form.has_key(self.addBarSubmitName):
            # Add button pressed
            self.addSectionBox(req.form[self.addBarSelectName])
        elif req.form.has_key(self.addBarSaveName):
            # Save button pressed
            self.savePrefs()
        elif req.form.has_key(self.addBarSaveDefName):
            # Save default pressed
            self.saveDefaultPrefs()
        elif (req.form.has_key(self.actionBarDelName) or \
        req.form.has_key(self.actionBarUpName)):
            # Handle action buttons (move up and delete)
            if form.has_key(self.radioButtonName):
                selected = form[self.radioButtonName]
                if form.has_key(self.actionBarDelName):
                    # delete selected
                    index = 0
                    for editSectionBox in self.editSectionBoxes:
                        if editSectionBox.controlBaseName == selected:
                            break
                        index += 1
                    del(self.editSectionBoxes[index])
                    
                elif form.has_key(self.actionBarUpName):
                    # move up selected
                    index = 0
                    for editSectionBox in self.editSectionBoxes:
                        if editSectionBox.controlBaseName == selected:
                            break
                        index += 1
                    if index > 0:
                        tempBox = self.editSectionBoxes[index]
                        self.editSectionBoxes[index] = \
                        self.editSectionBoxes[index-1]
                        
                        self.editSectionBoxes[index-1] = tempBox
        else:
            # No buttons submitted, initial load of the prefs page.
            # Get saved prefs from the database.
            prefs = self.loadPrefs(req)
            self.setPrefs(prefs)
        return

    def addSectionBox(self,addTypeId,settings=None,controlBaseName=None):
        sectionType = self.sectionBoxTypes[addTypeId]

        controlNumber = self.getNextControlNumber(addTypeId)

        self.editSectionBoxes.append(EditSectionBox(sectionType,\
        controlNumber,settings,controlBaseName,self.orgList)) 
        return

    def getNextControlNumber(self,typeId):
        """
        Get the next free control basename for section of type typeId 
        (for example if service_0_orgid exists, next free controlnumber is 1)
        """
        # make a list of the basenames already in use
        baseNameList = []
        for section in self.editSectionBoxes:
            baseNameList.append(section.controlBaseName)

        # find the next available control number, start at 0
        controlNumber = 0
        newBaseName = typeId + '_' + repr(controlNumber)

        while baseNameList.count(newBaseName):
            controlNumber += 1
            newBaseName = typeId + '_' + repr(controlNumber)

        return controlNumber

    def getPrefs(self):
        " returns a StatusPrefs object with the current preferences "
        prefs = StatusPrefs()

        for section in self.editSectionBoxes:
            if section.title == 'Mail':
                raise('jepp'+repr(section.filterSettings))


            newFilterSettings = {}
            # Change filterSettings to use name instead of control name 
            # ie. org instead of netbox_0_org
            for controlName,selected in section.filterSettings.items():
                name = re.match('.*_([a-zA-Z]*)$',controlName) 
                filterName = name.group(1)
                newFilterSettings[filterName] = selected
            prefs.addSection(section.controlBaseName,section.typeId,
            section.title,newFilterSettings)
        return prefs

    def setPrefs(self, prefs):
        """
        Set current preferences for this instance (from loaded prefs)
        """

        for section in prefs.sections:
            controlBaseName,typeId,title,filterSettings = section

            # Must convert filterSettings used by the main status page to
            # the format used by the prefs page (kludgy)
            # the stored name is just the filtername, the full filtername
            # should be controlBaseName + '_' + filtername
            # (this is the reverse of what is done in getPrefs())

            convertedFilterSettings = {}
            for filterName,selected in filterSettings.items():
                newFilterName = controlBaseName + '_' + filterName
                convertedFilterSettings[newFilterName] = selected 
            
            settings = []
            settings.append(title)  
            settings.append(convertedFilterSettings)

            self.addSectionBox(typeId,settings,controlBaseName)
        return

    def savePrefs(self):
        " Pickles and saves the preferences "
        prefs = self.getPrefs()
                
        connection = psycopg.connect(dsn="host=localhost user=manage \
        dbname=navprofiles password=eganam")
        database = connection.cursor()

        data = psycopg.QuotedString(cPickle.dumps(prefs))

        try:
            self.loadPrefs(self.req)
            # Prefs exists, update
            sql = "UPDATE accountproperty SET value=%s WHERE accountid=%s and \
            property='%s'" % \
            (data,self.req.session['user'].id,self.STATUS_PROPERTY)
        except:
            # No prefs previously saved

            sql = "INSERT INTO accountproperty (accountid,property,value) \
            VALUES (%s,'%s',%s)" % \
            (self.req.session['user'].id,self.STATUS_PROPERTY,data)
        database.execute(sql)
        connection.commit()
        connection.close()

    def loadPrefs(cls,req):
        accountid = req.session['user'].id

        connection = psycopg.connect(dsn="host=localhost user=manage \
        dbname=navprofiles password=eganam")
        database = connection.cursor()

        sql = "SELECT value FROM accountproperty WHERE accountid=%s \
        and property='%s'" % (req.session['user'].id,cls.STATUS_PROPERTY)
        database.execute(sql)

        data = database.fetchone()        
        if data:
            (data,) = data
            prefs = cPickle.loads(data)
        else:
            # No prefs stored in the database for this user,
            # load the default prefs from a file
            fh = file(DEFAULT_PREFS_FILENAME,'r')
            prefs = cPickle.load(fh)
        
        connection.close()
        return prefs
    loadPrefs = classmethod(loadPrefs)

    def saveDefaultPrefs(self):
        " Saves current prefs as default preferences in a file "
        prefs = self.getPrefs()

        fh = file(DEFAULT_PREFS_FILENAME,'w')
        fh.write(cPickle.dumps(prefs))
        fh.close()

class EditSectionBox:
    """
    An editable section box on the prefs page.
    """

    name = None
    title = None
    typeId = None
    controlBaseName = None

    # dict of {'controlname': ['selected','entries',...]}
    filterSettings = dict()

    # list of tuples (controlname,list of (value,option,selected=True|False))
    filterSelects = []
    # list of strings ('org','category', etc.)
    filterHeadings = []

    def __init__(self,sectionType,controlNumber,settings,controlBaseName,orgList):
        self.filterSettings = dict()
        self.typeId = sectionType.typeId
        self.orgList = orgList

        # if this is a new section, use the (unique) controlNumber to make
        # a new controlBaseName
        self.controlBaseName = sectionType.typeId + '_' + repr(controlNumber)
        # if this is an existing section, then preserve the controlBaseName
        if controlBaseName:
            self.controlBaseName = controlBaseName

        self.filterHeadings, self.filterSelects = \
        sectionType.getFilters(self.controlBaseName,self.orgList)
        
        self.name = sectionType.name
        self.title = sectionType.name 

        # if settings is present, then this isn't a new section box, so
        # the settings (from the form or loaded prefs) must be preserved
        if settings:
            self.title = settings[0]
            self.filterSettings = settings[1]

            # set selected = True | False based on filterSettings
            newFilterSelects = []
            for controlName, optionList in self.filterSelects:
                newOptionList = []
                for value,option,selected in optionList:
                    # MUST CHECK IF THE RESULT OF THE FORM CONTROL AS
                    # PARSED BY HandleStatusPrefs.__init__ IS PRESENT
                    # FieldStorage(keep_blank_values) SHOULD PREVENT
                    # THE NEED FOR THIS, BUT SOMETHING IS WRONG
                    if not self.filterSettings.has_key(controlName):
                        # If the control name is missing, nothing is selected,
                        # and the 'All' option should be auto selected
                        self.filterSettings[controlName] = [FILTER_ALL_SELECTED]

                    if self.filterSettings[controlName].count(value):
                        selected = True
                    else:
                        selected = False
                        
                    newOptionList.append((value,option,selected))
                newFilterSelects.append((controlName,newOptionList))
            self.filterSelects = newFilterSelects

class StatusPrefs:
    """ 
    class holding a users/groups preference for the status page 
    """

    sections = []

    def __init__(self):
        self.sections = []

    def addSection(self,controlBaseName,typeId,title,filterSettings):
        self.sections.append((controlBaseName,typeId,title,filterSettings))    
