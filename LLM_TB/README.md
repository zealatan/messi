Demo - Zynq UltraScale+ Power Tool

----- Installer

Build ZynqusPowerTool Release
copyassets.bat
deploy.bat
copy c:\ZynqusPowerToolDeployment

----- Parts List

PC with ZynqusPowerTool
ZCU102 board or
 ZCU1751 (or other) modified with Bus Pirate USB to I2C board
 Mini-USB cable
Board Power Supply
1920x1080 display
DisplayPort cable

App PC:
PC with Terminal scripts
SD Card
USB Hub
2 uUSB Cables
Ethernet Cable

----- Modify ZCU1751 with Bus Pirate

ZCU1751                                 Bus Pirate IO Connector
SCL R617 Far Side - Silkscreen Left  -> Bus Pirate CLK
SDA R616 Near Side - Silkscreen Left -> Bus Pirate MOSI
GND J128                             -> Bus Pirate GND

----- Setup Deprecated

copy c:\ZynqusPowerToolDeployment
Start > <Right Click> Computer > Properties > Device Manager > Ports
Note the COM ports.
Connect Bus Pirate via USB.
Note the additional COM port, this is for the Bus Pirate.
edit c:\ZynqusPowerToolDeployment\config.ini and change the BusPiratePort number.
The default ScreenSize (540 or 1080) can be changed if desired.
Create a shortcut to c:\ZynqusPowerToolDeployment\ZynqusPowerTool.exe

----- Setup

For ZCU102...
Connect Micro-USB between J83 and the PC USB.

copy c:\ZynqUS_Demos\ZynqusPowerToolDeployment
edit c:\ZynqUS_Demos\ZynqusPowerToolDeployment\config.ini and 
the default ScreenSize (540 or 1080), and other settings can be changed if desired.
Create a shortcut to c:\ZynqUS_Demos\ZynqusPowerToolDeployment\ZynqusPowerTool.exe

----- Run

Launch ZynqusPowerTool.exe
In a few seconds, a report of the Voltage/Current/Power for all the metered rails is shown.
Note the total powers for FPD/LPD/PLD/Total are also shown.
Launch insomnia.exe to keep awake

Various apps and bitfiles can be side-loaded and run, while noting the change in power.
It is always good to refer to the official "power model" software to predict power consumption.

The app can be resized by clicking the upper left corner.
The app can be closed by clicking the upper right corner.
The app can be hidden by <Alt-Esc> and brought back from the system tray.

Code version can be checked by Select > About

The block diagram and other controls are not yet implemented.

----- Various Apps

Putty sessions should be set to Telnet 192.168.1.112 Port 23
and saved under 2048, cmatrix, mbrot, nInvaders, top

----- Deployment Checklist

Backup Z:\Work\ZynqUS_Demos []

MSP430 touch api.c and rebuild []
Z:\Work\ZynqUS_Demos\tools\ReadMSP430.bat []
Update Z:\Work\ZynqUS_Demos\tools\FlashMSP430.bat []
Delete old _MSP430.txt file []

Qt Build Release (switch back to Debug) []
C:\ZynqusPowerTool\ZynqusPowerTool\copyassets.bat []
C:\ZynqusPowerTool\ZynqusPowerTool\deploy.bat []
Replace Z:\Work\ZynqUS_Demos\ZynqusPowerToolDeployment []

Deployment groupmktgdemo ZynqUS_Demos []
 Back up ZynqUS_Demos_<Date> []
 ZynqusPowerToolDeployment []
 <Date>_ZCU102_MSP430.txt []
 FlashMSP430.bat []
 SD - <Version> []
 deploy.bat SD - <Version> []
 Scripts []
 Documentation []

----- Regression Test

Regression Test []
 Hardware boots and works with known good Scripts []
 Follow documentation []
 Test Scripts work []
 Test Power Advantage Tool works (see below) []
 Test Shortcuts work []
 Make new SD Card and test it works []
 Flash MSP430 and test it works []

-- Power Advantage Tool Regression

Zoom
Personalize Display 100%/125%/150%
Rails/Plot/SystemMonitor/Legend/About - Versions
PLD/FPD/LPD Switching (check rail lights on ZCU102)
Preset Off/Minimum/Performance
PL Loading/Clock/Options/0.72V/Info
Domains
Islands

-- Upender SD Regression

(0) On boot, terminal should show message "IntervalTimerInit"
(1) Launch ZynqusPowerTool.exe - Shortcut > Click A53/3 > terminal should show message "@ps apu3 0" and "XPm_ForcePowerDown..."
(2) Launch ZynqusPowerTool.exe - Shortcut > Programmable Logic Domain Tachometer 100% -> 25% > terminal should show message "@ps pl options 0x0000301 0x0000100" and "GPIO PL read back:0x301 0x23000100"
(3) Close ZynqusPowerTool.exe and open Serial Tera Term to USB to UART Bridge: Interface 3 115200 Baud > @ps sysmon 0 > terminal should show message "!ps sysmon 0 27471" indicating a temperature of 27.471 degrees (or other reasonable temperature).

-- PL Options and Control Full Regression

3630 Default
2622 50% Utilization
2142 25%
1612 0%
3630
2213 50%
1518 25%
834 0%
3630mW 25%/25% <-- Ask Brian why
2921mW 100%/0% RW
3849mW 0%/100%
3893mW 50%/50%

----- Design Manual Steps

- UART1: BSP system.mss > Modify this BSP's Settings > standalone > stdin/stdout psu_uart_1 > OK
- xilpm: BSP system.mss > Modify this BSP's Settings > Check xilpm > Regenerate BSP sources
- Manually import ttcps_v3_1 folder to libsrc
- Copy XPAR_XTTCPS_0_DEVICE_ID (two sections) into xparameters.h
- Change the C:\zcu102_r5_dual_gpio\hw_platform\sw_workspace\gpio_demo_r5_bsp\psu_cortexr5_0\libsrc\xilpm_v2_0\src\Makefile from libxilpm to libxil
- Build clean 

----- Accolades

From: Glenn Steiner 
Sent: Monday, July 11, 2016 5:52 PM
To: Asad Riaz
Cc: Jerry Wong
Subject: FW: TSC survey so far

Hi Asad,

Our ZU+ Power Management Session received the highest ratings of all of the  General  sessions with an overall average of 4.57.
I held up my end of the deal on the Security & Protection Presentation with above average scores of 4.59 and 4.11 in Tokyo & Shanghai respectively.

Regards,

Glenn Steiner
Xilinx
408 626-6288
glenn.steiner@xilinx.com

(Best of 16 "General" vs "System Level Selling" TSC "Technical Sales Conference" events/sessions)
(Highest set of ratings ever - Tim)

===== Gotchas

----- The power report displays all 0's, Setup displays a small blank popup

This is the behavior if communication is lost to the INA226 Voltage/Current/Power
measurement modules.

- Make sure USB is cabled from the PC to the Bus Pirate. The Bus Pirate lights should be on.
- If running from MSP430, make sure there is no Bus Pirate attached to I2C.
- Recheck the COM port number as described in setup. Changing boards or PC's typically changes the COM port number.
- Recheck the .config file selects the correct target board.
- Perhaps the board was power cycled, which clears the calibrations in the INA226 chips. Relaunching the app sends the calibrations again.
- Make sure that there is not another instance of the program occupying the COM port.
- Verify there are three blue rework wires coming from the Bus Pirate to the ZCU1751. If one has broken, it may be repaired as described under "Modify ZCU1751 with Bus Pirate".

----- The power report display is blank, Setup displays a small blank popup

This is the behavior if communication is made to COM interface 3, but not to the INA226's.

- Make sure the MSP430 is running (blinking DS47). Press SW7 to reset MSP430.
- Make sure SW8 switches are set to binary 10000.
- Perhaps the MSP430 is not programmed.
- Perhaps the MSP430 is not working properly (this is the case for ZCU102 A027).

----- This application has requested the Runtime to terminate it in an unusual way

This can happen if the MSP430 is unavilable.
Make sure the MSP430 is running as suggested above. 

----- This application has requested the Runtime to terminate it in an unusual way

http://forum.qt.io/topic/23114/solved-qt-5-0-0-built-with-vs2012-app-exe-doesn-t-run-when-outside-qt-creator

You may be developing.
You may be missing a .dll in your deployment
Run C:\ZynqusPowerTool\ZynqusPowerTool\copyassets.bat
