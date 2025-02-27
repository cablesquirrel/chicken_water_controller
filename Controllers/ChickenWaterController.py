"""Chicken water controller"""
import machine
from machine import Pin
import time
from time import localtime
import mcron
from Helpers.DateHelpers import TimeToString
from Helpers.Logger import MultiLogger
from machine import WDT

class ChickenWaterChanger():
    PIN_START_BUTTON=15
    PIN_STOP_BUTTON=16
    PIN_ON_LED=19
    PIN_START_LED=17
    PIN_STOP_LED=18
    PIN_CASE_FAN=13
    PIN_FILL_VALVE=25
    PIN_DRAIN_VALVE_1=26
    PIN_DRAIN_VALVE_2=27
    STATE_IDLE=0
    STATE_DRAINING=1
    STATE_FLUSHING=2
    STATE_FILLING=3
    STATE_COMPLETE=4
    STATE_STOP=5
    BUTTON_STATE_PRESSED=0
    BUTTON_STATE_RELEASED=1

    def __init__(self):
        # Set up logger
        self._logger = MultiLogger(log_level=MultiLogger.LEVEL_DEBUG, syslog_server="172.16.102.6", app_name="Chicken_Water_changer")
        self._logger.log(MultiLogger.LEVEL_INFO, "ChickenWaterController.py: Controller initialization started")
        # Set up Watchdog Timer
        self._watchdog_timer = WDT(id=0, timeout=1000 * 60 * 10)
        # Set up button press vars
        self._stop_requested = False
        self._start_requested = False
        # Set Pin modes and default state
        self.ConfigurePins()
        self._program_state = ChickenWaterChanger.STATE_IDLE
        # Start the scheduler
        mcron.init_timer()
        # Heartbeat every minute
        mcron.insert(mcron.PERIOD_MINUTE, {0}, 'Heartbeat every minute', self.HeartBeat)
        # Change the chicken water every morning at 8AM (8 * 60 * 60 seconds after midnight)
        mcron.insert(mcron.PERIOD_DAY, {8 * 60 * 60}, 'Change water at 8AM', self.StartWaterChange)
     
    def Sleep(self, time_ms):
        total_time_slept = 0
        # Poll for input every 50ms
        while total_time_slept < time_ms:
            self.PollInput()
            # Emergency stop
            if self._stop_requested:
                return
            time.sleep_ms(50)
            total_time_slept += 50
            # if total_time_slept % 1000 == 0:
            #     print(total_time_slept // 1000)
            
    def ChangeState(self, new_state):
        self._logger.log(MultiLogger.LEVEL_INFO, f"ChickenWaterController.py: State change requested from {self._program_state} to {new_state}")
        # Move from any state to STOP
        if new_state == ChickenWaterChanger.STATE_STOP:
            self._logger.log(MultiLogger.LEVEL_INFO, "ChickenWaterController.py: ##### -- Begin Stopping State -- #####")
            self.TurnOffRunningLED()
            self.TurnOnStoppingLED()
            self._logger.log(MultiLogger.LEVEL_INFO, "ChickenWaterController.py: -> Closing drain valve")
            self.CloseDrainValve()
            self._logger.log(MultiLogger.LEVEL_INFO, "ChickenWaterController.py: -> Closing fill valve")
            self.CloseFillValve()
            self._logger.log(MultiLogger.LEVEL_INFO, "ChickenWaterController.py: -> Program stopped. Returning to IDLE")
            self.TurnOffStoppingLED()
            self._program_state = ChickenWaterChanger.STATE_IDLE     
        # Moving from IDLE to DRAINING
        elif self._program_state == ChickenWaterChanger.STATE_IDLE:
            if new_state == ChickenWaterChanger.STATE_DRAINING:
                self._program_state = ChickenWaterChanger.STATE_DRAINING
                self._logger.log(MultiLogger.LEVEL_INFO, "ChickenWaterController.py: ##### -- Begin Draining State -- #####")
                self.TurnOnRunningLED()
                self._logger.log(MultiLogger.LEVEL_INFO, "ChickenWaterController.py: -> Opening drain valve")
                self.OpenDrainValve()
                self._logger.log(MultiLogger.LEVEL_INFO, "ChickenWaterController.py: -> Waiting 1.5 minutes for pan to drain")
                self.Sleep(1000 * 90) # Allow to drain for 1.5 minutes (90 seconds)
                self._logger.log(MultiLogger.LEVEL_INFO, "ChickenWaterController.py: -> Draining completed")     
        # Moving from DRAINING to FLUSHING
        elif self._program_state == ChickenWaterChanger.STATE_DRAINING:
            if new_state == ChickenWaterChanger.STATE_FLUSHING:
                self._program_state = ChickenWaterChanger.STATE_FLUSHING
                self._logger.log(MultiLogger.LEVEL_INFO, "ChickenWaterController.py: ##### -- Begin Flushing State -- #####")
                self._logger.log(MultiLogger.LEVEL_INFO, "ChickenWaterController.py: -> Opening fill valve")
                self.OpenFillValve()
                self._logger.log(MultiLogger.LEVEL_INFO, "ChickenWaterController.py: -> Flushing with water for 15 seconds")
                self.Sleep(1000 * 15)
                self._logger.log(MultiLogger.LEVEL_INFO, "ChickenWaterController.py: -> Closing fill valve")
                self.CloseFillValve()
                self._logger.log(MultiLogger.LEVEL_INFO, "ChickenWaterController.py: -> Waiting 30 seconds for pan to drain")
                self.Sleep(1000 * 30)
                self._logger.log(MultiLogger.LEVEL_INFO, "ChickenWaterController.py: -> Closing drain valve")
                self.CloseDrainValve()
                self._logger.log(MultiLogger.LEVEL_INFO, "ChickenWaterController.py: -> Flushing completed")
        # Moving from FLUSHING to FILLING
        elif self._program_state == ChickenWaterChanger.STATE_FLUSHING:
            if new_state == ChickenWaterChanger.STATE_FILLING:
                self._program_state = ChickenWaterChanger.STATE_FILLING
                self._logger.log(MultiLogger.LEVEL_INFO, "ChickenWaterController.py: ##### -- Begin Filling State -- #####")
                self._logger.log(MultiLogger.LEVEL_INFO, "ChickenWaterController.py: -> Opening fill valve")
                self.OpenFillValve()
                self._logger.log(MultiLogger.LEVEL_INFO, "ChickenWaterController.py: -> Fill with water for 50 seconds")
                self.Sleep(1000 * 50)
                self._logger.log(MultiLogger.LEVEL_INFO, "ChickenWaterController.py: -> Closing fill valve")
                self.CloseFillValve()
                self._logger.log(MultiLogger.LEVEL_INFO, "ChickenWaterController.py: -> Filling completed")
        # Moving from FILLING to COMPLETED
        elif self._program_state == ChickenWaterChanger.STATE_FILLING:
            if new_state == ChickenWaterChanger.STATE_COMPLETE:
                self._program_state = ChickenWaterChanger.STATE_IDLE
                self._logger.log(MultiLogger.LEVEL_INFO, "ChickenWaterController.py: ##### -- Program Complete -- #####")
                self.TurnOffRunningLED()

    def ConfigurePins(self):
        self._logger.log(MultiLogger.LEVEL_INFO, "ChickenWaterController.py: Configuring GPIO pins")
        self._pin_start_button = Pin(ChickenWaterChanger.PIN_START_BUTTON, mode=Pin.IN, pull=Pin.PULL_UP)
        self._start_button_state = ChickenWaterChanger.BUTTON_STATE_RELEASED
        self._start_button_waiting_for_debounce = False
        self._pin_stop_button = Pin(ChickenWaterChanger.PIN_STOP_BUTTON, mode=Pin.IN, pull=Pin.PULL_UP)
        self._stop_button_state = ChickenWaterChanger.BUTTON_STATE_RELEASED
        self._stop_button_waiting_for_debounce = False
        self._pin_on_led = Pin(ChickenWaterChanger.PIN_ON_LED, mode=Pin.OUT, value=1)
        self._pin_start_led = Pin(ChickenWaterChanger.PIN_START_LED, mode=Pin.OUT, value=0)
        self._pin_stop_led = Pin(ChickenWaterChanger.PIN_STOP_LED, mode=Pin.OUT, value=0)
        self._pin_case_fan = Pin(ChickenWaterChanger.PIN_CASE_FAN, mode=Pin.OUT, value=1)
        self._pin_fill_valve = Pin(ChickenWaterChanger.PIN_FILL_VALVE, mode=Pin.OUT, value=1)
        self._pin_drain_valve_1 = Pin(ChickenWaterChanger.PIN_DRAIN_VALVE_1, mode=Pin.OUT, value=1)
        self._pin_drain_valve_2 = Pin(ChickenWaterChanger.PIN_DRAIN_VALVE_2, mode=Pin.OUT, value=1)

    def PollInput(self):
        # Check if start button is depressed
        # Configuration is PULL_UP with a Normally Open switch
        # Pressed Value: 0
        # Released Value: 1
        # If the button is pressed, and we're not waiting on a previous debounce timeout
        if self._pin_start_button.value() == 0 and self._start_button_waiting_for_debounce == False:
            # Mark the button as pressed, waiting on a release and debounce
            self._start_button_waiting_for_debounce = True
        # If the button is released, and we're waiting for a debounce timeout
        elif self._pin_start_button.value() == 1 and self._start_button_waiting_for_debounce == True:
            # Wait 50ms and check again
            time.sleep_ms(50)
            # Still released, so we consider this a press
            if self._pin_start_button.value() == 1:
                self._start_button_waiting_for_debounce = False
                # Handle button press actions
                self._logger.log(MultiLogger.LEVEL_WARN, "ChickenWaterController.py: !!!! START BUTTON PRESSED !!!")
                if self._program_state == ChickenWaterChanger.STATE_IDLE:
                    # Set the current state to the next state (Whatever that may be)
                    self.ChangeState(self._program_state + 1)
                    
        # Check if stop button is depressed
        # Configuration is PULL_UP with a Normally Closed switch
        # Pressed Value: 1
        # Released Value: 0
        if self._pin_stop_button.value() == 1 and self._stop_button_waiting_for_debounce == False:
            # Mark the button as pressed, waiting on a release and debounce
            self._stop_button_waiting_for_debounce = True
        # If the button is released, and we're waiting for a debounce timeout
        elif self._pin_stop_button.value() == 0 and self._stop_button_waiting_for_debounce == True:
            # Wait 50ms and check again
            time.sleep_ms(50)
            # Still released, so we consider this a press
            if self._pin_stop_button.value() == 0:
                self._stop_button_waiting_for_debounce = False
                # Handle button press actions
                self._logger.log(MultiLogger.LEVEL_WARN, "ChickenWaterController.py: !!!! STOP BUTTON PRESSED !!!")
                self._stop_requested = True

        
    def BeginProgramLoop(self):
        while True:
            # Handle emergency stop
            if self._stop_requested:
                self._stop_requested = False
                self.ChangeState(ChickenWaterChanger.STATE_STOP)
                
            # Feed the watchdog timer
            # NOTE: Any states that take 10 minutes or longer to run
            #       are responsible for feeding the watchdog timer.
            self._watchdog_timer.feed()
            
            # Allow any system processes to run
            time.sleep_ms(10)
            
            # Poll button input
            self.PollInput()
            
            # Check if we need to move to the next state
            if self._program_state != ChickenWaterChanger.STATE_IDLE:
                self.ChangeState(self._program_state + 1)
                
            # Check if the scheduler requested a start
            if self._start_requested:
                self._start_requested = False
                self.ChangeState(self._program_state + 1)
        
    def TurnOnRunningLED(self):
        # Handle emergency stop
        if self._stop_requested:
            return
        self._pin_start_led.value(1)
        
    def TurnOffRunningLED(self):
        # Handle emergency stop
        if self._stop_requested:
            return
        self._pin_start_led.value(0)
        
    def TurnOnStoppingLED(self):
        # Handle emergency stop
        if self._stop_requested:
            return
        self._pin_stop_led.value(1)
        
    def TurnOffStoppingLED(self):
        # Handle emergency stop
        if self._stop_requested:
            return
        self._pin_stop_led.value(0)

    def OpenDrainValve(self):
        # Handle emergency stop
        if self._stop_requested:
            return
        # Command the valve to start opening
        self._pin_drain_valve_1.value(1)
        self._pin_drain_valve_2.value(0)
        # Wait for the opening to finish
        self.Sleep(1000 * 10)
        # Set the relays back to default state
        self._pin_drain_valve_1.value(1)
        self._pin_drain_valve_2.value(1)
        
    def CloseDrainValve(self):
        # Handle emergency stop
        if self._stop_requested:
            return
        # Command the valve to close
        self._pin_drain_valve_1.value(0)
        self._pin_drain_valve_2.value(1)
        # Wait for the closing to finish
        self.Sleep(1000 * 10)
        # Set the relays back to default state
        self._pin_drain_valve_1.value(1)
        self._pin_drain_valve_2.value(1)
        
    def OpenFillValve(self):
        # Handle emergency stop
        if self._stop_requested:
            return
        # Command the valve to open
        self._pin_fill_valve.value(0)
        
    def CloseFillValve(self):
        # Handle emergency stop
        if self._stop_requested:
            return
        # Command the valve to close
        self._pin_fill_valve.value(1)
        
    def HeartBeat(self, callback_id, current_time, callback_memory):
        self._logger.log(MultiLogger.LEVEL_INFO, f"ChickenWaterController.py: Scheduler is running - Current Time: {TimeToString(localtime(current_time))}")
        
    def StartWaterChange(self, callback_id, current_time, callback_memory):
        self._logger.log(MultiLogger.LEVEL_INFO, f"ChickenWaterController.py: Scheduler requested the water change job to start - Current Time: {TimeToString(localtime(current_time))}")
        self._start_requested = True
