#!/usr/bin/python

import numpy as np
import sys
import yaml
from random_tester_board import *

def extract_test_point_dict(ipc_356_points):

  return { i['name']:i for i in [
    {
    'name' : tp['net_name'],
    'loc' : [tp['x_pos'], tp['y_pos']]
    } for tp in ipc_356_points if (
        tp['net_name'] != 'N/C' and 
        not tp['tooling_hole'] and
        not tp['smd_feature']
        )
    ]
  }

def center_dut_area(tp_dict) :
  locs = numpy.array([v['loc'] for v in tp_dict.values()])
  loc_min = locs.min(axis=0)
  loc_max = locs.max(axis=0)

  dut_dims = loc_max - loc_min

  cx, cy = loc_min + (dut_dims) / 2

  for props in tp_dict.values() :
    loc = props['loc']
    props['loc'] = [loc[0] - cx, loc[1] - cy]

  dut_w, dut_h = dut_dims + 4.0
  
  return {
    'test_points': tp_dict.values(),
    'dut_area': {'width':dut_w, 'height':dut_h},
    'ate_area': {'width':max(dut_w * 2, 10.0 * (len(locs + 7)/8) + 40.0), 'height':(dut_h + 30.0)}
  }

def import_356_D(infile):
  units_to_mm = False
  test_points = list()

  file = open(infile, 'r')

  for line in file:
    des = line[0]
    if des is 'C':
      continue

    elif des is 'P':
      if 'UNITS' in line:
        if 'CUST 0' in line:
          units_to_mm = 0.00254
          print "Units: 0.0001 inches"
        elif 'CUST 1' in line:
          units_to_mm = 0.001
          print "Units: microns"
        elif 'CUST 2' in line:
          units_to_mm = 0.00254
          print "Units: microns"
        else:
          raise Exception('Unsupported units')
      else:
        continue

    elif des == '3':
      if units_to_mm == False:
        raise Exception('Units undefined')
      if line[2] != '7':
        continue
      net_name = (line[3:17]).strip()
      ref_des =  (line[20:26]).strip()
      pin_number = (line[26:31]).strip()
      if line[31] == 'M':
        net_middle = True
      else:
         net_middle = False
      if line[1] == '1':
        smd_feature = False
        # Element == a thru-hole
        hole_dia = float(int((line[33:37]).strip()))*units_to_mm
        tooling_hole = False
        if line[37] == 'U':
          plated = False
        else:
          plated = True
      elif line[1] =='6':
        smd_feature = False
        # Element is a thru-hole
        hole_dia = float(int((line[33:37]).strip()))*units_to_mm
        tooling_hole = True
        if line[37] == 'U':
          plated = False
        else:
          plated = True
      elif line[1] == '2':
        smd_feature = True
        # TODO: specifying these for a smd feature is strange
        plated = True
        hole_dia = False
        tooling_hole = False
      access_side = int((line[39:41]).strip())
      # 00: both sides, 01: Primary side, 0X:Accessible from X layer (usually last in stack)
      x_pos = float(int((line[43:49]).strip()))*units_to_mm
      if line[42] == '-':
        x_pos = x_pos*-1
      y_pos = float(int((line[51:57]).strip()))*units_to_mm
      if line[50] == '-':
        y_pos = y_pos*-1  
      # Currently ignoring feature size/geometry, cols 58-71  

      test_loc = {
      'net_name':net_name,
      'ref_des':ref_des,
      'pin_number':pin_number,
      'net_middle':net_middle,
      'hole_dia':hole_dia,
      'plated':plated,
      'tooling_hole':tooling_hole,
      'access_side':access_side,
      'smd_feature':smd_feature,
      'x_pos':x_pos,
      'y_pos':y_pos,
      }
      test_points.append(test_loc)

    elif des is '9':
      if '999' in line:
        print('Found end of file')
        return test_points

def assign_power_nets(tp_dict, gnd_name, pwr_name) :
  gnd_dict = tp_dict.pop(gnd_name)
  gnd_dict.update({'name':'DUT_GND', 'v_dir':'in'})
  tp_dict['DUT_GND'] = gnd_dict
  pwr_dict = tp_dict.pop(pwr_name)
  pwr_dict.update({'name':'DUT_VIN', 'v_dir':'in', 'v_val':5.0, 'v_ref':'DUT_GND'})
  tp_dict['DUT_VIN'] = pwr_dict
  
if __name__ == '__main__':
  ipc_356_pts = import_356_D(sys.argv[1])
  tp_dict = extract_test_point_dict(ipc_356_pts)
  assign_power_nets(tp_dict, 'GND', 'NONAME362')
  tp_board = center_dut_area(tp_dict)
  write_test_board(filename=sys.argv[2], **tp_board)
