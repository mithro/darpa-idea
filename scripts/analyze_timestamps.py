#!/usr/bin/python

import os
import glob
import sys
import time
import yaml

def sec_to_dt(t):
  return time.strftime('%y/%m/%d %H:%M:%S', time.localtime(t))

def sec_to_hms(t):
  h = int(t / 3600) 
  m = int((t - (h * 3600))/60)
  s = t - (h * 3600 + m * 60)
  
  if s >= 10.0 :
    z = ''
  else :
    z = '0'

  return '%02d:%02d:%s%.2f' % (h,m,z,s)

def get_file_time(f) :
  t = os.path.getmtime(f)
  if f.endswith('continue'):
    fo = open(f,'r')
    t = float(fo.read())
    fo.close()
  return t

def get_design_times(files):
  times = [get_file_time(p) for p in files]

  design_times = {}

  for t,f in sorted(zip(times,files)) :
    root = get_design_root(f)
    step = f

    if f.endswith('.start') :
      step = f[:-6]
    elif f.endswith('.continue') :
      step = f[:-9]
  
    if not design_times.has_key(root) :
      design_times[root] = {}
    
    if not design_times[root].has_key(step) :
      design_times[root][step] = []
    
    design_times[root][step].append(t)

  return design_times

def get_design_root(filename):
  path = filename.split('/')
  design = path[-1].split('.')[0]
  return '/'.join(path[:-1] + [design])

def print_design_times(design_times):
  
  for root, steps in design_times.iteritems() :
    t0 = None

    for times, step in sorted(zip(design_times[root].values(), design_times[root].keys())) :
      if t0 is None:
        t0 = times[0]

        header = '%s - %s' % (root, sec_to_dt(t0))
        print header
        print '=' * len(header)
    
      print '  %s' % step[len(root):]
      print '  %s' % ' '.join([sec_to_hms(t-t0) for t in times])

    print '\n'

if __name__ == '__main__':
  report_file = sys.argv[1]

  design_files = []

  for pattern in sys.argv[2:] :
    design_files.extend(glob.glob(pattern))

  design_times = get_design_times(design_files)

  f = open(report_file, 'w')
  yaml.dump(design_times,f)
  f.close()
