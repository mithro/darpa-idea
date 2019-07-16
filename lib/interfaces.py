#!/usr/bin/env python3

# PCBBundle is a Python DataClass
# https://docs.python.org/3/library/dataclasses.html

def N(t: Type, n: int):
    """FIXME: Make Type[4] == Tuple[Type, Type, Type, Type]"""
    return eval("Tuple["+(t.__name__+", ")*n-1+t.__name__+"]")

class Power(PCBBundle):
  pos: Pin
  neg: Pin

class IVSense(PCBBundle):
  v_in: Pin
  v_out: Pin

class shunt(PCBBundle):
  i_in: Pin
  i_out: Pin

class UART(PCBBundle):
  rx: Pin
  tx: Pin

class FullDuplexUART(PCBBundle):
  rx: Pin
  tx: Pin

class FullDuplexUARTWithEnable(PCBBundle):
  rx: Pin
  tx: Pin
  en: Pin

class pci_lane(PCBBundle):
  tx: DiffPair
  rx: DiffPair

# Parallel style serdes, which has a data and clock pair which much be length matched
class serdes_par(PCBBundle):
  clk: DiffPair
  data: DiffPair

# these are indeed called "A" and "B" or "D_" and "D+" as a secondary option
# https://en.wikipedia.org/wiki/RS_485
class rs485(PCBBundle):
  d_: Pin
  dp: Pin

#pcb_capability rs485:rs485

class can(PCBBundle):
  rx: Pin
  tx: Pin

class i2c(PCBBundle):
  sda: Pin
  scl: Pin

#val spi_bundles: HashTable<Symbol, Seqable>()
def generate_spi_bundles():
  prefix = "spi_"
  m_or_s = ["master_", "slave"]
  dir    = ["bi"     , "in"   , "out"]
  common_pins: ["ss", "sck"]
  spi_bundles["spi_master"]    = common_pins + ["mosi", "miso"]
  spi_bundles["spi_master_in"] = common_pins + ["miso"]
  spi_bundles["spi_master_out"]= common_pins + ["mosi"]
  spi_bundles["spi_slave"]     = common_pins + ["mosi", "miso"]
  spi_bundles["spi_slave_in"]  = common_pins + ["mosi"]
  spi_bundles["spi_slave_out"] = common_pins + ["miso"]
  for k, v in spi_bundles.items():
    s = """\
class {}(PCBBundle):
"""
    for pname in v:
      s += """\
  {}: Pin
"""
    exec(s)
generate_spi_bundles()

class SPI(PCBBundle):
  mosi: Pin
  miso: Pin
  sck:  Pin
  ss:   Pin

class USB_2(PCBBundle):
  dat_p: Pin
  dat_n: Pin

class SWD(PCBBundle):
  swdio: Pin
  swclk: Pin
  reset: Pin
  swo:   Pin

class DiffPair(PCBBundle):
  D_P: Pin
  D_N: Pin

class edp(PCBBundle):
  Power_3v3: Power
  Power_19v0: Power
  aux_ch0: DiffPair
  d0: DiffPair
  d1: DiffPair
  hpd0: Pin
  lcd_bl_en: Pin
  lcd_bl_pwm: Pin

class sd(PCBBundle):
  dat: N(Pin, 4)
  clk : Pin
  cmd: Pin

class jtag(PCBBundle):
  tck: Pin
  tdi: Pin
  tdo: Pin
  tms: Pin
  trstn: Pin

class jtag_no_rst(PCBBundle):
  tck: Pin
  tdi: Pin
  tdo: Pin
  tms: Pin

class LVDS(PCBBundle):
  n: Pin
  p: Pin

# clock_capable LVDS.  Signal_wise it's the same as LVDS
class LVDS_clk(PCBBundle):
  n: Pin
  p: Pin

class pcie_lane(PCBBundle):
  rx: LVDS
  tx: LVDS

class rgmii(PCBBundle):
  txd: N(Pin, 4)
  rxd: N(Pin, 4)
  tx_clk: Pin
  tx_ctrl: Pin
  rx_clk: Pin
  rx_ctrl: Pin

class trd(PCBBundle):
  trd: DiffPair
  common: Pin

class ethernet_1000(PCBBundle):
  mdi: N(DiffPair, 4)

#pcb_capability ethernet_1000: ethernet_1000
#pcb_capability rgmii: rgmii
#pcb_capability LVDS: LVDS

#==== Capabilities =============================================================

#public val CAPABILITY_TABLE: HashTable<Symbol, Symbol>()

#CAPABILITY_TABLE = Dict[str, PCBBundle]

CAPABILITY_TABLE["Power_3v0_source"] = Power
CAPABILITY_TABLE["Power_3v0"] = Power
CAPABILITY_TABLE["Power_3v3_source"] = Power
CAPABILITY_TABLE["Power_3v3"] = Power
CAPABILITY_TABLE["Power_5v0_source"] = Power
CAPABILITY_TABLE["Power_5v0"] = Power
CAPABILITY_TABLE["Power_7v4_source"] = Power
CAPABILITY_TABLE["Power_7v4"] = Power
CAPABILITY_TABLE["Power_12v0_source"] = Power
CAPABILITY_TABLE["Power_12v0"] = Power
CAPABILITY_TABLE["Power_48v0_source"] = Power
CAPABILITY_TABLE["Power_48v0"] = Power
CAPABILITY_TABLE["Power_batt_source"] = Power
CAPABILITY_TABLE["Power_batt"] = Power
CAPABILITY_TABLE["Power_ref_source"] = Power
CAPABILITY_TABLE["Power_ref"] = Power
CAPABILITY_TABLE["Power_source"] = Power
CAPABILITY_TABLE["Power"] = Power

CAPABILITY_TABLE["adc"] = Pin
CAPABILITY_TABLE["dac"] = Pin
CAPABILITY_TABLE["pwm"] = Pin
CAPABILITY_TABLE["dio"] = Pin
CAPABILITY_TABLE["reset"] = Pin
CAPABILITY_TABLE["ext_int"] = Pin
CAPABILITY_TABLE["edio"] = Pin
CAPABILITY_TABLE["iv_sense"] = IVSense
CAPABILITY_TABLE["pass"] = Pin
CAPABILITY_TABLE["uart"] = UART
CAPABILITY_TABLE["fullduplex_uart_w_enable"] = FullDuplexUARTWithEnable
#CAPABILITY_TABLE["rs485"] = rs485
CAPABILITY_TABLE["sd"] = sd
CAPABILITY_TABLE["jtag"] = jtag
CAPABILITY_TABLE["jtag_no_rst"] = jtag_no_rst
CAPABILITY_TABLE["can"] = can
CAPABILITY_TABLE["i2c"] = i2c
CAPABILITY_TABLE["i2c_0"] = i2c
CAPABILITY_TABLE["spi"] = spi
for spi_name in spi_bundles.keys():
  CAPABILITY_TABLE[spi_name] =  spi_name
CAPABILITY_TABLE["usb_2"] = usb_2
CAPABILITY_TABLE["swd"] = swd
CAPABILITY_TABLE["DiffPair"] = DiffPair
CAPABILITY_TABLE["edp"] = edp
#CAPABILITY_TABLE["LVDS"] = `LVDS
CAPABILITY_TABLE["LVDS_clk"] = LVDS_clk
CAPABILITY_TABLE["pcie_lane"] = pcie_lane
# Dummy capabiltiy for crossbar use
CAPABILITY_TABLE["bar_pin"] = Pin

#for e in CAPABILITY_TABLE:
#  if value(e) == `: = Pin
#    pcb_capability {Ref(key(e))} = pin
#  else :
#    pcb_capability {Ref(key(e))} = {Ref(value(e))}
