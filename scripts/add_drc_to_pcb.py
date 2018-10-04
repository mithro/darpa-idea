#!/usr/bin/python

import sys
import yaml
import numpy

def pcb_line(layer, start, end) :
  lines = [
    '  (gr_line (start %f %f) (end %f %f) (layer %s) (width 0.02))\n' % (
      start[0], start[1], end[0], end[1], layer
    )
  ]

  return lines

def pcb_cross(layer, pos) :
  x,y = pos
  l0 = pcb_line(layer, (x - 0.1, y - 0.1), (x + 0.1, y + 0.1))
  l1 = pcb_line(layer, (x - 0.1, y + 0.1), (x + 0.1, y - 0.1))
  
  return l0 + l1

def pcb_text(layer, pos, text) :
  lines = [
    '  (gr_text %s (at %f %f) (layer %s)\n' % (text, pos[0], pos[1], layer),
    '    (effects (font (size 0.2 0.2) (thickness 0.02)) (justify left))\n',
    '  )\n'
  ]
  
  return lines

def pcb_circle(layer, pos, r) :
  lines = [
    '  (gr_circle (center %f %f) (end %f %f) (layer %s) (width 0.02))\n' % (
      pos[0], pos[1], pos[0] + r, pos[1], layer
    )
  ]

  return lines

def pcb_box(layer, bounds) :
  xmin, xmax, ymin, ymax = bounds
  
  l0 = pcb_line(layer, (xmin, ymin), (xmax, ymin))
  l1 = pcb_line(layer, (xmax, ymin), (xmax, ymax))
  l2 = pcb_line(layer, (xmax, ymax), (xmin, ymax))
  l3 = pcb_line(layer, (xmin, ymax), (xmin, ymin))
  
  return l0 + l1 + l2 + l3

def pcb_error_lines(layer, points, text) :
  lines = []


  # 1D array is bounds for expected error box
  if len(points.shape) == 1 :
  
    offset = [0.5, -0.5, -0.5, 0.5] if layer == 'Margin' else 4 * [0.0]
    op = points + offset
    lines.extend(pcb_box(layer, op))

    lines.extend(pcb_text(layer, (op[0], op[2] - 0.5), text))

  # Otherwise 2D array of violation points
  else :
    center = numpy.zeros(2)
    for point in points :
      center += point
      lines.extend(pcb_cross(layer, point))
  
    center = center / len(points)

    r = 1.2 if layer == 'Margin' else 1.0
    lines.extend(pcb_circle(layer, center, r))
    
    t_coord = 0.707 * (r + 0.2)
    lines.extend(pcb_text(layer, center + t_coord, text))
  
  return lines

def pcb_error(comparison, error, pcb_origin, net_coords) :
  error_text = {
    'min_annular_ring':'AR',
    'min_copper_copper_space':'CC',
    'min_copper_edge_space':'CE',
    'min_copper_hole_space':'CH',
    'min_copper_width':'CW',
    'min_drill_diameter':'DR',
    'min_silkscreen_width':'SS',
    'unroute':'UR'
  }
  
  # Draw expected error box
  if error.has_key('expected_errors') :
    layer = 'Margin' if comparison else 'Eco2.User'
    text = ','.join([error_text[e] for e in error['expected_errors']])
    if text == '' :
      text = 'NONE'

    # Need to negate Y axis and translate to origin for KiCAD coordinates
    x,y = pcb_origin
    points = numpy.array([
      x + error['x_min'],
      x + error['x_max'],
      y - error['y_min'],
      y - error['y_max']
    ])

  # Draw circle and crosshairs for violation
  else :  
    layer = 'Margin' if comparison else 'Eco1.User'
    text = '%s-%s' % (error_text[error['drc_type']], error['index'])
    
    if error.has_key('points') :
      # Need to negate Y axis and translate to origin for KiCAD coordinates
      points = numpy.array(error['points']) * [1, -1] + pcb_origin

    # Use net pad coordinate for unroute
    else :
      points = numpy.array([net_coords[error['net']]])
  
  return pcb_error_lines(layer, points, text)

def get_error_lines(errors, pcb_origin, net_coords) :
  error_list = []
  
  comparison = False

  if type(errors) is list :
    error_list = errors
  
  if type(errors) is dict :
    comparison = True
    for error_group in errors.values() :
      error_list.extend(error_group)

  error_lines = []

  for error in error_list :
    error_lines.extend(pcb_error(comparison, error, pcb_origin, net_coords))
  
  return error_lines

def insert_lines_at_match(pcb_lines, match_str, new_lines) :
  insert_idx = [line.startswith(match_str) for line in pcb_lines].index(True)
  return pcb_lines[:insert_idx] + new_lines + pcb_lines[insert_idx:]
  
def get_pcb_origin(pcb_lines) :
  origin = numpy.ones([1,2]) * numpy.nan

  for line in pcb_lines :
    if line.find('gr_line') > -1 and line.find('B.SilkS') > -1 :
      tks = line.replace(')','').replace('(','').strip().split()
      pts = numpy.array([
        [float(tks[2]), float(tks[3])],
        [float(tks[5]), float(tks[6])]
      ])
      origin = pts.mean(axis=0)
  
  return origin

def get_pcb_net_coords(pcb_lines) :
  net_coords = {}

  for idx in range(len(pcb_lines)) :
    if pcb_lines[idx].startswith('  (module drc-stress-test.kicad:test-point-pads-pkg') :
      
      parse_idx = idx
      paren_count = 0
      mod_tokens = []

      def parse_line(parse_idx, paren_count, mod_tokens) :
        line = pcb_lines[parse_idx]
        paren_count += line.count('(') - line.count(')')
        mod_tokens += line.replace('(',' [ ').replace(')',' ] ').split()
        parse_idx += 1
        return parse_idx, paren_count, mod_tokens

      parse_idx, paren_count, mod_tokens = parse_line(parse_idx, paren_count, mod_tokens)
      while paren_count > 0 :
        parse_idx, paren_count, mod_tokens = parse_line(parse_idx, paren_count, mod_tokens)

      mod_str = ''
      list_tks = []

      for tk in mod_tokens :
        if tk in ['[', ']'] :
          if len(mod_str) > 0 and mod_str[-1] not in [',','['] :
            mod_str += ','
          if len(list_tks) > 0 :
            mod_str += ','.join(list_tks) + ','
            list_tks = []
          mod_str += tk
        else :
          list_tks.append('"%s"' % tk.strip('"'))

      mod_list = eval(mod_str)

      for mod_elem in mod_list :
        if type(mod_elem) is list :
          if mod_elem[0] == 'at' :
            pos = numpy.array([float(mod_elem[1]), float(mod_elem[2])])

          elif mod_elem[0] == 'pad' :
            for pad_elem in mod_elem :
              if type(pad_elem) is list and pad_elem[0] == 'net' :
                net = pad_elem[2]
      
      net_coords[net] = pos
  
  return net_coords

if __name__ == '__main__':
  pcb_filename = sys.argv[1]

  with open(pcb_filename) as pf :
    pcb_lines = pf.readlines()
    
    pcb_origin = get_pcb_origin(pcb_lines)
    net_coords = get_pcb_net_coords(pcb_lines)

    error_lines = []

    for error_filename in sys.argv[2:] :
      with open(error_filename) as ef :
        errors = yaml.load(ef)
        error_lines.extend(get_error_lines(errors, pcb_origin, net_coords))
    
    pcb_out_lines = insert_lines_at_match(pcb_lines, '  (gr_', error_lines)

    pcb_tks = pcb_filename.split('.')
    pcb_tks.insert(-1, 'drc')
    pcb_out_filename = '.'.join(pcb_tks)

    with open(pcb_out_filename, 'w') as pfo :
      pfo.write(''.join(pcb_out_lines))
