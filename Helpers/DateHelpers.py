"""Date/Time helper functions"""
from time import localtime, mktime, time

def UTCToET():
    """Convert current system time(UTC) to Eastern Time
       
       https://forum.micropython.org/viewtopic.php?t=3675#p29856
    """
    year = localtime()[0] #get current year
    HHMarch = mktime((year,3 ,(14-(int(5*year/4+1))%7),1,0,0,0,0,0)) #Time of March change to DST
    HHNovember = mktime((year,10,(7-(int(5*year/4+1))%7),1,0,0,0,0,0)) #Time of November change to EST
    now=time()
    if now < HHMarch : # we are before last sunday of march
        dst=localtime(now-18000) # EST: UTC-5H
    elif now < HHNovember : # we are before last sunday of october
        dst=localtime(now-14400) # DST: UTC-4H
    else: # we are after last sunday of october
        dst=localtime(now-18000) # EST: UTC-5H
    return(dst)

def TimeToString(local_time):
    # Output: 'DoW, MM/DD/YY HH:MM:SS'
    # Time.localtime format: (YYYY, MM, DD, HH, MM, SS, Day of week [Monday=0], Day of year)
    output_time = ""
    if local_time[6] == 0:
        output_time = "Monday, "
    elif local_time[6] == 1:
        output_time = "Tuesday, "
    elif local_time[6] == 2:
        output_time = "Wednesday, "
    elif local_time[6] == 3:
        output_time = "Thursday, "
    elif local_time[6] == 4:
        output_time = "Friday, "
    elif local_time[6] == 5:
        output_time = "Saturday, "
    else:
        output_time = "Sunday, "

    output_time += f"{local_time[2]}/{local_time[1]:02d}/{local_time[0]:02d} {local_time[3]:02d}:{local_time[4]:02d}:{local_time[5]:02d}"
    return output_time
