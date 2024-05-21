#!/usr/bin/env python
import logging
import configparser
import os
from DeyeAtComm import DeyeAtComm

from functools import reduce


def main():
    logging.basicConfig(format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        level=logging.INFO,
                        handlers=[
                            logging.FileHandler(
                                "%s/current.log" % (os.path.dirname(os.path.realpath(__file__)))),
                            logging.StreamHandler()
                        ])

    data = _getDeyeData()

    logging.info("data from deye:")
    logging.info(data)


def _getDeyeData():
    config = _getConfig()
    address = config['DEFAULT']['Address']
    port = int(config['DEFAULT']['Port'])

    modbus = DeyeAtComm(address,port)
    serial = modbus.serial

    try:
        #_checkResetDailyProduction(modbus)
        
        acEnergyForward = _getDailyProduction(modbus)
        acPower = _getTotalACOutputPower(modbus)
        acCurrent = _getGridCurrent(modbus)
        acVoltage = _getAcVoltage(modbus)
        firmwareVersion = _getFirmwareVersion(modbus)
        return {
            "acEnergyForward": acEnergyForward,
            "acPower": acPower,
            "acCurrent": acCurrent,
            "acVoltage": acVoltage,
            "_firmwareVersion": firmwareVersion,
        }
    except Exception as e:
        logging.critical('Error at %s', '_update', exc_info=e)
 
def _getDailyProduction(modbus):
    # - name: "Daily Production"
    #   class: "energy"
    #   state_class: "total"
    #   uom: "kWh"
    #   scale: 0.1
    #   rule: 1
    #   registers: [0x003C]
    #   icon: 'mdi:solar-power'
    result = modbus.read(0x3c,1)
    return result[0]*0.1


def _getAcVoltage(modbus):
    #  - name: "AC Voltage"
    #   class: "voltage"
    #   state_class: "measurement"
    #   uom: "V"
    #   scale: 0.1
    #   rule: 1
    #   registers: [0x0049]
    #   icon: 'mdi:transmission-tower'
    result = modbus.read(0x49,1)
    return result[0]*0.1


def _getGridCurrent(modbus):
    # - name: "Grid Current"
    #   class: "current"
    #   state_class: "measurement"
    #   uom: "A"
    #   scale: 0.1
    #   rule: 2
    #   registers: [0x004C]
    #   icon: 'mdi:home-lightning-bolt'
    result = modbus.read(0x4C,1)
    return result[0]*0.1


def _getTotalACOutputPower(modbus):
    #  - name: "Total AC Output Power (Active)"
    #   class: "power"
    #   state_class: "measurement"
    #   uom: "W"
    #   scale: 0.1
    #   rule: 3
    #   registers: [0x0056, 0x0057]
    #   icon: 'mdi:home-lightning-bolt'
    values = modbus.read(
        register_addr=0x0056, count=2)
    byteValues = list(map(lambda v: v.to_bytes(2, 'big'), values))
    byteValues.reverse()
    bytes = reduce(lambda a, b: a + b, byteValues)
    intValue = int.from_bytes(bytes, 'big')
    value = float(intValue) * 0.1
    return value

def _getFirmwareVersion(modbus):
    if modbus:
        firmwareVersion = modbus.getversion()
        return firmwareVersion
    else :
        return '?'

def _getConfig():
    config = configparser.ConfigParser()
    config.read("%s/config.ini" %
                (os.path.dirname(os.path.realpath(__file__))))
    return config


if __name__ == "__main__":
    main()
