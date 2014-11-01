#! /usr/bin/env python3

#----------------------------------------------------------------------------
# Name:     Monitor.py
# Purpose:  Monitor and control a set of NCPA sensors.
#
# Author:   J Park
#
# Created:  
#----------------------------------------------------------------------------

#------------------------------------------------------------------
# todo:
# Opening a new file dialog clears the listbox sensor highlighting
#------------------------------------------------------------------

#------------------------------------------------------------------
# Installation:
# sudo apt-get install python3.2
# sudo apt-get install python3-tk
# Edit Sensors.txt to specify sensors & .cfg files
# ./Monitor.py
#------------------------------------------------------------------

import os
import argparse
import subprocess
import tempfile

from tkinter import *
# Override tkinter (Tk) widgets with the tk-themed ones (Ttk) in ttk
from tkinter import ttk # 'tk themed widgets'
from tkinter import messagebox
from tkinter import filedialog

import NCPASensor_py3 as NCPASensor # NCPASensor & SensorCollection
import MonitorCommands

DEBUG = False # Set True by the -v (verbose) option

#---------------------------------------------------------------
# Python equivalent of a C++ enumeration using a class
class MonitorStatus:
    OK, WARN, ERROR = range( 3 )

#---------------------------------------------------------------
# Class to monitor the overall sensor collection status
#---------------------------------------------------------------
class Status:
    def __init__( self, monitor ):
        OKFile   = monitor.args.monitorPath + '/statusOK.gif'
        WarnFile = monitor.args.monitorPath + '/statusWarn.gif'
        ErrFile  = monitor.args.monitorPath + '/statusError.gif'

        # If we can't open these files, tell the user to set -m
        if not os.access( OKFile,   os.R_OK ) or \
           not os.access( WarnFile, os.R_OK ) or \
           not os.access( ErrFile,  os.R_OK ) :
           errMsg = 'Failed to find Monitor graphic files ' + \
                    'in the path:\n' + monitor.args.monitorPath + \
                    '\nUse the -m option to specify the path.'
           raise( Exception( errMsg ) )

        self.Tk_root      = monitor.Tk_root
        self.state        = MonitorStatus.OK
        self.Label        = None # assigned in main()
        self.OKGraphic    = PhotoImage( file = OKFile   )
        self.WarnGraphic  = PhotoImage( file = WarnFile )
        self.ErrorGraphic = PhotoImage( file = ErrFile  )
        self.pingStatus   = MonitorStatus.OK
        self.timeStatus   = MonitorStatus.OK
        self.dataStatus   = MonitorStatus.OK
        self.logStatus    = MonitorStatus.OK
        self.umxStatus    = MonitorStatus.OK

    #----------------------------------------------------------------
    def Update( self ) :
        # Check all the monitor update states
        # JP Containerize these ?
        if self.pingStatus == MonitorStatus.OK and \
           self.timeStatus == MonitorStatus.OK and \
           self.dataStatus == MonitorStatus.OK and \
           self.logStatus  == MonitorStatus.OK and \
           self.umxStatus  == MonitorStatus.OK :

            self.state = MonitorStatus.OK

        elif self.pingStatus == MonitorStatus.ERROR or \
             self.timeStatus == MonitorStatus.ERROR or \
             self.dataStatus == MonitorStatus.ERROR or \
             self.logStatus  == MonitorStatus.ERROR or \
             self.umxStatus  == MonitorStatus.ERROR :

            self.state = MonitorStatus.ERROR

        else:
            self.state = MonitorStatus.WARN

        # Set the overall status based on the monitor states
        if self.state == MonitorStatus.OK :
            self.Label.config( image = self.OKGraphic )
        elif self.state == MonitorStatus.WARN :
            self.Label.config( image = self.WarnGraphic )
        elif self.state == MonitorStatus.ERROR :
            self.Label.config( image = self.ErrorGraphic )
        else:
            raise( Exception( 'UpdateStatus() Invalid state: ', 
                              self.MonitorStatus ) )

        self.Label.update_idletasks()

        # Re-register this function for another callback
        self.Tk_root.after( 1000, self.Update )

#---------------------------------------------------------------
# The application container (GUI & executive functions)
#---------------------------------------------------------------
class NCPA_Monitor:

    # Note that a tkinter Tk() StringVar() can not be created
    # until after the root widget is created: root = Tk()
    # StringVar() has get() and set() methods for Label updates. 
    def __init__( self, root, args ):
        self.Version          = 'NCPA Sensor Monitor\nVer. 0.1\n'
        self.Tk_root          = root
        self.args             = args
        self.sensorFile       = args.sensorFile    # reassigned in OpenFile()
        self.configFilePath   = '~/'               # reassigned in OpenFile()
        self.msgLogFile       = StringVar( value = 'Log Info'  )
        self.msgDataFile      = StringVar( value = 'Data Info' )
        self.msgPing          = StringVar( value = 'Ping Info' )
        self.msgTime          = StringVar( value = 'Time Info' )
        self.msgUMX           = StringVar( value = 'UMX Info'  )
        self.msgCommand       = StringVar( value = 'Commands'  )
        self.timeMessages     = ''
        self.pingMessages     = ''
        self.dataMessages     = ''
        self.logMessages      = ''
        self.umxMessages      = ''
        self.rebootMessages   = ''
        self.haltMessages     = ''
        self.sendConfigMessages = ''
        self.startUMXMessages = ''
        self.killUMXMessages  = ''
        self.plotMessages     = ''
        self.pollOnOff        = BooleanVar( value = False )
        self.pollSelectWindow = None
        self.pingPoll         = BooleanVar( value = True )
        self.timePoll         = BooleanVar( value = True )
        self.dataPoll         = BooleanVar( value = True )
        self.logPoll          = BooleanVar( value = True )
        self.umxPoll          = BooleanVar( value = True )
        self.pingAfterID      = None  # assigned in PollChanged()
        self.timeAfterID      = None
        self.dataFileAfterID  = None
        self.logFileAfterID   = None
        self.umxAfterID       = None
        self.listBox          = None  # assigned in main()
        self.SensorCollection = None  # assigned in main() or OpenFile() 
        self.selectedSensors  = None  # assigned in ProcessListbox()
        self.Status           = None  # assigned in main()

        # Create a temporary directory for plot files
        self.TemporaryDirectory = tempfile.TemporaryDirectory()
        self.tempDir            = self.TemporaryDirectory.name + '/'
        if DEBUG:
            print( 'Created temporary directory: ' + self.tempDir )

    #----------------------------------------------------------------
    # Called when the root window Poll On/Off checkbox is clicked
    def PollChanged( self ) :
        if DEBUG:
            print( 'PollChanged value: ', self.pollOnOff.get() )
            print( 'timePoll', self.timePoll.get(),
                   'timeRefresh', self.args.timeRefresh )
            print( 'pingPoll', self.pingPoll.get(), 
                   'pingRefresh ', self.args.pingRefresh )
            print( 'dataPoll', self.dataPoll.get(),
                   'dataRefresh', self.args.dataRefresh )
            print( 'logPoll',  self.logPoll.get(),
                   'logRefresh', self.args.dataRefresh )
            print( 'umxPoll', self.umxPoll.get(),
                   'umxRefresh', self.args.umxRefresh )

        if self.pollOnOff.get() :
            # Activate the callbacks if the poll interval is positive
            # Note that each of these functions automatically
            # re-registers itself to run again. 
            if self.timePoll.get() and self.args.timeRefresh > 0. :
                self.timeAfterID = self.Tk_root.after( self.args.timeRefresh, 
                                                       self.TimeMonitor )
            if self.pingPoll.get() and self.args.pingRefresh > 0. :
                self.pingAfterID = self.Tk_root.after( self.args.pingRefresh, 
                                                       self.PingMonitor )
            if self.dataPoll.get() and self.args.dataRefresh > 0. :
                self.dataFileAfterID = self.Tk_root.after(self.args.dataRefresh,
                                                          self.DataFileMonitor)
            if self.logPoll.get() and self.args.logRefresh > 0. :
                self.logFileAfterID = self.Tk_root.after( self.args.logRefresh,
                                                          self.LogFileMonitor )
            if self.umxPoll.get() and self.args.umxRefresh > 0. :
                self.umxAfterID = self.Tk_root.after( self.args.umxRefresh, 
                                                      self.UMXMonitor )

            self.msgCommand.set( MonitorCommands.GetLocalUTC() + \
                                 ' Sensor Polling Activated.' )

        else:
            # deactivate the callbacks
            id = self.timeAfterID
            self.timeAfterID = None
            if id:
                self.Tk_root.after_cancel( id )

            id = self.pingAfterID
            self.pingAfterID = None
            if id:
                self.Tk_root.after_cancel( id )

            id = self.dataFileAfterID
            self.dataFileAfterID = None
            if id:
                self.Tk_root.after_cancel( id )

            id = self.logFileAfterID
            self.logFileAfterID = None
            if id:
                self.Tk_root.after_cancel( id )

            id = self.umxAfterID
            self.umxAfterID = None
            if id:
                self.Tk_root.after_cancel( id )

            self.msgCommand.set( MonitorCommands.GetLocalUTC() + \
                                 ' Sensor Polling Deactivated.' )

    #----------------------------------------------------------------
    # Called when the Config - Polling menu is selected
    # Allows the user to selectively turn on/off polling
    def ChangePolling( self ):
        if self.pollOnOff.get() :
            # Turn off polling
            self.pollOnOff.set( False )
            self.PollChanged()
            msg = "Polling disabled.\n" + \
                  "Reactivate AFTER poll\nselections are made."
            messagebox.showinfo( message = msg )

        self.pollSelectWindow = Toplevel( self.Tk_root )
        self.pollSelectWindow.title( 'NCPA: Set Polling' )
        self.pollSelectWindow.config( padx = 25, pady = 20 )
        
        # One checkbox for each polling function
        ping = ttk.Checkbutton( self.pollSelectWindow, 
                                text = 'Ping On/Off', variable = self.pingPoll,
                                onvalue = True, offvalue = False )

        time = ttk.Checkbutton( self.pollSelectWindow, 
                                text = 'Time On/Off', variable = self.timePoll,
                                onvalue = True, offvalue = False )

        log = ttk.Checkbutton(  self.pollSelectWindow, 
                                text = 'Log On/Off', variable = self.logPoll,
                                onvalue = True, offvalue = False )

        data = ttk.Checkbutton( self.pollSelectWindow, 
                                text = 'Data On/Off', variable = self.dataPoll,
                                onvalue = True, offvalue = False )

        umx = ttk.Checkbutton(  self.pollSelectWindow, 
                                text = 'UMX On/Off', variable = self.umxPoll,
                                onvalue = True, offvalue = False )

        ping.grid( column = 0, row = 0, sticky = (W,E) )
        time.grid( column = 0, row = 1, sticky = (W,E) )
        umx.grid ( column = 0, row = 2, sticky = (W,E) )
        data.grid( column = 0, row = 3, sticky = (W,E) )
        log.grid ( column = 0, row = 4, sticky = (W,E) )


    #----------------------------------------------------------------
    # The following are just wrappers for the actual commands to
    # communicate with and control the sensors. The commands are 
    # in the MonitorCommands.py module.
    #----------------------------------------------------------------
    def PlotData( self ) :
        if DEBUG:
            print( 'PlotData' )
            print( self.selectedSensors )

        if self.selectedSensors :
            # Clear the plot msgs
            self.plotMessages = ''

            # Schedule PlotCmd for each sensor and store the Popen object
            for key in self.selectedSensors :
                sensor = self.SensorCollection.SensorDict[ key ]

                if not sensor.plotPopenBusy :
                    sensor.plotStatusMsg = ''
                    MonitorCommands.PlotCmd( sensor )

    #----------------------------------------------------------------
    def StartUMX( self ) :
        if DEBUG:
            print( 'StartUMX' )
            print( self.selectedSensors )

        if self.selectedSensors :
            validateStartUMX = messagebox.askyesno( 
                message = 'Start UMX on ' + \
                          ', '.join( self.selectedSensors ) + '?',
                icon = 'question', title = 'Start UMX' )
            
            if not validateStartUMX :
                return

            # Clear the startUMX msgs
            self.startUMXMessages = ''

            # Schedule StartUMXSchedulerCmd for each sensor and store Popen
            for key in self.selectedSensors :
                sensor = self.SensorCollection.SensorDict[ key ]

                if not sensor.startUMXSchedulerPopenBusy :
                    if DEBUG:
                        print( 'StartUMX() scheduling StartUMXSchedulerCmd()' )

                    sensor.startUMXStatusMsg = ''
                    sensor.startUMXSchedulerPopenBusy = True
                    sensor.startUMXSchedulerPopen = \
                        MonitorCommands.StartUMXSchedulerCmd( sensor )

                    # Register a callback to poll and report the resultant
                    # message from StartUMXCmd into monitor.msgCommand.set()
                    self.Tk_root.after_idle( sensor.PollStartUMXSchedulerCmd )

    #----------------------------------------------------------------
    def KillUMX( self ) :
        if DEBUG:
            print( 'KillUMX' )
            print( self.selectedSensors )

        if self.selectedSensors :
            validateKillUMX = messagebox.askyesno( 
                message = 'Kill UMX on ' + \
                          ', '.join( self.selectedSensors ) + '?',
                icon = 'question', title = 'Kill UMX' )
            
            if not validateKillUMX :
                return

            # Clear the killUMX msgs
            self.killUMXMessages = ''

            # Schedule KillUMXCmd for each sensor and store the Popen object
            for key in self.selectedSensors :
                sensor = self.SensorCollection.SensorDict[ key ]

                if not sensor.killUMXPopenBusy :
                    sensor.killUMXStatusMsg = ''
                    sensor.killUMXPopenBusy = True
                    sensor.killUMXPopen = MonitorCommands.KillUMXCmd( sensor )

                    # Register a callback to poll and report the resultant
                    # message from KillUMXCmd into monitor.msgCommand.set()
                    self.Tk_root.after_idle( sensor.PollKillUMXCmd )

    #----------------------------------------------------------------
    def SendConfig( self ) :
        if DEBUG:
            print( 'SendConfig' )
            print( self.selectedSensors )

        if self.selectedSensors :
            validateSendConfig = messagebox.askyesno( 
                message = 'Send config to ' + \
                          ', '.join( self.selectedSensors ) + '?',
                icon = 'question', title = 'Send Config' )
            
            if not validateSendConfig :
                return

            # Clear the sendConfig msgs
            self.sendConfigMessages = ''

            # Schedule SendConfigCmd for each sensor and store the Popen object
            for key in self.selectedSensors :
                sensor = self.SensorCollection.SensorDict[ key ]

                if not sensor.sendConfigPopenBusy :
                    sensor.sendConfigStatusMsg = ''
                    sensor.sendConfigPopenBusy = True
                    sensor.sendConfigPopen = \
                        MonitorCommands.SendConfigCmd( sensor )

                    # Register a callback to poll and report the resultant
                    # message from HaltCmd into monitor.msgCommand.set()
                    self.Tk_root.after_idle( sensor.PollSendConfigCmd )

    #----------------------------------------------------------------
    def Halt( self ) :
        if DEBUG:
            print( 'Halt' )
            print( self.selectedSensors )

        if self.selectedSensors :
            validateHalt = messagebox.askyesno( 
                message = 'Halt ' + \
                          ', '.join( self.selectedSensors ) + '?',
                icon = 'question', title = 'Halt' )
            
            if not validateHalt :
                return

            # Clear the halt msgs
            self.haltMessages = ''

            # Schedule HaltCmd for each sensor and store the Popen object
            for key in self.selectedSensors :
                sensor = self.SensorCollection.SensorDict[ key ]

                if not sensor.haltPopenBusy :
                    sensor.haltStatusMsg = ''
                    sensor.haltPopenBusy = True
                    sensor.haltPopen     = MonitorCommands.HaltCmd( sensor )

                    # Register a callback to poll and report the resultant
                    # message from HaltCmd into monitor.msgCommand.set()
                    self.Tk_root.after_idle( sensor.PollHaltCmd )

    #----------------------------------------------------------------
    def Reboot( self ) :
        if DEBUG:
            print( 'Reboot' )
            print( self.selectedSensors )

        if self.selectedSensors :
            validateReboot = messagebox.askyesno( 
                message = 'Reboot ' + \
                          ', '.join( self.selectedSensors ) + '?',
                icon = 'question', title = 'Reboot' )
            
            if not validateReboot :
                return

            # Clear the reboot msgs
            self.rebootMessages = ''

            # Schedule RebootCmd for each sensor and store the Popen object
            for key in self.selectedSensors :
                sensor = self.SensorCollection.SensorDict[ key ]

                if not sensor.rebootPopenBusy :
                    sensor.rebootStatusMsg = ''
                    sensor.rebootPopenBusy = True
                    sensor.rebootPopen     = MonitorCommands.RebootCmd( sensor )

                    # Register a callback to poll and report the resultant
                    # message from RebootCmd into monitor.msgCommand.set()
                    self.Tk_root.after_idle( sensor.PollRebootCmd )

    #----------------------------------------------------------------
    def TimeMonitor( self ):
        if DEBUG:
            print( "TimeMonitor()" )
            print( self.selectedSensors )

        if self.selectedSensors :
            # Show any messages
            self.msgTime.set( self.timeMessages )
            # Clear the time msgs
            self.timeMessages = ''

            # Schedule TimeCmd for each sensor
            for key in self.selectedSensors :
                sensor = self.SensorCollection.SensorDict[ key ]

                if not sensor.timePopenBusy :
                    sensor.timeStatusMsg = ''
                    sensor.timePopenBusy = True
                    sensor.timePopen     = MonitorCommands.TimeCmd( sensor )
                
                    # Register a callback to poll and report the resultant
                    # message from TimeCmd into monitor.msgTime.set( msg )
                    self.Tk_root.after_idle( sensor.PollTimeCmd )

        # Re-register TimeMonitor for another callback
        if self.pollOnOff.get() :
            self.Tk_root.after( self.args.timeRefresh, self.TimeMonitor )

    #----------------------------------------------------------------
    def PingMonitor( self ):
        if DEBUG:
            print( "PingMonitor()" )
            print( self.selectedSensors )

        if self.selectedSensors :
            # Show current messages
            self.msgPing.set( self.pingMessages )
            # Clear the ping msgs
            self.pingMessages = ''

            # Schedule PingCmd for each sensor and store the Popen object
            for key in self.selectedSensors :
                sensor = self.SensorCollection.SensorDict[ key ]

                if not sensor.pingPopenBusy :
                    sensor.pingStatusMsg = ''
                    sensor.pingPopenBusy = True
                    sensor.pingPopen     = MonitorCommands.PingCmd( sensor )
                
                    # Register a callback to poll and report the resultant
                    # message from PingCmd into monitor.msgPing.set()
                    self.Tk_root.after_idle( sensor.PollPingCmd )

        # Re-register this function for another callback
        if self.pollOnOff.get() :
            self.Tk_root.after( self.args.pingRefresh, self.PingMonitor )

    #----------------------------------------------------------------
    def DataFileMonitor( self ):
        if DEBUG:
            print( "DataFileMonitor()" )

        # Show the data msgs since the last monitor call
        if self.selectedSensors :
            self.msgDataFile.set( self.dataMessages )
            # Clear the data msgs
            self.dataMessages = ''

            # Schedule DataCmd for each sensor and store the Popen object
            for key in self.selectedSensors :
                sensor = self.SensorCollection.SensorDict[ key ]

                if not sensor.dataPopenBusy :
                    sensor.dataStatusMsg = ''
                    sensor.dataPopenBusy = True
                    sensor.dataPopen = \
                       MonitorCommands.DataFileCmd( sensor )
                
                    # Register a callback to poll and report the resultant
                    # message from DataCmd into monitor.msgData.set()
                    self.Tk_root.after_idle( sensor.PollDataCmd )

        # Re-register this function for another callback
        if self.pollOnOff.get() :
            self.Tk_root.after( self.args.dataRefresh, self.DataFileMonitor )

    #----------------------------------------------------------------
    def LogFileMonitor( self ):
        if DEBUG:
            print( "LogFileMonitor()" )

        # Show the log msgs since the last monitor call
        if self.selectedSensors :
            self.msgLogFile.set( self.logMessages )
            # Clear the log msgs
            self.logMessages = ''

            # Schedule LogCmd for this sensor and store the Popen object
            for key in self.selectedSensors :
                sensor = self.SensorCollection.SensorDict[ key ]

                if not sensor.logPopenBusy :
                    sensor.logStatusMsg = ''
                    sensor.logPopenBusy = True
                    sensor.logPopen = \
                       MonitorCommands.LogFileCmd( sensor )
                
                    # Register a callback to poll and report the resultant
                    # message from LogCmd into monitor.msgLog.set()
                    self.Tk_root.after_idle( sensor.PollLogCmd )

        # Re-register this function for another callback
        if self.pollOnOff.get() :
            self.Tk_root.after( self.args.logRefresh, self.LogFileMonitor )

    #----------------------------------------------------------------
    def UMXMonitor( self ):
        if DEBUG:
            print( "UMXMonitor()" )

        # Show the umx msgs since the last monitor call
        if self.selectedSensors :
            self.msgUMX.set( self.umxMessages )
            # Clear the umx msgs
            self.umxMessages = ''

            # Schedule UMXCmd for each sensor and store the Popen object
            for key in self.selectedSensors :
                sensor = self.SensorCollection.SensorDict[ key ]

                if not sensor.umxPopenBusy :
                    sensor.umxStatusMsg = ''
                    sensor.umxPopenBusy = True
                    sensor.umxPopen = MonitorCommands.UMXCmd( sensor )
                
                    # Register a callback to poll and report the resultant
                    # message from UMXCmd into monitor.msgUMX.set()
                    self.Tk_root.after_idle( sensor.PollUMXCmd )

        # Re-register this function for another callback
        if self.pollOnOff.get() :
            self.Tk_root.after( self.args.umxRefresh, self.UMXMonitor )

    #----------------------------------------------------------------
    # Read the listbox selection and assign to selectedSensors
    #----------------------------------------------------------------
    def ProcessListbox( self, *args ):
        # Get the names of selected sensors
        selected = self.listBox.selection_get()
        selectedSensors = selected.split()

        if DEBUG:
            for sensor in selectedSensors :
                print( 'ProcessListbox() ' + sensor )

        self.selectedSensors = selectedSensors

    #----------------------------------------------------------------
    def ShowAboutInfo( self ):
        messagebox.showinfo( message = self.Version )

    #----------------------------------------------------------------
    def OpenFile( self ):
        sensorFile = filedialog.askopenfilename(
            initialfile = 'Sensors.txt', 
            filetypes   = [('Sensor Files', '*.txt')],
            multiple    = False )

        if not sensorFile :
            #messagebox.showinfo(message='Sensor file not loaded.')
            return

        self.selectedSensors = None
        self.sensorFile      = sensorFile
        self.SensorCollection.NewFile( self.sensorFile )

        # Clear the ListBox
        self.listBox.delete( 0, END )
        # Insert the sensor names into the Listbox
        i = 1
        for key in self.SensorCollection.SensorDict.keys() :
            self.listBox.insert( i, key )
            i = i + 1

        # Colorize alternating lines of the listbox
        for i in range( 0, len(self.SensorCollection.SensorDict.keys()), 2 ):
            self.listBox.itemconfigure( i, background = '#f0f0ff' )

        # Get a suggestion for self.configFilePath from the first sensor
        # Note that dict.values() is a view in Py3, not a sliceable item
        # Convert to a list to use indexing, but on a copy for thread safety
        sensor = list( self.SensorCollection.SensorDict.copy().values() )[0]
        self.configFilePath = sensor.configInPath

    #----------------------------------------------------------------
    def OpenConfigFile( self ):
        configFile = filedialog.askopenfilename(
            initialdir  = self.configFilePath,
            # initialfile = 'UMX1.4.cfg', 
            filetypes   = [('Sensor Config Files', '*.cfg')],
            multiple    = False )

        if not configFile :
            #messagebox.showinfo( message = 'Config file not loaded.' )
            return

        self.msgCommand.set( MonitorCommands.GetLocalUTC() + \
                             ' New sensor config opened: ' + configFile )

        cmdLine = 'gedit ' + configFile

        if DEBUG:
            print( 'OpenConfigFile(): ' + cmdLine ) 

        sp = subprocess.Popen( cmdLine, shell = True )


#----------------------------------------------------------------------------
# Main module
#----------------------------------------------------------------------------
def main():
    
    # Parse the command line
    args = ParseCmdLine()

    # Initialize the root Tk object
    root = Tk()
    root.title( 'NCPA Sensor Monitor' )

    monitor = NCPA_Monitor( root, args )
    
    # Read the program configuration files, create the NCPASensor
    # objects and populate a dictionary of NCPASensor objects
    monitor.SensorCollection = \
        NCPASensor.SensorCollection( monitor )
  
    # Create the main widget Frame (window)
    mainframe = ttk.Frame( root, padding = "3 3 6 6" )

    # Setup the menu bar
    menuBar = Menu( root )
    root.config( menu = menuBar )
    #-----------------------------------------------
    menuFile = Menu( menuBar, tearoff = False )
    menuBar.add_cascade( menu = menuFile, label = 'File' )
    menuFile.add_command( label = 'Open', command = monitor.OpenFile )
    #-----------------------------------------------
    menuConfig = Menu( menuBar, tearoff = False )
    menuBar.add_cascade( menu = menuConfig, label = 'Config' )
    menuConfig.add_command( label = 'Open', command = monitor.OpenConfigFile )
    menuConfig.add_command( label = 'Polling', command = monitor.ChangePolling)
    #-----------------------------------------------
    menuHelp = Menu( menuBar, tearoff = False )
    menuBar.add_cascade( menu = menuHelp, label = 'Help' )
    menuHelp.add_command( label = 'About', command = monitor.ShowAboutInfo )

    # Setup the window layout with the 'grid' geometry manager. 
    # This is the main window, so we set it to use column = 0, row = 0
    # The value of the "sticky" option is a string of 0 or more of the 
    # compass directions N S E W, specifying which edges of the cell the 
    # widget should be "stuck" to.
    mainframe.grid( column = 0, row = 0, sticky = (N, W, E, S) )

    # Create a button to press to plot the data of the selected sensor
    # Tell the button to call monitor.PlotData() when it is pressed
    plotButton = ttk.Button( mainframe, text = "Plot",
                             command = monitor.PlotData )

    # Button to copy a sensor config file to the sensor 
    sendConfigButton = ttk.Button( mainframe, text = "Send Config",
                                   command = monitor.SendConfig )

    # Button to start the UMXScheduler 
    startUMXButton = ttk.Button( mainframe, text = "Start UMX",
                                 command = monitor.StartUMX )

    # Button to kill UMXScheduler and Control
    killUMXButton = ttk.Button( mainframe, text = "Kill UMX",
                                command = monitor.KillUMX )

    # Button to halt the sensor
    haltButton = ttk.Button( mainframe, text = "Halt",
                             command = monitor.Halt )

    # Button to reboot the sensor
    rebootButton = ttk.Button( mainframe, text = "Reboot",
                               command = monitor.Reboot )

    # Radiobutton for polling on/off
    pollButton = ttk.Checkbutton( mainframe, text = 'Poll On/Off', 
                                  command  = monitor.PollChanged, 
                                  variable = monitor.pollOnOff,
                                  onvalue = True, offvalue = False )

    # Status handler
    monitor.Status = Status( monitor )
    # Label that will show the status as green, yellow or red
    statusLabel = ttk.Label( mainframe, relief="sunken", 
                             image = monitor.Status.OKGraphic )
    monitor.Status.Label = statusLabel

    # Labels for messages
    # Set the textvariable StringVar() to watch for set() updates
    logFileLabel  = ttk.Label( mainframe, textvariable = monitor.msgLogFile,
                               background = 'white' )
    dataFileLabel = ttk.Label( mainframe, textvariable = monitor.msgDataFile,
                               background = 'white' )
    timeLabel     = ttk.Label( mainframe, textvariable = monitor.msgTime,
                               background = 'white' )
    pingLabel     = ttk.Label( mainframe, textvariable = monitor.msgPing,
                               background = 'white' )
    commandLabel  = ttk.Label( mainframe, textvariable = monitor.msgCommand,
                               background = 'white' )
    umxLabel      = ttk.Label( mainframe, textvariable = monitor.msgUMX,
                               background = 'white' )

    # Create the Sensor Listbox
    monitor.listBox = Listbox( mainframe, height = 5, width = 10, 
                               selectmode = EXTENDED )

    # Insert the sensor names into the Listbox
    # The listvariable = [] option won't work if
    # there is whitespace in a name, so insert them manually
    i = 1
    for key in monitor.SensorCollection.SensorDict.keys() :
        monitor.listBox.insert( i, key )
        i = i + 1

    # Create a vertical scroll bar for the Listbox
    # Tell the scrollbar that it will call the Listbox yview function
    # when the user moves the scrollbar
    scrollBar = ttk.Scrollbar( mainframe, orient = VERTICAL, 
                               command = monitor.listBox.yview )

    # Tell the Listbox that it will scroll according to the scrollBar
    monitor.listBox.configure( yscrollcommand = scrollBar.set )

    # This tells the Listbox to call the function ProcessListbox()
    # when the selection in the listbox changes
    monitor.listBox.bind('<<ListboxSelect>>', monitor.ProcessListbox)

    # Colorize alternating lines of the listbox
    for i in range( 0, len( monitor.SensorCollection.SensorDict.keys() ), 2):
        monitor.listBox.itemconfigure( i, background = '#f0f0ff' )

    # Grid all the widgets - This is the layout of the window
    # This application has 8 columns and 6 rows
    monitor.listBox.grid ( column = 0, row = 1, sticky = (N,S),   rowspan = 4 )
    scrollBar.grid       ( column = 0, row = 1, sticky = (E,N,S), rowspan = 4 )

    statusLabel.grid     ( column = 0, row = 0, sticky = (W,E) )
    pollButton.grid      ( column = 1, row = 0, sticky = (W,E) )
    plotButton.grid      ( column = 2, row = 0, sticky = (W,E) )
    sendConfigButton.grid( column = 3, row = 0, sticky = (W,E) )
    startUMXButton.grid  ( column = 4, row = 0, sticky = (W,E) )
    killUMXButton.grid   ( column = 5, row = 0, sticky = (W,E) )
    haltButton.grid      ( column = 6, row = 0, sticky = (W,E) )
    rebootButton.grid    ( column = 7, row = 0, sticky = (W,E) )

    timeLabel.grid     ( column = 1, row = 1, sticky = (N,S,W,E), 
                         columnspan = 3 )
    pingLabel.grid     ( column = 4, row = 1, sticky = (N,S,W,E), 
                         columnspan = 4 )
    umxLabel.grid      ( column = 1, row = 2, sticky = (N,S,W,E), 
                         columnspan = 7 )
    dataFileLabel.grid ( column = 1, row = 3, sticky = (N,S,W,E), 
                         columnspan = 7 )
    logFileLabel.grid  ( column = 1, row = 4, sticky = (N,S,W,E),
                         columnspan = 7 )
    commandLabel.grid  ( column = 1, row = 5, sticky = (N,S,W,E), 
                         columnspan = 7 )
    
    # For each widget in the mainframe, set some padding around
    # the widget to space things out and look better
    for child in mainframe.winfo_children():
        child.grid_configure( padx = 3, pady = 3 )

    # Add a Sizegrip to make resizing easier.
    ttk.Sizegrip(mainframe).grid(column = 99, row = 99, sticky = (N,S,E,W))

    # Setup the resize control with the 'grid' geometry manager. 
    # Every column and row has a "weight" grid option associated with it, 
    # which tells it how much it should grow if there is extra room in 
    # the master to fill. By default, the weight of each column or row 
    # is 0, meaning don't expand to fill space. Here we set the weight
    # to 1 telling the widget to expand and fill space as the window 
    # is resized. 
    # Make Sure to set on the root window!!!
    root.columnconfigure( 0, weight = 1 )
    root.rowconfigure   ( 0, weight = 1 )
    # Don't resize the column 0 - the width of the Listbox
    mainframe.columnconfigure( 0, weight = 0 )
    mainframe.columnconfigure( 1, weight = 1 )
    mainframe.columnconfigure( 2, weight = 1 )
    mainframe.columnconfigure( 3, weight = 1 )
    mainframe.columnconfigure( 4, weight = 1 )
    mainframe.columnconfigure( 5, weight = 1 )
    # Don't resize the row 0 - the depth of the status & buttons
    mainframe.rowconfigure   ( 0, weight = 0 )
    mainframe.rowconfigure   ( 1, weight = 1 )
    mainframe.rowconfigure   ( 2, weight = 1 )
    mainframe.rowconfigure   ( 3, weight = 1 )
    mainframe.rowconfigure   ( 4, weight = 1 )
    mainframe.rowconfigure   ( 5, weight = 1 )

    # Start the Status Monitor label
    monitor.Status.Update()

    # Enter the Tk mainloop to service the window
    root.mainloop()

#----------------------------------------------------------------------------
def ParseCmdLine():
    global DEBUG

    parser = argparse.ArgumentParser( description = 'NCPA Sensor Monitor' )
    
    parser.add_argument('-a', '--subnet',
                        dest   = 'subnet', type = str, 
                        action = 'store', default = '192.168.1.',
                        help = 'IP subnet prefix (192.168.1.).')

    parser.add_argument('-s', '--sensorList',
                        dest   = 'sensorList', type = str, 
                        action = 'store', default = '',
                        help = 'Sensor IP address suffix (51,106,169).')

    parser.add_argument('-f', '--sensorFile',
                        dest   = 'sensorFile', type = str, 
                        action = 'store', default = '',
                        help = 'Sensor parameter file name.')

    homePath = os.environ['HOME']
    parser.add_argument('-m', '--monitorPath',
                        dest   = 'monitorPath', type = str, 
                        action = 'store', 
                        #default = homePath + \
                        #          '/Sensor/monitorGUI',
                        default = './',
                        help = 'Path to Monitor.py ' + \
                               '(~/Sensor/monitorGUI).')

    parser.add_argument('-p', '--pingRefresh',
                        dest   = 'pingRefresh', type = float, 
                        action = 'store', default = 3.0,
                        help = 'Ping monitor refresh interval (3 s).' )

    parser.add_argument('-u', '--umxRefresh',
                        dest   = 'umxRefresh', type = float,
                        action = 'store', default = 4.0,
                        help = 'UMX monitor refresh interval (4 s).' )

    parser.add_argument('-l', '--logRefresh',
                        dest   = 'logRefresh', type = float, 
                        action = 'store', default = 5.0,
                        help = 'Log file monitor refresh interval (5 s).' )

    parser.add_argument('-d', '--dataRefresh',
                        dest   = 'dataRefresh', type = float, 
                        action = 'store', default = 6.0,
                        help = 'Data file monitor refresh interval (6 s).' )

    parser.add_argument('-t', '--timeRefresh',
                        dest   = 'timeRefresh', type = float, 
                        action = 'store', default = 5.0,
                        help = 'Time monitor refresh interval (5 s).' )

    parser.add_argument('-v', '--verbose',
                        dest   = 'verbose', # type = bool, 
                        action = 'store_true', default = False )

    args = parser.parse_args()

    # convert the refresh args to milliseconds for after() 
    args.pingRefresh = round( args.pingRefresh * 1000 )
    args.umxRefresh  = round( args.umxRefresh  * 1000 )
    args.logRefresh  = round( args.logRefresh  * 1000 )
    args.dataRefresh = round( args.dataRefresh * 1000 )
    args.timeRefresh = round( args.timeRefresh * 1000 )

    # Save the users home directory
    args.homePath = homePath

    # set DEBUG status
    DEBUG = args.verbose

    return args

#----------------------------------------------------------------------------
# Provide for cmd line invocation independent of import
if __name__ == "__main__":
    main()
