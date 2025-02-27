"""Program entry point"""
from Controllers.ChickenWaterController import ChickenWaterChanger
from Helpers.Logger import MultiLogger


def main():
    myLogger = MultiLogger(log_level=MultiLogger.LEVEL_DEBUG, syslog_server="SYSLOG_IP_ADDRESS", app_name="Chicken_Water_changer")
    myLogger.log(MultiLogger.LEVEL_INFO, "main.py: Initializing Controller")
    controller = ChickenWaterChanger()
    myLogger.log(MultiLogger.LEVEL_INFO, "main.py: Starting program loop")
    controller.BeginProgramLoop()

  
if __name__=="__main__":
    main()
else:
    print(__name__)