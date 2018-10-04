#!/usr/bin/python

import sys
import yaml
import matplotlib.pyplot as plt
import datetime as dt
import matplotlib.dates as mdates

def stamp_to_mdate(ts):
  return mdates.date2num(dt.datetime.fromtimestamp(ts))

def plot_designs(designs):
  fig, ax = plt.subplots()
  
  t0_tn_names = []

  for name, steps in designs.iteritems() :
    t0 = min(min(steps.values()))
    tn = max(max(steps.values()))
    t0_tn_names.append((t0, tn, name))

  sorted_names = sorted(t0_tn_names)

  y_idxs = {name[-1]:i for name,i in zip(sorted_names, range(len(sorted_names)))}

  colormap = get_color_map(designs)
  
  series = {k:[] for k in colormap.keys()}

  for name, steps in designs.iteritems() :
    xs_steps = []

    for step, times in steps.iteritems():
      mds = [stamp_to_mdate(t) for t in times]
      if len(mds) == 2 :
        xs_steps.append( ((mds[0], mds[1] - mds[0]), step) )
      elif len(mds) == 3 :
        xs_steps.append( ((mds[0], mds[1] - mds[0]), '.wait') )
        xs_steps.append( ((mds[1], mds[2] - mds[1]), step) )
          
    for xs, step in xs_steps :
      label = step_suffix(step)
      series[label].append( ( xs, (y_idxs[name] - 0.3, 0.6) ) )
  
  for boxes, label in sorted(zip(series.values(), series.keys())) :
    maybe_label = label
    color = colormap[label]
    for xs, ys in boxes:
      ax.broken_barh([xs], ys, facecolors=color, edgecolors=color, label=maybe_label)
      maybe_label = None
  
  plt.xticks(rotation = 45)
  xfmt = mdates.DateFormatter('%Y-%m-%d %H:%M:%S')
  ax.xaxis.set_major_formatter(xfmt)
  xloc = mdates.SecondLocator(bysecond = range(0,60,10))
  ax.xaxis.set_major_locator(xloc)
  fig.subplots_adjust(left=0.13,bottom=0.15,top=0.9,right=0.98)

  plt.yticks(y_idxs.values(), y_idxs.keys())
  ax.grid(True)

  plt.legend(loc='lower center', bbox_to_anchor=(0.5,1.01), ncol=(len(series) + 1)/2)
  
  fig.set_size_inches(24.0,16.0,forward=True)
  
  return fig

def step_suffix(step):
  suffix = '.'.join(step.split('.')[1:])
  if suffix == '':
    suffix = 'executable'
  return suffix

def get_color_map(designs):
  suffixes = set(['wait'])

  for _, steps in designs.iteritems() :
    for step, times in steps.iteritems() :
      if len(times) > 1 :
        suffixes.add(step_suffix(step))
  
  jet_cm = plt.cm.get_cmap('Set1', len(suffixes))
  
  colors = [jet_cm(i) for i in range(len(suffixes))]

  return dict(zip(suffixes, colors))

if __name__ == '__main__':
  f = open(sys.argv[1])
  designs = yaml.load(f)
  f.close()
  
  fig = plot_designs(designs)

  if len(sys.argv) > 2 :
    fig.savefig(sys.argv[2])
  else :
    plt.show()
