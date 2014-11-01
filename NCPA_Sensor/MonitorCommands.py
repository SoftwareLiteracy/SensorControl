import subprocess
import time

DEBUG = False

#---------------------------------------------------------------
def GetLocalUTC() :
    t = time.strftime( '%b %d %Y %H:%M:%S', ( time.gmtime(time.time()) ) )
    return str( t )

#---------------------------------------------------------------
def SendConfigCmd( sensor ) :

    cmdLine = 'scp -o "ConnectTimeout 3" ' + \
              sensor.configInPath + sensor.configInFile + \
              ' root@' + sensor.IP + ':' + \
              sensor.configOutPath + sensor.configOutFile

    sp = subprocess.Popen( cmdLine, shell = True, 
                           stdout = subprocess.PIPE )
    return sp

#---------------------------------------------------------------
def StartUMXSchedulerCmd( sensor ):

    cmdLine = 'ssh -o "ConnectTimeout 3" root@' + sensor.IP + \
              ' ./' + sensor.UMXSchedulerCmd

    if DEBUG:
        print( 'StartUMXSchedulerCmd(): ' + cmdLine ) 

    sp = subprocess.Popen( cmdLine, shell = True, 
                           stdout = subprocess.PIPE )
    return sp

#---------------------------------------------------------------
def StartUMXControlCmd( sensor ):

    cmdLine = 'ssh -o "ConnectTimeout 3" root@' + sensor.IP + \
              ' ./UMXcontrol4.4.0 &'

    sp = subprocess.Popen( cmdLine, shell = True, 
                           stdout = subprocess.PIPE )
    return sp

#---------------------------------------------------------------
def KillUMXCmd( sensor ):

    # Get pid of UMXscheduler4
    cmdLine = 'ssh -o "ConnectTimeout 3" root@' + sensor.IP + \
              ' ps -e | grep UMXscheduler4'

    sp = subprocess.Popen( cmdLine, shell = True, 
                           stdout = subprocess.PIPE )
    return sp

#---------------------------------------------------------------
def KillUMXSubCmd( sensor ):

    # kill the umxSchedPID
    cmdLine = 'ssh -o "ConnectTimeout 3" root@' + sensor.IP + \
              ' kill -9 ' + sensor.umxSchedPID

    sp = subprocess.Popen( cmdLine, shell = True, 
                           stdout = subprocess.PIPE )
    return sp

#---------------------------------------------------------------
def KillUMXSubCmd2( sensor ):

    # Get pid of UMXcontrol4.4.0
    cmdLine = 'ssh -o "ConnectTimeout 3" root@' + sensor.IP + \
              ' ps -e | grep UMXcontrol4.4.0'

    sp = subprocess.Popen( cmdLine, shell = True, 
                           stdout = subprocess.PIPE )
    return sp

#---------------------------------------------------------------
def KillUMXSubCmd3( sensor ):

    # kill the UMXcontrol4.4.0
    cmdLine = 'ssh -o "ConnectTimeout 3" root@' + sensor.IP + \
              ' kill -9 ' + sensor.umxControlPID

    sp = subprocess.Popen( cmdLine, shell = True, 
                           stdout = subprocess.PIPE )
    return sp

#---------------------------------------------------------------
def HaltCmd( sensor ):

    cmdLine = 'ssh -o "ConnectTimeout 3" root@' + sensor.IP + ' halt'

    sp = subprocess.Popen( cmdLine, shell = True, 
                           stdout = subprocess.PIPE )
    return sp

#---------------------------------------------------------------
def RebootCmd( sensor ):

    cmdLine = 'ssh -o "ConnectTimeout 3" root@' + sensor.IP + ' reboot'

    sp = subprocess.Popen( cmdLine, shell = True, 
                           stdout = subprocess.PIPE )
    return sp

#---------------------------------------------------------------
def TimeCmd( sensor ):

    cmdLine = 'ssh -o "ConnectTimeout 3" root@' + \
               sensor.IP + ' date'
    sp = subprocess.Popen( cmdLine, shell = True, 
                           stdout = subprocess.PIPE )
    return sp

#---------------------------------------------------------------
def PingCmd( sensor ):

    cmdLine = 'ping -q -c 1 -W 1 ' + sensor.IP
    sp = subprocess.Popen( cmdLine, shell = True, 
                           stdout = subprocess.PIPE )
    return sp

#---------------------------------------------------------------
def DataFileCmd( sensor ) :

    # The file name is:
    # /data/ncpa42-1XXX_YYMMDD/ncpa42-1XXX_YYMMDD_HHMMSS.umx
    # Get the latest directory in /data
    cmdLine = 'ssh -o "ConnectTimeout 3" root@' + \
              sensor.IP + ' ls -t /data'
    sp = subprocess.Popen( cmdLine, shell = True, 
                           stdout = subprocess.PIPE )
    return sp

#---------------------------------------------------------------
def DataFileSubCmd( sensor ) :
    # Called from PollDataCmd() if DataFileCmd() succeeded

    # Now get the list of files in this dir
    # return the full line file info from ls -lt
    cmdLine = 'ssh -o "ConnectTimeout 3" root@' + \
              sensor.IP + ' ls -lt /data/' + sensor.firstDataDir
    
    sp = subprocess.Popen( cmdLine, shell = True, 
                           stdout = subprocess.PIPE )
    return sp

#---------------------------------------------------------------
def LogFileCmd( sensor ):

    # The file name is /log/ncpa42-1XXX_YYMMDD.txt
    cmdLine = 'ssh -o "ConnectTimeout 3" root@' + \
              sensor.IP + ' ls -t /log'
    sp = subprocess.Popen( cmdLine, shell = True, 
                           stdout = subprocess.PIPE )
    return sp

#---------------------------------------------------------------
def LogFileSubCmd( sensor ):
    # Called from PollLogCmd() if LogFileCmd() succeeded

    # now get the last 2 lines of the most recent log file
    # use stdout = subprocess.PIPE to return result into a tuple, 
    # this will just return the command value
    cmdLine = 'ssh -o "ConnectTimeout 3" root@' + sensor.IP + \
              ' tail -n 2 ' + '/log/' + sensor.firstLogFile

    sp = subprocess.Popen( cmdLine, shell = True, 
                           stdout = subprocess.PIPE )
    return sp

#---------------------------------------------------------------
# Verify that the UMXcontrol4.4.0 is running
# ssh exits with the exit status of the remote command
# or with 255 if an error occurred.
#---------------------------------------------------------------
def UMXCmd( sensor ):

    cmdLine = 'ssh -o "ConnectTimeout 3" root@' + sensor.IP + \
              ' ps -e | grep UMXcontrol4.4.0'

    sp = subprocess.Popen( cmdLine, shell = True, 
                           stdout = subprocess.PIPE )
    return sp

#---------------------------------------------------------------
def PlotCmd( sensor ):

    dataFile = '/data/' + sensor.firstDataDir + '/' + sensor.firstDataFile

    tempDir      = sensor.monitor.tempDir
    tempUMXFile  = tempDir + sensor.name + '_temp.umx'
    tempDataFile = tempUMXFile.replace('.umx', '.dat')
    gnuplotFile  = tempDir + sensor.name + '_gnuplot.plt'

    # Copy the .umx to a local temporary file
    cmdLine = 'scp -o "ConnectTimeout 3" root@' + \
              sensor.IP + ':' + dataFile + ' ' + tempUMXFile

    sp = subprocess.Popen( cmdLine, shell = True, 
                           stdout = subprocess.PIPE )

    # communicate() returns a tuple, sets returncode
    sp_out = sp.communicate() 

    if sp.returncode != 0 :
        msg = GetLocalUTC() + ' ' + sensor.name + ': scp ' + dataFile + \
              ' Failed: ' + sp_out[0].decode("utf-8") + '\n'
        sensor.plotStatusMsg = msg
        sensor.monitor.msgCommand.set( msg )
        return

    # Convert the .umx into ASCII in a temporary file
    cmdLine = 'umxcat4 ' + tempUMXFile + ' > ' + tempDataFile

    sp = subprocess.Popen( cmdLine, shell = True, 
                           stdout = subprocess.PIPE )

    sp_out = sp.communicate() 

    if sp.returncode != 0 :
        msg = GetLocalUTC() +  ' ' + sensor.name + ': umxcat4 ' + dataFile + \
              'Failed: ' + sp_out[0].decode("utf-8") + '\n'
        sensor.plotStatusMsg = msg
        sensor.monitor.msgCommand.set( msg )
        return

    # Create the gnuplot.plt file
    cmdLine = '''echo 'plot "''' + tempDataFile + '" using 1:2 with ' + \
              '''lines' > ''' + gnuplotFile

    sp = subprocess.Popen( cmdLine, shell = True, 
                           stdout = subprocess.PIPE )

    sp_out = sp.communicate() 

    if sp.returncode != 0 :
        msg = GetLocalUTC() + ' ' + sensor.name + \
              ': Creating gnuplot.plt Failed: ' + \
              sp_out[0].decode("utf-8") + '\n'
        sensor.plotStatusMsg = msg
        sensor.monitor.msgCommand.set( msg )
        return

    # Subprocess gnuplot to plot the data
    cmdLine = 'gnuplot ' + gnuplotFile + ' -persist'

    sp = subprocess.Popen( cmdLine, shell = True, 
                           stdout = subprocess.PIPE )

    msg = GetLocalUTC() + ' ' + sensor.name + \
              ': Plotting ' + tempUMXFile + '\n'
    sensor.monitor.msgCommand.set( msg )
