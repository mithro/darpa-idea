#!/usr/bin/python

import numpy
from svgpathtools import *
import matplotlib.pyplot as plt
import sys

def interpolate_bezier(bezier_path, tvals=numpy.linspace(0.0,1.0,10)):
  """Compute seg.point(t) for each seg in path and each t in tvals."""
  A = numpy.array([[-1,  3, -3,  1], # transforms cubic bez to standard poly
                 		[ 3, -6,  3,  0],
                 		[-3,  3,  0,  0],
                 		[ 1,  0,  0,  0]])
  return numpy.dot(bezier_path.bpoints(), numpy.dot(A, numpy.power(tvals, [[3],[2],[1],[0]])))

def interpolate_path(path):
  pts = []
  for seg in path :
    if type(seg) is CubicBezier :
      pts.extend(interpolate_bezier(seg)[:-1])
    else :
      pts.append(seg.bpoints()[0])
  pts.append(pts[0])
  return pts

def complex_to_cartesian(path):
  return [[p.real, p.imag] for p in path]

def attr_tf(attr):
  R = numpy.eye(2)
  T = numpy.zeros((1,2))
  
  if 'transform' in attr.keys() :
    tf_str = attr['transform']
    tf_type, vals = tf_str.split('(')
    vals = [float(f) for f in vals.strip(')').split(',')]
    
    if tf_type == 'matrix' :
      R =  numpy.array(vals[:4]).reshape(-1,2).T
      T[0,0] = vals[4]
      T[0,1] = vals[5]

    elif tf_type == 'translate' :
      T[0,0] = vals[0]
      if len(vals) > 1 :
        T[0,1] = vals[1]
    
    #print tf_type, vals
    #print R, T

  return R,T

def svg_path_to_points(path,attr):
  p = numpy.array(complex_to_cartesian(interpolate_path(path)))
  R,T = attr_tf(attr)
  return (R.dot(p.T).T + T) * numpy.array([1, -1])

def plot_svg_path(path, attr, ax=plt.gca(), color=(0.0,0.0,0.0)):
  path_pts = svg_path_to_points(path,attr)
  ax.plot(path_pts[:,0], path_pts[:,1], color=color)

def attr_color_str(attr):
  if 'style' in attr.keys() :
    style_dict = {str(kv.split(':')[0]):str(kv.split(':')[1]) for kv in attr['style'].split(';')}
    if 'fill' in style_dict.keys() :
      c_str = style_dict['fill'][1:]
    else :
      c_str = 'ff00ff'
  else :
    c_str = 'ff00ff'
  return c_str.upper()

def attr_color_tuple(attr):
  c_str = attr_color_str(attr)
  return [float(int(c_str[i:(i+2)],16))/255.0 for i in [0,2,4]]

def plot_svg(filename):
  paths, attrs = svg2paths(filename)
  ax = plt.gca()
  ax.patch.set_facecolor('gray')
  plt.axis('equal')
  plt.grid(True)
  for path, attr in zip(paths, attrs):
    plot_svg_path(path, attr, ax, attr_color_tuple(attr))
  plt.show()

color_names = {
  '000000':'black',
  'FF0000':'red',
  'FFFF00':'yellow',
  '00FF00':'green',
  '00FFFF':'cyan',
  '0000FF':'blue',
  'FF00FF':'magenta',
  'FFFFFF':'white'
}

def pts_to_list(pts, indent=4, prefix='p = '):
  return ('\n' + (' ' * indent)).join(['%s(%f,%f)' % (prefix, p[0], p[1]) for p in pts])

spec_template = """input-spec %s :

  board :
    shape = polygon(
      %s
    )
%s
"""

def pts_to_led(pts) :
  pt = pts.mean(axis=0)
  """ 
  cov = numpy.cov(pts.T)
  evals, evecs = numpy.linalg.eig(cov)
  sort_idxs = numpy.argsort(evals)[::-1]
  x,y = evecs[:,sort_idxs][0]
  """
  ml = 0.0
  x, y = 0.0, 1.0
  for p0, p1 in zip(pts[:-1],pts[1:]) :
    v = p1 - p0
    if v.dot(v) > ml :
      ml = v.dot(v)
      x = v[0]
      y = v[1]
  if y < 0.0 :
    x *= -1
    y *= -1
  return (pt[0], pt[1], 180.0 * numpy.arctan2(y,x) / numpy.pi)

silkscreen_template = """
  silkscreen at loc(0.0, 0.0) on Top :
    %s
"""

led_template = """
  binary-led at loc(%s,%s,%s) :
    res-side = bottom
    drive = high
    color = "%s"
"""

def save_jitpcb(infile, outfile) :
  outline = None
  silkscreen = []
  leds = []
  
  paths, attrs = svg2paths(infile)
  
  for p, a in zip(paths,attrs) :
    pts = svg_path_to_points(p,a)
    c_str = attr_color_str(a)
    if c_str == '000000' :
      outline = pts
    elif c_str == 'FFFFFF' :
      silkscreen.append(pts)
    else :
      leds.append(pts_to_led(pts) + (color_names[c_str],))
  
  min_pt = outline.min(axis=0)
  max_pt = outline.max(axis=0)
  scale = 60.0 / (max_pt[0] - min_pt[0])

  outline_str = pts_to_list(scale * (outline - min_pt), 6, 'point') 
  
  silkscreen_str = ''.join([
    silkscreen_template % (
      pts_to_list(scale * (s - min_pt))
    ) for s in silkscreen
  ])
  
  led_idxs = numpy.argsort([l[0] for l in leds])
  led_str = ''.join([
    led_template % (
      scale * (leds[i][0] - min_pt[0]), scale * (leds[i][1] - min_pt[1]), leds[i][2], leds[i][3]
    ) for i in led_idxs
  ])
  
  design_name = infile.split('/')[-1].split('.')[0]

  f = open(outfile,'w')
  f.write(spec_template % (design_name, outline_str, led_str + silkscreen_str))
  f.close()

if __name__ == '__main__':
  if len(sys.argv) > 2 :
    save_jitpcb(sys.argv[1], sys.argv[2])
  elif len(sys.argv) > 1 :
    plot_svg(sys.argv[1])
