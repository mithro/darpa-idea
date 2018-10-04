#!/usr/bin/python

import yaml
import sys
import numpy

def int_idxs(bool_idx) :
  return numpy.arange(len(bool_idx))[bool_idx]

def idxs_vals(vals) :
  return zip(range(len(vals)), vals)

def exception_regions(exceptions) :
  regions = numpy.nan * numpy.ones([len(exceptions), 4])
  
  for e_i, e in idxs_vals(exceptions) : 
    regions[e_i] = [e[f] for f in ['x_min', 'x_max', 'y_min', 'y_max']]

  nan_idx = numpy.isnan(regions).any(axis = 1)

  if any(nan_idx) :
    print 'Warning: following exception regions were not set:%s' % str(int_idxs(nan_idx))
    
    regions = regions[~nan_idx]
  
  inval_idx = (regions[:,0] > regions[:,1]) | (regions[:,2] > regions[:,3])

  if any(inval_idx) :
    print 'Warning: following excpetion regions are invalid:%s' % str(ind_idxs(inval_idx))

    regions = regions[~inval_idx]

  return regions

# Return the set of region indices that contain any point in points
def regions_containing_points(regions, points) :
  containing = set()

  for x, y in points :
    bool_idx = (regions[:,0] <= x) & (x <= regions[:,1]) & (regions[:,2] <= y) & (y <= regions[:,3])
    containing.update(int_idxs(bool_idx))
  
  return containing

def init_exception_matches(exceptions) :
  exception_matches = []

  unroute_net_idxs = {}
  
  for e in exceptions :
    if 'unroute' in e['expected_errors'] :
      if 'net' in e.keys() :
        unroute_net_idxs[e['net']] = e['index']
      else :
        print 'Warning: no net name for expected unroute index %d' % e['index']
    
    matches = {drc_type:[] for drc_type in e['expected_errors']}
    
    exception_matches.append(matches)
  
  return exception_matches, unroute_net_idxs

def compare_drc(violations, exceptions) :
  remaining_violations = []

  regions = exception_regions(exceptions)
  
  exception_matches, unroute_net_idxs = init_exception_matches(exceptions)

  for v in violations :
    match_idxs = set()

    if v.has_key('points') :
      r_idxs = regions_containing_points(regions, v['points'])
      for r_idx in r_idxs :
        if exception_matches[r_idx].has_key(v['drc_type']) :
          match_idxs.update([r_idx])

    if v['drc_type'] == 'unroute' :
      if unroute_net_idxs.has_key(v['net']) :
        match_idxs.update([unroute_net_idxs[v['net']]])
      else :
        print 'Warning: unroute net "%s" not found in unroute net table.' % v['net']

    for match_idx in match_idxs :
      exception_matches[match_idx][v['drc_type']].append(v['index'])

    if len(match_idxs) == 0 :
      remaining_violations.append(v)

  unmet_exceptions = []
  
  for m_i, m in zip(range(len(exception_matches)), exception_matches) :
    if any([len(match_list) == 0 for match_list in m.values()]) :
      unmet_exceptions.append(exceptions[m_i])

  result = {}
  result['remaining_violations'] = remaining_violations
  result['unmet_exceptions'] = unmet_exceptions

  return result

def correct_drc_names(violations) :
  for v in violations :
    if v['drc_type'] == 'copper_too_narrow' :
      v['drc_type'] = 'min_copper_width'

if __name__ == '__main__':
  violations_file = sys.argv[1]
  exceptions_file = sys.argv[2]
  comparison_file = sys.argv[3]

  with open(violations_file) as vf, open(exceptions_file) as ef :
    violations = yaml.load(vf)
    correct_drc_names(violations)

    exceptions = yaml.load(ef)
    comparison = compare_drc(violations, exceptions)

    print '==== DRC Comparison Result ===='
    print '  Remaining Violations: %d' % len(comparison['remaining_violations'])
    print '  Unmet Exceptions: %d' % len(comparison['unmet_exceptions'])

    with open(comparison_file, 'w') as cf :
      yaml.dump(comparison, cf)
