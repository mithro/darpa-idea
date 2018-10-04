#!/usr/bin/python

import numpy
import scipy.spatial
import sys
import time
import yaml

MAX_N_TP = 256
MAX_N_VIN = 16
MAX_N_VOUT = 16

TP_MIN_DIST = 2.0

DUT_AREA = {
  'width': 50.0,
  'height': 50.0,
}

ATE_AREA = {
  'width': 60.0,
  'height': 150.0,
}

TP_TYPES = ['digital-io', 'analog-in', 'analog-out', 'pass-through']

def inclusive_randint(a, b=None):
  if b is None:
    v_min = 0
    v_max = a
  else :
    v_min = a
    v_max = b

  return numpy.random.randint(v_max - v_min + 1) + v_min

def random_test_board_config(seed=None, n_tp=None, n_vin=None, n_vout=None):
  if seed is None:
    t = time.time()
    seed = int((t - numpy.floor(t)) * (2**32-1))

  numpy.random.seed(seed)

  # 2 <= n_tp <= MAX_N_TP
  if n_tp is None :
    n_tp = inclusive_randint(2,MAX_N_TP)
  elif n_tp < 2 :
    raise ValueError('n_tp must be >= 2')

  # 1 <= n_vin <= min(n_tp-1, MAX_N_VIN)
  if n_vin is None :
    n_vin = inclusive_randint(1,min(n_tp-1,MAX_N_VIN))
  elif n_vin < 1 :
    raise ValueError('n_vin must be >= 1')

  # 0 <= n_vout <= min(n_tp - 1 - n_vin, MAX_N_VOUT)
  if n_vout is None :
    n_vout = inclusive_randint(min(n_tp-1-n_vin,MAX_N_VOUT))
  elif n_vout < 0 :
    raise ValueError('n_vout must be >= 0')

  # n_vin + n_vout + 1 <= n_tp
  if n_vin + n_vout + 1 > n_tp :
    raise ValueError('Illegal voltage pin configuration')

  return {
    'seed':seed,
    'n_tp':n_tp,
    'n_vin':n_vin,
    'n_vout':n_vout,
  }

def string_to_config(s):
  tokens = s.split('_')
  fields = ['seed','n_tp','n_vin','n_vout']
  config = {f:None for f in fields}
  for i in range(len(tokens)):
    config[fields[i]] = int(tokens[i])
  return config

def random_points(seed=0, n_tp=0, dut_area=DUT_AREA, tooling_pins=None, tp_min_dist=TP_MIN_DIST, **kwargs):
  numpy.random.seed(seed)
  
  if tooling_pins is None:
    tooling_pins = []

  tool_pin_dists = numpy.array([(pin['diameter'] + tp_min_dist) / 2 for pin in tooling_pins])
  tool_pin_locs = numpy.array([pin['loc'] for pin in tooling_pins])
  
  pts = numpy.inf * numpy.ones((n_tp,2))
  
  w = dut_area['width']
  h = dut_area['height']
  d = tp_min_dist / 2

  def random_point():
    return numpy.random.rand(1,2) * [w - 2*d, h - 2*d] - [w/2 - d, h/2 - d]

  def valid_point_dist(p, ps, ds):
    dists = numpy.sum((ps-p)**2,axis=1) 
    valid = dists > ds ** 2
    return valid.all()
    
  def valid_point(p):
    pts_valid = valid_point_dist(p, pts, tp_min_dist)
    pins_valid = valid_point_dist(p, tool_pin_locs, tool_pin_dists)
    return pts_valid and pins_valid

  for idx in range(n_tp):
    pt = random_point()
    while not valid_point(pt):
      pt = random_point()

    pts[idx] = pt
      
  return pts

def random_voltage_config(seed=0, n_vin=1, n_vout=0, tp_types=TP_TYPES, **kwargs):
  numpy.random.seed(seed)
  
  v_config = [{'v_dir':'in'},{'v_dir':'in', 'v_val':5.0, 'v_ref':0}]
  v_config += [{'v_dir':'in', 'v_val':(5.0 * v), 'v_ref':0} for v in numpy.random.rand(n_vin-1)]
  
  def v_out_config(v):
    cfg = {'v_dir':'out', 'v_val':(5.0 * v), 'v_ref':0}
    if 'analog-out' in tp_types :
      cfg['analog-out'] = 1
    return cfg

  v_config += [v_out_config(v) for v in numpy.random.rand(n_vout)]

  return v_config

def random_test_point_config(seed=0, n_tp=2, n_vin=1, n_vout=0, tp_types=TP_TYPES,  **kwargs):
  numpy.random.seed(seed)
  
  n_v = n_vin + n_vout
  rnd_types = numpy.random.randint(0, len(tp_types), n_tp - (n_v + 1))
  rnd_refs = numpy.random.randint(1, n_v+1, n_tp - (n_v + 1))

  tp_config = [{tp_types[t]:r} for t,r in zip(rnd_types, rnd_refs)]

  return tp_config

def random_test_board(seed=None, n_tp=None, n_vin=None, n_vout=None, tp_types=TP_TYPES, config_str=None, **kwargs):
  config = kwargs
  config['tp_types'] = tp_types

  if config_str is not None :
    config.update(string_to_config(config_str))
  else :
    config.update(random_test_board_config(seed, n_tp, n_vin, n_vout))
    
  seed = config['seed']
  n_tp = config['n_tp']

  pts = random_points(**config)
  
  v_configs = random_voltage_config(**config)

  tp_configs = random_test_point_config(**config)
  
  v_tp_configs = v_configs + tp_configs

  numpy.random.seed(seed)
  rnd_order = numpy.random.permutation(n_tp)
  
  test_points = [
    {
      'name':'TP_%04d' % i,
      'loc':pts[i].tolist(),
    } for i in range(n_tp)
  ]
  
  test_points[rnd_order[0]]['name'] = 'DUT_GND'
  test_points[rnd_order[1]]['name'] = 'DUT_VIN'

  # Update the voltage reference index in configs with the resulting randomly
  # permuted test point index
  for v_tp_cfg in v_tp_configs :
    for k in v_tp_cfg.keys() :
      if k in tp_types + ['v_ref'] :
        v_tp_cfg[k] = test_points[rnd_order[v_tp_cfg[k]]]['name']

  for v_tp_cfg, idx in zip(v_tp_configs, rnd_order) :
    test_points[idx].update(v_tp_cfg)

  config['test_points'] = test_points

  return config

def config_to_string(c):
  return '%010d_%04d_%02d_%02d' % (c['seed'], c['n_tp'], c['n_vin'], c['n_vout'])

def write_test_board(test_points=None, filename=None, tp_types=TP_TYPES, dut_area=DUT_AREA, ate_area=ATE_AREA, tooling_pins=None, **kwargs):
  if test_points is None:
    test_points = []

  if filename is None:
    filename = 'test-gen-%s.i' % config_to_string(config)
  
  if tooling_pins is None:
    tooling_pins = []

  f = open(filename,'w')
  f.write('board :\n  width = %0.4f\n  height = %0.4f\n\n' % (dut_area['width'],dut_area['height']))
  f.write('working-area :\n  width = %0.4f\n  height = %0.4f\n\n' % (ate_area['width'],ate_area['height']))
  
  for pin in tooling_pins :
    l = pin['loc']
    d = pin['diameter']
    f.write('tooling-pin at loc(%.4f,%.4f):\n  diameter = %.4f\n\n' % (l[0], l[1], d))

  search_keys = set(tp_types + ['v_dir'])
  
  for tp in test_points :
    x,y = tp['loc']

    ending_colon = ''
    
    tp_keys = set(tp.keys())

    if not search_keys.isdisjoint(tp_keys) :
      ending_colon = ':'

    f.write('test-point %s at loc(%.4f,%.4f)%s\n' % (tp['name'],x,y,ending_colon))
    
    if 'v_dir' in tp.keys() :
      if 'v_ref' in tp.keys() :
        v_spec = '%.2f relative to %s' % (tp['v_val'],tp['v_ref'])
      else :
        v_spec = 'GND'
      f.write('  voltage(%s) = %s\n' % (tp['v_dir'],v_spec))
      
    for k in tp.keys() :
      if k in tp_types :
        if k == 'digital-io' :
          f.write('  %s :\n    voltage = %s\n' % (k, tp[k]))
        else :
          f.write('  %s :\n    voltage = DUT_VIN\n' % k)

    f.write('\n')

  f.close()

if __name__ == '__main__':
  config = {'filename':None}

  int_args = []
  str_args = []
  yaml_args = []
  flag_args = {}
  
  skip_arg = False
  
  str_fields = ['filename']
  int_fields = ['seed','n_tp','n_vin','n_vout']

  for arg, next_arg in zip(sys.argv[1:], sys.argv[2:] + [None]) :
    if skip_arg :
      skip_arg = False
    else :
      # Flag argument
      if arg[0] == '-' :
        flag = arg.strip('-')
        if next_arg is not None and not next_arg[0] == '-' :
          skip_arg = True
          if flag == 'config' :
            yaml_args.append(next_arg)
          else :
            if flag in int_fields :
              next_arg = int(next_arg)
            flag_args[flag] = next_arg
        else :
          flag_args[flag] = True

      # YAML argument
      elif arg.endswith('.yaml') :
        yaml_args.append(arg)

      # Int or String argument
      else :
        try :
          int_args.append(int(arg))
        except :
          str_args.append(arg)
  
  # Load YAML parameter files and update config
  for yaml_arg in yaml_args :
    f = open(yaml_arg)
    config.update(yaml.load(f))
    f.close()
  
  # Update config with command line flag arguments
  config.update(flag_args)

  # Update config with positional integer arguments
  config.update(dict(zip(int_fields, int_args)))
  
  # Update config with positional string arguments
  config.update(dict(zip(str_fields, str_args)))

  board_config = random_test_board(**config)

  write_test_board(**board_config)
