#----------------------------------------------------------------------------
# Name:     NCPASensor.py
# Purpose:  Object definitions for NCPA Sensors
#           
# Author: J Park
#
# Created:      
#----------------------------------------------------------------------------

import MonitorCommands
import Monitor

DEBUG = False # Set True by the -v (verbose) option

#---------------------------------------------------------
# Geo-reference Class
#---------------------------------------------------------
class Position:
    def __init__( self, latitude, longitude, altitude ):
        self.latitude   = latitude
        self.longitude  = longitude
        self.altitude   = altitude
        self.X_relative = 0.
        self.Y_relative = 0.
        self.Z_relative = 0.

#---------------------------------------------------------
# Sensor Class
#---------------------------------------------------------
class NCPASensor:
    def __init__( self, monitor, SN, IP, 
                  configInPath    = './',
                  configInFile    = 'SN123_UMSX1.4.cfg',
                  configOutPath   = '~/', 
                  configOutFile   = 'UMSX1.4.cfg',
                  UMXSchedulerCmd = 'run_scheduler.sh' ):

        self.name            = 'SN' + SN     # string: 'SN056'
        self.serialNumber    = SN            # 3 digit string: '056'
        self.IP              = IP            # string of IP address
        self.configInPath    = configInPath
        self.configInFile    = configInFile
        self.configOutPath   = configOutPath
        self.configOutFile   = configOutFile
        self.UMXSchedulerCmd = UMXSchedulerCmd
        self.Position        = None
        # These are specific to Monitor.py
        self.monitor                 = monitor
        self.timePopen               = None
        self.pingPopen               = None
        self.dataPopen               = None
        self.dataSubCmdPopen         = None
        self.logPopen                = None
        self.logSubCmdPopen          = None
        self.umxPopen                = None
        self.rebootPopen             = None
        self.haltPopen               = None
        self.sendConfigPopen         = None
        self.startUMXSchedulerPopen  = None
        self.killUMXPopen            = None
        self.killUMXSubCmdPopen      = None
        self.killUMXSubCmd2Popen     = None
        self.killUMXSubCmd3Popen     = None
        self.plotPopen               = None
        self.timePopenBusy           = False
        self.pingPopenBusy           = False
        self.dataPopenBusy           = False
        self.dataSubCmdPopenBusy     = False
        self.logPopenBusy            = False
        self.logSubCmdPopenBusy      = False
        self.umxPopenBusy            = False
        self.rebootPopenBusy         = False
        self.haltPopenBusy           = False
        self.sendConfigPopenBusy     = False
        self.killUMXPopenBusy        = False
        self.killUMXSubCmdPopenBusy  = False
        self.killUMXSubCmd2PopenBusy = False
        self.killUMXSubCmd3PopenBusy = False
        self.startUMXSchedulerPopenBusy = False
        self.plotPopenBusy           = False
        self.timeStatusMsg           = ''
        self.pingStatusMsg           = ''
        self.dataStatusMsg           = ''
        self.logStatusMsg            = ''
        self.umxStatusMsg            = ''
        self.rebootStatusMsg         = ''
        self.haltStatusMsg           = ''
        self.sendConfigStatusMsg     = ''
        self.startUMXStatusMsg       = ''
        self.killUMXStatusMsg        = ''
        self.killUMXSubCmdStatusMsg  = ''
        self.killUMXSubCmd2StatusMsg = ''
        self.killUMXSubCmd3StatusMsg = ''
        self.plotStatusMsg           = ''
        self.firstDataDir            = ''
        self.firstDataFile           = ''
        self.firstLogFile            = ''
        self.umxSchedPID             = ''

    def Print( self ):
        print( 'ConfigInFile: ' + self.configInFile )
        print( 'SerialNumber: ' + self.SN )
        print( 'IP: '           + self.IP )
        print( 'ConfigOutFile: '+ self.configOutFile )

    #-----------------------------------------------------------
    # These are specific to Monitor.py
    #-----------------------------------------------------------
    def PollTimeCmd( self ):
        if self.timePopen:
            # check the timePopen object (subprocess.Popen) with
            # a poll and see if the command has finished
            self.timePopen.poll()

            # None value indicates that the process hasn’t terminated yet.
            if self.timePopen.returncode == None :
                # register this function for a callback after 200 ms
                self.monitor.Tk_root.after( 200, self.PollTimeCmd )
            else:
                # Post the return status
                timeStr = MonitorCommands.GetLocalUTC()
                if self.timePopen.returncode != 0 :
                    msg = timeStr + ' ' + self.name + ': date Failed.\n'
                else:
                    # communicate() returns a tuple: (stdoutdata, stderrdata),
                    # sets returncode, and will block until the process returns.
                    # The returned stdoutdata can be byte string data, in which
                    # case it needs to be decoded.
                    sp_out = self.timePopen.communicate() 
                    msg = timeStr + ' ' + self.name + ': ' + \
                          sp_out[0].decode("utf-8")

                self.timeStatusMsg = msg

                # Add the status to the monitor.timeMessages and
                # display the text to monitor.msgCommand
                self.monitor.timeMessages = self.monitor.timeMessages + \
                                            self.timeStatusMsg

                if 'Failed' in msg :
                    self.monitor.Status.timeStatus = Monitor.MonitorStatus.ERROR
                else:
                    self.monitor.Status.timeStatus = Monitor.MonitorStatus.OK

                del( self.timePopen )
                self.timePopen     = None
                self.timePopenBusy = False

    #-----------------------------------------------------------
    def PollPingCmd( self ):
        if self.pingPopen:
            # check the pingPopen object (subprocess.Popen) with
            # a poll and see if the command has finished
            self.pingPopen.poll()

            # None value indicates that the process hasn’t terminated yet.
            if self.pingPopen.returncode == None :
                # register this function for a callback after 200 ms
                self.monitor.Tk_root.after( 200, self.PollPingCmd )
            else:
                # Post the return status
                timeStr = MonitorCommands.GetLocalUTC()

                sp_out  = self.pingPopen.communicate() 
                pingOut = sp_out[0].decode("utf-8").split()

                msg = MonitorCommands.GetLocalUTC() + ' ' + \
                      self.name + ': ' + ' '.join( pingOut[15:20] ) + '\n'

                self.pingStatusMsg = msg

                # Add the status to the monitor.pingMessages and
                # display the text to monitor.msgCommand
                self.monitor.pingMessages = self.monitor.pingMessages + \
                                            self.pingStatusMsg

                if '0 received' in msg :
                    self.monitor.Status.pingStatus = Monitor.MonitorStatus.ERROR
                else:
                    self.monitor.Status.pingStatus = Monitor.MonitorStatus.OK

                del( self.pingPopen )
                self.pingPopen     = None
                self.pingPopenBusy = False

    #-----------------------------------------------------------
    def PollDataCmd( self ):
        if self.dataPopen:
            # check the dataPopen object (subprocess.Popen) with
            # a poll and see if the command has finished
            self.dataPopen.poll()

            # None value indicates that the process hasn’t terminated yet.
            if self.dataPopen.returncode == None :
                # register this function for a callback after 200 ms
                self.monitor.Tk_root.after( 200, self.PollDataCmd )
            else:
                # Post the return status
                self.firstDataDir  = ''
                self.firstDataFile = ''

                timeStr = MonitorCommands.GetLocalUTC()
                if self.dataPopen.returncode != 0 :
                    msg = timeStr + ' ' + self.name + ': ls -lt /data' + \
                          ' Failed.\n'
                else:
                    sp_out = self.dataPopen.communicate() 
                    sp_ls_words       = sp_out[0].decode("utf-8").split() 
                    self.firstDataDir = sp_ls_words[0] # first dir in the list
                    msg = '' #timeStr + ' ls -t /data ' + self.name + \
                             #' ' + self.firstDataDir + '\n'

                    # Now call the DataFileSubCmd() to get the data file name
                    self.dataSubCmdPopen = \
                         MonitorCommands.DataFileSubCmd( self )

                    # Register a callback to poll and report the resultant
                    # message from DataFileSubCmd into monitor.msgData.set()
                    self.monitor.Tk_root.after_idle( self.PollDataSubCmd )

                # Report any status from the DataCmd
                self.dataStatusMsg = msg

                # Add the status to the monitor.dataMessages and
                # display the text to monitor.msgCommand
                self.monitor.dataMessages = self.monitor.dataMessages + \
                                            self.dataStatusMsg

                if 'Failed' in msg :
                    self.monitor.Status.dataStatus = Monitor.MonitorStatus.ERROR
                else:
                    self.monitor.Status.dataStatus = Monitor.MonitorStatus.OK

                del( self.dataPopen )
                self.dataPopen     = None
                self.dataPopenBusy = False

    #-----------------------------------------------------------
    def PollDataSubCmd( self ):
        if self.dataSubCmdPopen:
            # check the dataSubCmdPopen object (subprocess.Popen) with
            # a poll and see if the command has finished
            self.dataSubCmdPopen.poll()

            # None value indicates that the process hasn’t terminated yet.
            if self.dataSubCmdPopen.returncode == None :
                # register this function for a callback after 200 ms
                self.monitor.Tk_root.after( 200, self.PollDataSubCmd )
            else:
                # Post the return status
                timeStr = MonitorCommands.GetLocalUTC()

                if self.dataSubCmdPopen.returncode != 0 :
                    dataFileInfo = MonitorCommands.GetLocalUTC() + \
                                   ' ' + self.name + \
                                   ': ls -lt /data/' + self.firstDataDir + \
                                   ' Failed.\n'
                else:
                    # list of files in /data/
                    sp_out   = self.dataSubCmdPopen.communicate() 
                    ls_lines = sp_out[0].decode("utf-8").split('\n') 

                    if DEBUG:
                        print( ls_lines )

                    # the full file info is on the second line: ls_lines[1]
                    dataFileInfo = MonitorCommands.GetLocalUTC() + ' ' + \
                                   self.name + ': ' + ls_lines[1] + '\n'

                    # the file name is the last word on the second line
                    self.firstDataFile = ls_lines[1].split()[-1]

                self.dataStatusMsg = dataFileInfo

                # Add the status to the monitor.dataMessages and
                # display the text to monitor.msgCommand
                self.monitor.dataMessages = self.monitor.dataMessages + \
                                            self.dataStatusMsg

                if 'Failed' in dataFileInfo :
                    self.monitor.Status.dataStatus = Monitor.MonitorStatus.ERROR
                else:
                    self.monitor.Status.dataStatus = Monitor.MonitorStatus.OK

                del( self.dataSubCmdPopen )
                self.dataSubCmdPopen     = None
                self.dataSubCmdPopenBusy = False

    #-----------------------------------------------------------
    def PollLogCmd( self ):
        if self.logPopen:
            # check the logPopen object (subprocess.Popen) with
            # a poll and see if the command has finished
            self.logPopen.poll()

            # None value indicates that the process hasn’t terminated yet.
            if self.logPopen.returncode == None :
                # register this function for a callback after 200 ms
                self.monitor.Tk_root.after( 200, self.PollLogCmd )
            else:
                # Post the return status
                self.firstLogFile = ''
                timeStr = MonitorCommands.GetLocalUTC()

                if self.logPopen.returncode != 0 :
                    msg = timeStr + ' ' + self.name + ': ls -t /log' + \
                          ' Failed.\n'
                else:
                    sp_out = self.logPopen.communicate() 
                    # list of the files in /log
                    sp_words = sp_out[0].decode("utf-8").split()
                    # first file in the list
                    self.firstLogFile = sp_words[0]              
                    msg = '' #timeStr + ' ls -t /log ' + self.name + \
                             #' ' + self.firstLogFile + '\n'

                    # Now call the LogFileSubCmd() to get the log file name
                    self.logSubCmdPopen = \
                         MonitorCommands.LogFileSubCmd( self )

                    # Register a callback to poll and report the resultant
                    # message from LogFileSubCmd into monitor.msgLog.set()
                    self.monitor.Tk_root.after_idle( self.PollLogSubCmd )

                # Report any status from the LogCmd
                self.logStatusMsg = msg

                # Add the status to the monitor.logMessages and
                # display the text to monitor.msgCommand
                self.monitor.logMessages = self.monitor.logMessages + \
                                           self.logStatusMsg

                if 'Failed' in msg :
                    self.monitor.Status.logStatus = Monitor.MonitorStatus.ERROR
                else:
                    self.monitor.Status.logStatus = Monitor.MonitorStatus.OK

                del( self.logPopen )
                self.logPopen = None
                self.logPopenBusy = False

    #-----------------------------------------------------------
    def PollLogSubCmd( self ):
        if self.logSubCmdPopen:
            # check the logSubCmdPopen object (subprocess.Popen) with
            # a poll and see if the command has finished
            self.logSubCmdPopen.poll()

            # None value indicates that the process hasn’t terminated yet.
            if self.logSubCmdPopen.returncode == None :
                # register this function for a callback after 200 ms
                self.monitor.Tk_root.after( 200, self.PollLogSubCmd )
            else:
                # Post the return status
                timeStr = MonitorCommands.GetLocalUTC()

                if self.logSubCmdPopen.returncode != 0 :
                    logFileMsg = timeStr + ' ' + self.name + \
                                 ': ls -lt /log/' + self.firstLogFile + \
                                 ' Failed.\n'
                else:
                    # 
                    sp_out = self.logSubCmdPopen.communicate() 
                    logFileMsg = timeStr + ' ' + self.name + ': ' + \
                                 sp_out[0].decode("utf-8") + '\n'

                self.logStatusMsg = logFileMsg

                # Add the status to the monitor.logMessages and
                # display the text to monitor.msgCommand
                self.monitor.logMessages = self.monitor.logMessages + \
                                           self.logStatusMsg

                if 'Failed' in logFileMsg :
                    self.monitor.Status.logStatus = Monitor.MonitorStatus.ERROR
                else:
                    self.monitor.Status.logStatus = Monitor.MonitorStatus.OK

                del( self.logSubCmdPopen )
                self.logSubCmdPopen = None
                self.logSubCmdPopenBusy = False

    #-----------------------------------------------------------
    def PollUMXCmd( self ):
        if self.umxPopen:
            # check the umxPopen object (subprocess.Popen) with
            # a poll and see if the command has finished
            self.umxPopen.poll()

            # None value indicates that the process hasn’t terminated yet.
            if self.umxPopen.returncode == None :
                # register this function for a callback after 200 ms
                self.monitor.Tk_root.after( 200, self.PollUMXCmd )
            else:
                # Post the return status
                timeStr = MonitorCommands.GetLocalUTC()

                if self.umxPopen.returncode != 0 :
                    umxMsg = timeStr + ' ' + self.name + \
                             ': ps -e | grep UMXcontrol4.4.0 Failed.\n'
                else:
                    sp_out = self.umxPopen.communicate() 
                    umxMsg = timeStr + ' ' + self.name + ': ' + \
                             sp_out[0].decode("utf-8")

                self.umxStatusMsg = umxMsg

                # Add the status to the monitor.umxMessages and
                # display the text to monitor.msgCommand
                self.monitor.umxMessages = self.monitor.umxMessages + \
                                           self.umxStatusMsg

                if 'Failed' in umxMsg :
                    #self.monitor.Status.umxStatus = Monitor.MonitorStatus.ERROR
                    self.monitor.Status.umxStatus = Monitor.MonitorStatus.WARN
                else:
                    self.monitor.Status.umxStatus = Monitor.MonitorStatus.OK

                del( self.umxPopen )
                self.umxPopen = None
                self.umxPopenBusy = False

    #-----------------------------------------------------------
    def PollRebootCmd( self ):
        if self.rebootPopen:
            # check the rebootPopen object (subprocess.Popen) with
            # a poll and see if the command has finished
            self.rebootPopen.poll()

            # None value indicates that the process hasn’t terminated yet.
            if self.rebootPopen.returncode == None :
                # register this function for a callback after 200 ms
                self.monitor.Tk_root.after( 200, self.PollRebootCmd )
            else:
                # Post the return status
                timeStr = MonitorCommands.GetLocalUTC()

                #sp_out = self.rebootPopen.communicate() 

                if self.rebootPopen.returncode != 0 :
                    msg = timeStr + ' ' + self.name + \
                          ': Reboot command Failed.\n'
                else:
                    msg = timeStr + ' ' + self.name + ': Rebooting...\n'

                self.rebootStatusMsg = msg

                # Add the status to the monitor.rebootMessages and
                # display the text to monitor.msgCommand
                self.monitor.rebootMessages = self.monitor.rebootMessages + \
                                              self.rebootStatusMsg
                self.monitor.msgCommand.set( self.monitor.rebootMessages )

                if 'Failed' in msg :
                    self.monitor.Status.rebootStatus = \
                                        Monitor.MonitorStatus.ERROR
                else:
                    self.monitor.Status.rebootStatus = \
                                        Monitor.MonitorStatus.OK

                del( self.rebootPopen )
                self.rebootPopen = None
                self.rebootPopenBusy = False

    #-----------------------------------------------------------
    def PollHaltCmd( self ):
        if self.haltPopen:
            # check the haltPopen object (subprocess.Popen) with
            # a poll and see if the command has finished
            self.haltPopen.poll()

            # None value indicates that the process hasn’t terminated yet.
            if self.haltPopen.returncode == None :
                # register this function for a callback after 200 ms
                self.monitor.Tk_root.after( 200, self.PollHaltCmd )
            else:
                # Post the return status
                timeStr = MonitorCommands.GetLocalUTC()

                #sp_out = self.haltPopen.communicate() 

                if self.haltPopen.returncode != 0 :
                    msg = timeStr + ' ' + self.name + ': Halt command Failed.\n'
                else:
                    msg = timeStr + ' ' + self.name + ': Halting...\n'

                self.haltStatusMsg = msg

                # Add the status to the monitor.haltMessages and
                # display the text to monitor.msgCommand
                self.monitor.haltMessages = self.monitor.haltMessages + \
                                            self.haltStatusMsg
                self.monitor.msgCommand.set( self.monitor.haltMessages )

                if 'Failed' in msg :
                    self.monitor.Status.haltStatus = \
                                        Monitor.MonitorStatus.ERROR
                else:
                    self.monitor.Status.haltStatus = \
                                        Monitor.MonitorStatus.OK

                del( self.haltPopen )
                self.haltPopen = None
                self.haltPopenBusy = False

    #-----------------------------------------------------------
    def PollSendConfigCmd( self ):
        if self.sendConfigPopen:
            # check the sendConfigPopen object (subprocess.Popen) with
            # a poll and see if the command has finished
            self.sendConfigPopen.poll()

            # None value indicates that the process hasn’t terminated yet.
            if self.sendConfigPopen.returncode == None :
                # register this function for a callback after 200 ms
                self.monitor.Tk_root.after( 200, self.PollSendConfigCmd )
            else:
                # Post the return status
                timeStr = MonitorCommands.GetLocalUTC()

                #sp_out = self.sendConfigPopen.communicate() 

                if self.sendConfigPopen.returncode != 0 :
                    msg = timeStr + ' ' + self.name + \
                          ': SendConfig Failed.\n'
                else:
                    msg = timeStr + ' ' + self.name + ': Sent Config.\n'

                self.sendConfigStatusMsg = msg

                # Add the status to the monitor.sendConfigMessages and
                # display the text to monitor.msgCommand
                self.monitor.sendConfigMessages = \
                    self.monitor.sendConfigMessages + \
                    self.sendConfigStatusMsg

                self.monitor.msgCommand.set( self.monitor.sendConfigMessages )

                if 'Failed' in msg :
                    self.monitor.Status.sendConfigStatus = \
                                        Monitor.MonitorStatus.ERROR
                else:
                    self.monitor.Status.sendConfigStatus = \
                                        Monitor.MonitorStatus.OK

                del( self.sendConfigPopen )
                self.sendConfigPopen     = None
                self.sendConfigPopenBusy = False

    #-----------------------------------------------------------
    def PollKillUMXCmd( self ):
        if self.killUMXPopen:
            # check the killUMXPopen object (subprocess.Popen) with
            # a poll and see if the command has finished
            self.killUMXPopen.poll()

            # None value indicates that the process hasn’t terminated yet.
            if self.killUMXPopen.returncode == None :
                # register this function for a callback after 200 ms
                self.monitor.Tk_root.after( 200, self.PollKillUMXCmd )
            else:
                # Post the return status
                timeStr = MonitorCommands.GetLocalUTC()

                sp_out = self.killUMXPopen.communicate() 

                if self.killUMXPopen.returncode != 0 :
                    msg = MonitorCommands.GetLocalUTC() + ' ' + self.name + \
                          ': ps -e | grep UMXscheduler4 Failed.\n'
                else:
                    # the first element of the tuple is the command return
                    sp_ps = sp_out[0].decode("utf-8")
                    # first element of string split into a list is the pid
                    self.umxSchedPID = sp_ps.split()[0]

                    msg = '' # timeStr + ' KillUMX: ' + self.name + '\n'

                    # Now call the KillUMXFileSubCmd()
                    self.killUMXSubCmdPopen = \
                         MonitorCommands.KillUMXSubCmd( self )

                    # Register a callback to poll KillUMXSubCmd
                    self.monitor.Tk_root.after_idle( self.PollKillUMXSubCmd )

                self.killUMXStatusMsg = msg

                # Add the status to the monitor.killUMXMessages and
                # display the text to monitor.msgCommand
                self.monitor.killUMXMessages = self.monitor.killUMXMessages + \
                                               self.killUMXStatusMsg
                self.monitor.msgCommand.set( self.monitor.killUMXMessages )

                if 'Failed' in msg :
                    self.monitor.Status.killUMXStatus = \
                                        Monitor.MonitorStatus.ERROR
                else:
                    self.monitor.Status.killUMXStatus = \
                                        Monitor.MonitorStatus.OK

                del( self.killUMXPopen )
                self.killUMXPopen     = None
                self.killUMXPopenBusy = False

    #-----------------------------------------------------------
    def PollKillUMXSubCmd( self ):
        if self.killUMXSubCmdPopen:
            # check the killUMXSubCmdPopen object (subprocess.Popen) with
            # a poll and see if the command has finished
            self.killUMXSubCmdPopen.poll()

            # None value indicates that the process hasn’t terminated yet.
            if self.killUMXSubCmdPopen.returncode == None :
                # register this function for a callback after 200 ms
                self.monitor.Tk_root.after( 200, self.PollKillUMXSubCmd )
            else:
                # Post the return status
                timeStr = MonitorCommands.GetLocalUTC()

                sp_out = self.killUMXSubCmdPopen.communicate() 

                if self.killUMXSubCmdPopen.returncode != 0 :
                    msg = MonitorCommands.GetLocalUTC() + ' ' + self.name + \
                          ': kill -9 UMXscheduler4 (' + self.umxSchedPID + \
                          ') Failed: ' + sp_out[0].decode("utf-8") + '\n'
                else:
                    msg = timeStr + ' ' + self.name + \
                          ': Killed UMXscheduler4 with PID ' + \
                          self.umxSchedPID + '\n'

                    # Now call the KillUMXFileSubCmd2()
                    self.killUMXSubCmd2Popen = \
                         MonitorCommands.KillUMXSubCmd2( self )

                    # Register a callback to poll KillUMXSubCmd2
                    self.monitor.Tk_root.after_idle( self.PollKillUMXSubCmd2 )

                self.killUMXSubCmdStatusMsg = msg

                # Add the status to the monitor.killUMXMessages and
                # display the text to monitor.msgCommand
                self.monitor.killUMXMessages = self.monitor.killUMXMessages + \
                                               self.killUMXSubCmdStatusMsg
                self.monitor.msgCommand.set( self.monitor.killUMXMessages )

                if 'Failed' in msg :
                    self.monitor.Status.killUMXStatus = \
                                        Monitor.MonitorStatus.ERROR
                else:
                    self.monitor.Status.killUMXStatus = \
                                        Monitor.MonitorStatus.OK

                del( self.killUMXSubCmdPopen )
                self.killUMXSubCmdPopen     = None
                self.killUMXSubCmdPopenBusy = False

    #-----------------------------------------------------------
    def PollKillUMXSubCmd2( self ):
        if self.killUMXSubCmd2Popen:
            # check the killUMXSubCmd2Popen object (subprocess.Popen) with
            # a poll and see if the command has finished
            self.killUMXSubCmd2Popen.poll()

            # None value indicates that the process hasn’t terminated yet.
            if self.killUMXSubCmd2Popen.returncode == None :
                # register this function for a callback after 200 ms
                self.monitor.Tk_root.after( 200, self.PollKillUMXSubCmd2 )
            else:
                # Post the return status
                timeStr = MonitorCommands.GetLocalUTC()

                sp_out = self.killUMXSubCmd2Popen.communicate() 

                if self.killUMXSubCmd2Popen.returncode != 0 :
                    msg = MonitorCommands.GetLocalUTC() + ' ' + self.name + \
                          ': ps -e | grep UMXcontrol4.4.0 Failed.\n'
                else:
                    # the first element of the tuple is the command return
                    sp_ps = sp_out[0].decode("utf-8")
                    # first element of string split into a list is the pid
                    self.umxControlPID = sp_ps.split()[0]

                    msg = '' # timeStr + ' ' + self.name + \
                    #' Killed UMXscheduler4 with PID: ', umxSchedPID + '\n'

                    # Now call the KillUMXFileSubCmd3()
                    self.killUMXSubCmd3Popen = \
                         MonitorCommands.KillUMXSubCmd3( self )

                    # Register a callback to poll KillUMXSubCmd3
                    self.monitor.Tk_root.after_idle( self.PollKillUMXSubCmd3 )

                self.killUMXSubCmd2StatusMsg = msg

                # Add the status to the monitor.killUMXMessages and
                # display the text to monitor.msgCommand
                self.monitor.killUMXMessages = self.monitor.killUMXMessages + \
                                               self.killUMXSubCmd2StatusMsg
                self.monitor.msgCommand.set( self.monitor.killUMXMessages )

                if 'Failed' in msg :
                    self.monitor.Status.killUMXStatus = \
                                        Monitor.MonitorStatus.ERROR
                else:
                    self.monitor.Status.killUMXStatus = \
                                        Monitor.MonitorStatus.OK

                del( self.killUMXSubCmd2Popen )
                self.killUMXSubCmd2Popen     = None
                self.killUMXSubCmd2PopenBusy = False

    #-----------------------------------------------------------
    def PollKillUMXSubCmd3( self ):
        if self.killUMXSubCmd3Popen:
            # check the killUMXSubCmd3Popen object (subprocess.Popen) with
            # a poll and see if the command has finished
            self.killUMXSubCmd3Popen.poll()

            # None value indicates that the process hasn’t terminated yet.
            if self.killUMXSubCmd3Popen.returncode == None :
                # register this function for a callback after 200 ms
                self.monitor.Tk_root.after( 200, self.PollKillUMXSubCmd3 )
            else:
                # Post the return status
                timeStr = MonitorCommands.GetLocalUTC()

                sp_out = self.killUMXSubCmd3Popen.communicate() 

                if self.killUMXSubCmd3Popen.returncode != 0 :
                    msg = timeStr + ' ' + self.name + ': kill -9 ' + \
                          self.umxControlPID + ' Failed: ' + \
                          sp_out[0].decode("utf-8") + '\n'
                else:
                    msg = timeStr + ' ' + self.name + \
                          ': Killed UMXcontrol4.4.0 with PID ' + \
                          self.umxControlPID + '\n'

                self.killUMXSubCmd3StatusMsg = msg

                # Add the status to the monitor.killUMXMessages and
                # display the text to monitor.msgCommand
                self.monitor.killUMXMessages = self.monitor.killUMXMessages + \
                                               self.killUMXSubCmd3StatusMsg
                self.monitor.msgCommand.set( self.monitor.killUMXMessages )

                if 'Failed' in msg :
                    self.monitor.Status.killUMXStatus = \
                                        Monitor.MonitorStatus.ERROR
                else:
                    self.monitor.Status.killUMXStatus = \
                                        Monitor.MonitorStatus.OK

                del( self.killUMXSubCmd3Popen )
                self.killUMXSubCmd3Popen     = None
                self.killUMXSubCmd3PopenBusy = False

    #-----------------------------------------------------------
    def PollStartUMXSchedulerCmd( self ):
        if self.startUMXSchedulerPopen:
            # check the startUMXSchedulerPopen object (subprocess.Popen) with
            # a poll and see if the command has finished
            self.startUMXSchedulerPopen.poll()

            # None value indicates that the process hasn’t terminated yet.
            if self.startUMXSchedulerPopen.returncode == None :
                # register this function for a callback after 200 ms
                self.monitor.Tk_root.after( 200, self.PollStartUMXSchedulerCmd )
            else:
                # Post the return status
                timeStr = MonitorCommands.GetLocalUTC()

                sp_out = self.startUMXSchedulerPopen.communicate() 

                if DEBUG:
                    print( 'PollStartUMXSchedulerCmd() returncode: ' + \
                            str(self.startUMXSchedulerPopen.returncode) )
                    print( 'PollStartUMXSchedulerCmd() : ' + \
                            sp_out[0].decode("utf-8") )

                if self.startUMXSchedulerPopen.returncode != 0 :
                    msg = timeStr + ' ' + self.name + ': StartUMX Failed: ' + \
                          sp_out[0].decode("utf-8") + '\n'
                else:
                    msg = timeStr + ' ' + self.name + ': StartUMX\n'

                self.startUMXSchedulerStatusMsg = msg

                # Add the status to the monitor.startUMXMessages and
                # display the text to monitor.msgCommand
                self.monitor.startUMXMessages = \
                     self.monitor.startUMXMessages + \
                     self.startUMXSchedulerStatusMsg
                self.monitor.msgCommand.set( self.monitor.startUMXMessages )

                if 'Failed' in msg :
                    self.monitor.Status.startUMXStatus = \
                                        Monitor.MonitorStatus.ERROR
                else:
                    self.monitor.Status.startUMXStatus = \
                                        Monitor.MonitorStatus.OK

                del( self.startUMXSchedulerPopen )
                self.startUMXSchedulerPopen     = None
                self.startUMXSchedulerPopenBusy = False

#---------------------------------------------------------
# SensorCollection has a dictionary of NCPASensor objects
#---------------------------------------------------------
class SensorCollection:
    def __init__( self, monitor ):
        self.monitor    = monitor
        self.sensorFile = monitor.sensorFile # from -f command line
        self.SensorDict = {}
        # OpenFile() in the gui menubar will call NewFile() 
        # which will populate the SensorDict from a file.

        # If the user has specified sensors with -s, call
        # CreateSensorsFromCmd() 
        if self.monitor.args.sensorList :
            self.CreateSensorsFromCmd()

        elif self.monitor.args.sensorFile :
            # If the user specified a file with -f, call NewFile()
            self.NewFile( self.sensorFile )

    #----------------------------------------------------- 
    def NewFile( self, sensorFile ):
        # sensorFile is from filedialog.askopenfilename in FileOpen
        # or the -f command line option 
        self.sensorFile = str( sensorFile )
        del( self.SensorDict )
        self.SensorDict = {}
        # Populate the SensorDict from the sensorFile
        self.CreateSensorsFromFile()

    #----------------------------------------------------- 
    def ValidIPAddress( self, IPAddress ) :
        # Verify a reasonable IP as a.b.c.d 
        digits = IPAddress.split( '.' )
        if len( digits ) != 4 :
            return False
        
        # Every field must have at least one digit
        for digit in digits :
            if not digit :
                return False

        # Digits must be > 0 and < 256
        for digit in digits :
            val = int( digit ) 
            if val < 1 or val > 255 :
                return False

        return True

    #----------------------------------------------------- 
    def CreateSensorsFromFile( self ):
        global DEBUG 
        DEBUG = self.monitor.args.verbose

        # Read the sensorFile
        fi    = open( self.sensorFile, 'r' )
        lines = fi.readlines()
        fi.close()
        numLines = len( lines )

        # Process the sensorFile
        # The delimeters are: Sensor { ... }
        # with fields: IP = xxx, ConfigInPath = xxx, ConfigInFile...
        # For now we assume that parameter entries are on separate lines.
        Done      = False
        newSensor = False
        i         = 0
        msg       = ''

        while not Done :
            if i >= numLines - 1 :
                break

            line = lines[ i ]

            if '#' in line :
                # treat this line as a comment
                i = i + 1
                continue

            if '{' in line :
                newSensor = True

                # allow { on the same line as a parameter field
                line = line.split( '{' )[1]

                IP            = ''
                ConfigInPath  = ''
                ConfigInFile  = ''
                ConfigOutPath = ''
                ConfigOutFile = ''
                UMXStart      = ''

                while newSensor :
                    if '#' in line :
                        # treat this line as a comment
                        i = i + 1
                        if i >= numLines - 1 :
                            break
                        line = lines[ i ]
                        continue

                    if '}' in line :
                        # allow } on the same line as a parameter field
                        line = line.split( '}' )[0]
                        newSensor = False

                    if 'IP' in line :
                        words = line.split('=')
                        if len( words ) != 2 :
                            msg = msg + MonitorCommands.GetLocalUTC() + \
                                  ' ERROR: Malformed IP: ' + line + '\n'
                            break
                        IP = words[1].split()[0]

                    elif 'ConfigInPath' in line :
                        words = line.split('=')
                        if len( words ) != 2 :
                            msg = msg + MonitorCommands.GetLocalUTC() + \
                                  ' ERROR: Malformed ConfigInPath: ' + \
                                  line + '\n'
                            break
                        ConfigInPath = words[1].split()[0]

                    elif 'ConfigInFile' in line :
                        words = line.split('=')
                        if len( words ) != 2 :
                            msg = msg + MonitorCommands.GetLocalUTC() + \
                                  ' ERROR: Malformed ConfigInFile: ' + \
                                  line + '\n'
                            break
                        ConfigInFile = words[1].split()[0]

                    elif 'ConfigOutPath' in line :
                        words = line.split('=')
                        if len( words ) != 2 :
                            msg = msg + MonitorCommands.GetLocalUTC() + \
                                  ' ERROR: Malformed ConfigOutPath: ' + \
                                  line + '\n'
                            break
                        ConfigOutPath = words[1].split()[0]

                    elif 'ConfigOutFile' in line :
                        words = line.split('=')
                        if len( words ) != 2 :
                            msg = msg + ' ERROR: Malformed ConfigOutFile: ' + \
                                  line + '\n'
                            break
                        ConfigOutFile = words[1].split()[0]

                    elif 'UMXStart' in line :
                        words = line.split('=')
                        if len( words ) != 2 :
                            msg = msg + MonitorCommands.GetLocalUTC() + \
                                  ' ERROR: Malformed UMXStart: ' + \
                                  line + '\n'
                            break
                        UMXStart = words[1].split()[0]

                    if newSensor:
                        i = i + 1
                        if i >= numLines - 1 :
                            break
                        line = lines[ i ]

                # END: while newSensor :

                if not IP:
                    msg = msg + MonitorCommands.GetLocalUTC() + \
                          ' ERROR: Failed to parse IP\n'
                    continue
                if not ConfigInPath:
                    msg = msg + MonitorCommands.GetLocalUTC() + \
                          ' ERROR: Failed to parse ConfigInPath' + \
                          ' for sensor ' + IP + '\n'
                    continue
                if not ConfigInFile:
                    msg = msg + MonitorCommands.GetLocalUTC() + \
                          ' ERROR: Failed to parse ConfigInFile' + \
                          ' for sensor ' + IP + '\n'
                    continue
                if not ConfigOutPath:
                    msg = msg + MonitorCommands.GetLocalUTC() + \
                          ' ERROR: Failed to parse ConfigOutPath' + \
                          ' for sensor ' + IP + '\n'
                    continue
                if not ConfigOutFile:
                    msg = msg + MonitorCommands.GetLocalUTC() + \
                          ' ERROR: Failed to parse ConfigOutFile' + \
                          ' for sensor ' + IP  + '\n'
                    continue
                if not UMXStart :
                    msg = msg + MonitorCommands.GetLocalUTC() + \
                          ' ERROR: Failed to parse UMXStart ' + \
                          ' for sensor ' + IP  + '\n'
                    continue

                if not self.ValidIPAddress( IP ) :
                    msg = msg + MonitorCommands.GetLocalUTC() + \
                          ' ERROR: Malformed IP: ' + IP + ' from file: ' + \
                          self.sensorFile + '\n'
                    continue
                                
                sensorName = IP[ IP.rfind('.') + 1 : ]
                sensor = NCPASensor( monitor         = self.monitor,
                                     SN              = sensorName, 
                                     IP              = IP, 
                                     configInPath    = ConfigInPath,
                                     configInFile    = ConfigInFile,
                                     configOutPath   = ConfigOutPath,
                                     configOutFile   = ConfigOutFile,
                                     UMXSchedulerCmd = UMXStart )

                self.SensorDict[ sensorName ] = sensor

                i = i + 1

            # END: if '{' in line :

            else :
                i = i + 1
                
            if i >= numLines - 1 :
                Done = True

        # END: while not Done :

        # Report results
        msg = msg + MonitorCommands.GetLocalUTC() + \
              ' Read ' + str( numLines ) + ' lines from ' + \
              self.sensorFile + ' created ' + \
              str( len( self.SensorDict ) ) + ' sensors.'

        self.monitor.msgCommand.set( msg )

        if DEBUG:
            print( self.SensorDict.keys() )
            print( msg )

    #----------------------------------------------------- 
    def CreateSensorsFromCmd( self ):
        global DEBUG 
        DEBUG = self.monitor.args.verbose
        msg = ''

        # Get the IP's from the args.sensorList
        # This assumes the command line list is IP suffix only
        sensorNames = self.monitor.args.sensorList.split(',')

        if len( sensorNames ) < 1 :
            msg = msg + MonitorCommands.GetLocalUTC() + \
                  ' ERROR: CreateSensors() failed on input -s ' + \
                  self.monitor.args.sensorList + '\n'

        else :
            for sensorName in sensorNames :
                IPAddress = self.monitor.args.subnet + sensorName

                if not self.ValidIPAddress( IPAddress ) :
                    msg = msg + MonitorCommands.GetLocalUTC() + \
                          ' ERROR: Malformed IP from -s option: ' + \
                          IPAddress + '\n'
                    continue
                                
                sensor = NCPASensor( monitor         = self.monitor,
                                     SN              = sensorName, 
                                     IP              = IPAddress, 
                                     configInPath    = '~/',
                                     configInFile    = 'UMSX1.4.cfg',
                                     configOutPath   = '~/',
                                     configOutFile   = 'UMSX1.4.cfg',
                                     UMXSchedulerCmd = 'run_scheduler.sh')

                self.SensorDict[ sensorName ] = sensor
        
            # Report results
            msg = msg + MonitorCommands.GetLocalUTC() + \
                  ' Read ' + str( len( sensorNames ) ) + \
                  ' sensors from -s command line, created ' + \
                  str( len( self.SensorDict ) ) + ' sensors.'

        self.monitor.msgCommand.set( msg )

        if DEBUG:
            print( self.SensorDict.keys() )
            print( msg )
