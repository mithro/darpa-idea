#!/usr/bin/python3
from collections import Iterable
from collections import defaultdict
from subprocess import check_output
import os.path
import csv

"""
README: This script extracts a component definition with appropriate supports/pin/port statements
based on xdc files exported from FPGA software.  It will look at al *.xdc files in the current directory,
build a list of the properties assigned to them, unify them, and generate pcb-component
"""

# Grab all .xdc files in the current directory
s = check_output('ls')
s = check_output('find . -name "*.xdc"',shell=True).decode("ASCII")
fnames = [x.strip() for x in s.split()]

lines = []

for fname in fnames:
    f = open(fname)
    lines.extend(f.readlines())
    f.close()

lines = [l.strip() for l in lines]
print("Read %u lines"%len(lines))
# Remove empties
lines = filter(lambda l:l,lines)
# Remove comments
lines = filter(lambda l:l[0] != '#', lines)
lines = list(lines)
print("After filtering comments and empties: %u lines"%len(lines))

# Import csv file. Kinda hacky - maybe replace with dict?
csv_name = "xcku060ffva1517pkg.csv"

csv_lines = []
f = open(csv_name)
csv_lines.extend(f.readlines())
f.close()
csv_lines = [l.replace(" ", "").split(',') for l in csv_lines[1::]]
pwr_names = list(set([l[1] for l in csv_lines if any(x in l[1] for x in ('GND', 'VCC', 'VTT'))]))
pwr_pins = []
for n in pwr_names:
    pwr_pins.append([l[0] for l in csv_lines if l[1] == n])

def vioRef(padName):
    bank = 'VCCO_' + [l[3] for l in csv_lines if l[0] == padName][0]
    pin = [l[0] for l in csv_lines if l[1] == bank][0]
    return stanzifyName(bank)

def smartSplit(s,end_char=None):
    if isinstance(s,str):
        s = [c for c in s]
    pairs = {}
    pairs['('] = ')'
    pairs['['] = ']'
    pairs['{'] = '}'
    tokens = []
    token = ''
    while s:
        c = s.pop(0)
        if c in pairs:
            if token:
                tokens.append(token)
                token = ''
            tokens.append(smartSplit(s,pairs[c]))
        elif c == end_char:
            if token:
                tokens.append(token)
            end_char = None
            break
        else:
            token += c
    if end_char:
        print("Unterminated group!")
    rval = []
    for t in tokens:
        if isinstance(t,str):
            rval.extend(t.split())
        else:
            rval.append(t)
    return rval

# Structure of this dictionary:
# Keys: (pinname:string, pinindex:int)
# Values: Dictionary:
#       Keys: propname:string
#       Values: props:one of (list, string, int, float)
# pinindex is None for non-vector pins

props_ = defaultdict(lambda:{})

def stanzifyName(s):
    s = s.replace('_','-')
    s = s.replace(' ', '-')
    s = s.lower()
    return s

def processPinName(l):
    # Expect a list of grouped tokens representing the strings like "get_ports {CB_AD[7]}"
    getter = l[0]
    name = ''
    index = None
    if getter == 'get_ports':
        if isinstance(l[1],str):
            # Unvectored pin name
            name = l[1]
        elif len(l[1]) == 1:
            # Unvectored pin name, for some reason wrapped like a vectored one (why?)
            name = l[1][0]
        elif len(l[1]) == 2:
            # Vectored pin name
            name = l[1][0]
            index_token = l[1][1][0]
            if index_token == '*':
                # Wildcard will be applied to all indices when parsing finished
                index = index_token
            else:
                index = int(index_token)
        else:
            raise Exception("Unexpected tokens parsing pin name")
    else:
        print("Unhandled pin getter %s"%getter)
    return stanzifyName(name),index

def handleSetProperty(s):
    tokens = smartSplit(s)
    assert(tokens.pop(0)=='set_property')
    propname = tokens.pop(0)
    propval = tokens.pop(0)
    pinref = processPinName(tokens.pop(0))
    if not pinref[0]:
        #Finish early, could not process the pinref
        print("Unhandled: %s" % s)
        return
    propdict = props_[pinref]
    if propval == None:
        raise Exception("None propval")
    propdict[propname] = propval

line_handlers = {}
line_handlers['set_property'] = handleSetProperty

for l in lines:
    tokens = l.split()
    cmd = tokens[0]
    if cmd in line_handlers:
        line_handlers[cmd](l)
    else:
        print("Unhandled setter: %s"%l)

# Apply wildcard parameters
wildcards = set(filter(lambda x:x[1]=='*',props_))
wildcards = set(x[0] for x in wildcards)
for k in props_.keys():
    if k[0] in wildcards:
        props_[k].update(props_[(k[0],'*')])
for wc in wildcards:
    del props_[(wc,'*')]
del wildcards

# Check to see that all pins have a package assigned
no_package = set()
for k,v in props_.items():
    if 'PACKAGE_PIN' not in v:
        print("Pin %s has no package"%(str(k)))
        no_package.add(k)
for k in no_package:
    del props_[k]
del no_package

# Just for debugging
param_pools = defaultdict(set)
for v in props_.values():
    for k,v in v.items():
        param_pools[k].add(v)
print(param_pools)


# Evaluating gaps in pin indices (just for debugging)
index_dict = defaultdict(set)
for name, index in props_.keys():
    index_dict[name].add(index)
for name, indices in index_dict.items():
    if None in indices:
        if len(indices)>1:
            print("%s is both subscripted AND unsubscripted!"%name)
    else:
        for i in range(len(indices)):
            if i not in indices:
                print("%s is missing index %u!" % (name,i))
del index_dict

def groupPinsWithSuffixGroup(suffices):
    rval = defaultdict(set)
    for k, v in props_.items():
        for suffix in suffices:
            if k[0].endswith(suffix):
                gname = k[0][:-len(suffix)]
                rval[(gname, k[1])].add(k)
                break
    items = tuple(rval.items())
    # Remove all elements which don't have one of each suffix
    for k,v in items:
        if len(v) != len(suffices):
            print("Group %s length is %u, needed %u, removing"%(k,len(v),len(suffices)))
            del rval[k]
        elif not all(any(pinref[0].endswith(suf) for pinref in v) for suf in suffices):
            print("Group %s has bad suffix set: "%name,v, ", removing")
            del rval[k]
    return rval

# Infer LVDS pairs from pin names
# NOTE: Only one pin in an LVDS pair has to carry the LVDS IOSTANDARD, the other can be blank
diffpair_suffix = ('-p', '-m')
diffpair_pairs_ = groupPinsWithSuffixGroup(diffpair_suffix)

items = tuple(diffpair_pairs_.items())
for k,v in items:
    tag = "IOSTANDARD"
    iostandards = set(props_[pinref][tag] for pinref in filter(lambda x:tag in props_[x], v))
    if None in iostandards:
        iostandards.remove(None)
    if len(iostandards) == 0:
        def subIOStandardForNameMatch(name,inferred_standard):
            if name in k[0]:
                print(k, " is %s and carries no IOSTANDARD , assuming %s"%(name, inferred_standard))
                iostandards.add(inferred_standard)
                return True
            return False
        if subIOStandardForNameMatch('ddr3','DIFF_SSTL15'):
            pass
        elif subIOStandardForNameMatch('lvds', 'LVDS'):
            pass
        elif subIOStandardForNameMatch('aurora', 'SERDES'):
            pass
        elif subIOStandardForNameMatch('pci', 'SERDES'):
            pass
        else:
            print(k, " carries no IOSTANDARD , removing.")
            del diffpair_pairs_[k]
    elif len(iostandards) > 1:
        print(k, " carries multiple conflicting IOSTANDARDs : %s, removing." % (str(iostandards)))
        del diffpair_pairs_[k]
    elif next(iter(iostandards)) != "LVDS":
        print(k, " carries %s IOSTANDARD despite carrying LVDS naming, removing." % (next(iter(iostandards))))
        del diffpair_pairs_[k]
    elif len(v) != 2:
        print(k, " doesn't have 2 members (has %u), removing."%len(v))
        del diffpair_pairs_[k]
    # Make sure both pins have the IOstandard
    if len(iostandards) > 0:
        standard = next(iter(iostandards))
        if standard == None:
            raise("Bad")
        for pinref in v:
            props_[pinref]["IOSTANDARD"] = standard
            print(props_[pinref]["PACKAGE_PIN"])
del items
print(diffpair_pairs_)

# Infer UART pairs from pin names
fullduplex_uart_suffix = ('-tx','-rx','-tx-en')
fullduplex_uart_sets_ = groupPinsWithSuffixGroup(fullduplex_uart_suffix)

rxonly_uart_suffix = ('-rx',)
rxonly_uart_sets_ = groupPinsWithSuffixGroup(rxonly_uart_suffix)
for k in fullduplex_uart_sets_:
    if k in rxonly_uart_sets_:
        del rxonly_uart_sets_[k]

i2c_suffix = ('-scl','-sda')
i2c_sets_ = groupPinsWithSuffixGroup(i2c_suffix)

pinrefs_in_bundles_ = set()
for val in diffpair_pairs_.values():
    for pinref in val:
        pinrefs_in_bundles_.add(pinref)
for val in fullduplex_uart_sets_.values():
    for pinref in val:
        pinrefs_in_bundles_.add(pinref)
for val in i2c_sets_.values():
    for pinref in val:
        pinrefs_in_bundles_.add(pinref)

def pinrefEndsWith(pinref,suffices):
    for end in suffices:
        if pinref[0].endswith(end):
            return end
    return None

def dumpPropsToCSV():
    f = open('out.csv', 'w+')
    param_names = list(param_pools.keys())
    param_names.sort()
    f.write("PINNAME, INDEX, ")
    for n in param_names:
        f.write(n+', ')
    f.write('\n"')
    k = list(props_.keys())
    k.sort()
    for p in k:
        f.write(p[0] + ', ')
        if p[1] != None:
            f.write(str(p[1]))
        f.write(', ')
        for n in param_names:
            if n in props_[p] and props_[p][n] != None:
                f.write(props_[p][n])
            f.write(', ')
        f.write('\n')
    f.close()
dumpPropsToCSV()
del param_pools

# FIXME TODO Handle PCIe lanes.  You need to actually get to work on the generators even though your parsing of the xbd files is incomplete

def pinrefToName(k):
    # If this is a diffpair we need to use D_P and D_N style names
    suffix = None
    if k in pinrefs_in_bundles_:
        suffix = pinrefEndsWith(k, diffpair_suffix + fullduplex_uart_suffix + i2c_suffix)
    if suffix:
        prefix = k[0][:-len(suffix)]
    else:
        prefix = k[0]
    rval = prefix
    if k[1] != None:
        rval += '-' + str(k[1])
    # Append appropriate bundle accessor
    suffix_translate = {}
    suffix_translate['-m'] = '.D_N'
    suffix_translate['-p'] = '.D_P'
    suffix_translate['-rx'] = '.rx'
    suffix_translate['-tx'] = '.tx'
    suffix_translate['-tx-en'] = '.en'
    suffix_translate['-sda'] = '.sda'
    suffix_translate['-scl'] = '.scl'
    if suffix in suffix_translate:
        rval += suffix_translate[suffix]
    return rval

# Translate IOSTANDARDs to family and voltage
def convertIOSTANDARD():
    # IOSTANDARD name => (family, voltage)
    lookup = {}
    # CHECK ALL THESE VOLTAGES, NOT SURE
    lookup['LVDS']           = ('LVDS',   1.5)
    lookup['DIFF_SSTL15']    = ('SSTL',   1.5)
    lookup['SERDES']         = ('SERDES', 1.8)
    lookup['DIFF_HSTL_I_18'] = ('HSTL',   1.8)
    lookup['LVCMOS18']       = ('LVCMOS', 1.8)
    lookup['LVCMOS33']       = ('LVCMOS', 3.3)
    lookup[None]             = ('LVCMOS', 1.8) #DEFAULT
    for pinref, propset in props_.items():
        k = 'IOSTANDARD'
        if k in propset:
            replacements = lookup[propset[k]]
            del propset[k]
        else:
            replacements = lookup[None]
            print("Pin %s had no IOSTANDARD set, using default %s"%(pinrefToName(pinref),str(replacements)))
        propset['family'] = replacements[0]
        propset['voltage'] = replacements[1]
convertIOSTANDARD()

# Load the csv file, which has default values, which we will fill in for pins that aren't already populated
# The only way we can correlate the csvs to the xdcs is through the pad name.
# So build a set of the pads already occupied so we can know what lines to exclude
def readCSV(fname):
    f = open(fname)
    lines = f.readlines()
    f.close()
    # Read Header
    header_fields = [stanzifyName(x.strip()) for x in lines.pop(0).split(',')]
    table = defaultdict(lambda: {})
    for l in lines:
        fields = [x.strip() for x in l.split(',')]
        pad_name = fields[0]
        #pin_name = fields[1]
        for i in range(len(fields)):
            if fields[i]:
                table[pad_name][header_fields[i]] = fields[i]
    return table
csv_table = readCSV('xcku060ffva1517pkg.csv')

# Build a map to the props keyed on the pad
pad_map = {}
for k,v in props_.items():
    pad_map[v['PACKAGE_PIN']] = v

for pad, vals in csv_table.items():
    pin_name = stanzifyName(vals['pin-name'])
    def translate(vals, lookup):
        rval = {}
        for k,v in vals.items():
            if k in lookup:
                k = lookup[k]
                if k == None:
                    continue
            rval[k] = v
        return rval
    lookup = {}
    lookup['pin'] = 'PACKAGE_PIN'
    lookup['pin-name'] = None
    vals = translate(vals, lookup)
    if pad not in pad_map:
        # Fresh entry
        pinref = (pin_name,None)
        if pinref not in props_:
            props_[pinref] = vals.copy()
        else:
            target_dict = props_[pinref]
            for k,v in vals.items():
                if k in target_dict:
                    if isinstance(target_dict[k],list):
                        target_dict[k].append(v)
                    else:
                        new_val = [target_dict[k], v]
                        target_dict[k] = new_val
del pad_map

class Writer(object):
    def __init__(self,file):
        self.file = file
        self.__indent = 0
    def __startLine(self):
        self.file.write('  '*self.__indent)
    def writeLine(self,*args):
        self.__startLine()
        for arg in args:
            self.file.write(str(arg))
        self.file.write('\n')
    def indent(self):
        self.__indent += 1
    def unindent(self):
        self.__indent -= 1

def stringifyProp(prop):
    if isinstance(prop,list):
        propstring = '['
        propstring += ', '.join('%s'%stringifyProp(s) for s in prop)
        propstring += ']'
    elif isinstance(prop,float):
        propstring = str(prop)
    elif isinstance(prop,int):
        propstring = str(prop)
    elif prop[0] in "0123456789":
        # Starts with a number, can't treat as symbol
        propstring = '"%s"'%prop
    else:
        propstring = '`'+prop
    return propstring

def dumpPropertiesToTable(pinref, writer):
    props_to_write = props_[pinref]
    if len(props_to_write):
        name = pinrefToName(pinref)
        str = '[#R(' + name + '), '
        for propname, propval in props_to_write.items():
            if propname == 'PACKAGE_PIN':
                pin = propval
                str = str + stringifyProp(pin) + ', ['
        for propname, propval in props_to_write.items():
            if propname != 'PACKAGE_PIN':
                str = str + '`' + propname + ' => ' + stringifyProp(propval) + ' '
        str = str + ']]'
        writer.writeLine(str)

def flatten(l):
    for el in l:
        if isinstance(el, Iterable) and not isinstance(el, (str, bytes)):
            yield from flatten(el)
        else:
            yield el

def dumpPinAndPropertyDeclarations():
    my_path = os.path.abspath(os.path.dirname(__file__))
    path = os.path.join(my_path, "../xcku060-cmp.stanza")
    f = open(path, 'w+')
    writer = Writer(f)
    writer.writeLine("defpackage xcku060-cmp :")
    writer.indent()
    writer.writeLine("import core")
    writer.writeLine("import collections")
    writer.writeLine("import components")
    writer.writeLine("import symbols")
    writer.writeLine("import math")
    writer.writeLine("import input-spec/ir")
    writer.writeLine("import rtm/ir")
    writer.writeLine("import rtm/ir-gen")
    writer.writeLine("import rtm/ir-connections")
    writer.writeLine("import rtm/ir-utils")
    writer.unindent()
    writer.writeLine("#use-added-syntax(ir-gen)")

    writer.writeLine("pcb-component xilinx-XCKU060-1FFVA1517I-cmp :")
    writer.indent()
    # Write table
    # First go through writing the diff pairs

    def declareBundleTable(bundle_dict, bundle_str):
        bundle_names = list(bundle_dict.keys())
        bundle_names.sort()
        for name in bundle_names:
            for pinref in bundle_dict[name]:
                dumpPropertiesToTable(pinref, writer)
    def declareBundles(bundle_dict, bundle_str):
        bundle_names = list(bundle_dict.keys())
        bundle_names.sort()
        for name in bundle_names:
            writer.writeLine("port ", pinrefToName(name), " : %s"%bundle_str)

    # Declare bundles
    declareBundles(diffpair_pairs_, 'diff-pair')
    declareBundles(fullduplex_uart_sets_, 'fullduplex-uart-w-enable')
    declareBundles(i2c_sets_, 'i2c')

    # Declare the individual pins
    solo_pinrefs = list(props_.keys())
    for pinref in pinrefs_in_bundles_:
        solo_pinrefs.remove(pinref)
    solo_pinrefs.sort()
    for pinref in solo_pinrefs:
        writer.writeLine("pin ", pinrefToName(pinref))

    # Declare all "supports" statements
    for pinref in solo_pinrefs:
        writer.writeLine("supports dio:")
        writer.indent()
        writer.writeLine("dio => ", pinrefToName(pinref))
        writer.unindent()
    # TODO: DDR3, pci-lane, serdes-par pair
    for pairs in diffpair_pairs_.values():
        writer.writeLine("supports lvds:")
        writer.indent()
        suffices = {}
        suffices['-p'] = '.D_P'
        suffices['-m'] = '.D_N'
        for pinref in pairs:
            writer.writeLine(pinrefToName(('lvds' + suffices[pinrefEndsWith(pinref,diffpair_suffix)],None)), ' => ',pinrefToName(pinref))
        writer.unindent()
    for sets in fullduplex_uart_sets_.values():
        writer.writeLine("supports fullduplex-uart-w-enable:")
        writer.indent()
        suffices = {}
        suffices['-rx'] = '.rx'
        suffices['-tx'] = '.tx'
        suffices['-tx-en'] = '.en'
        for pinref in sets:
            writer.writeLine(pinrefToName(('fullduplex-uart-w-enable' + suffices[pinrefEndsWith(pinref,fullduplex_uart_suffix)],None)), ' => ',pinrefToName(pinref))
        writer.unindent()
    for sets in i2c_sets_.values():
        writer.writeLine("supports i2c:")
        writer.indent()
        suffices = {}
        suffices['-sda'] = '.sda'
        suffices['-scl'] = '.scl'
        for pinref in sets:
            writer.writeLine(pinrefToName(('i2c' + suffices[pinrefEndsWith(pinref,i2c_suffix)],None)), ' => ',pinrefToName(pinref))
        writer.unindent()

    writer.writeLine("val xcku-060-cmp-pins = [")
    writer.indent()
    declareBundleTable(diffpair_pairs_, 'diff-pair')
    declareBundleTable(fullduplex_uart_sets_, 'fullduplex-uart-w-enable')
    declareBundleTable(i2c_sets_, 'i2c')
    for pinref in solo_pinrefs:
        dumpPropertiesToTable(pinref, writer)
    #for i in range(len(pwr_names)):
    #    str = '[#R(' + stanzifyName(pwr_names[i]) + '), ['
    #    for p in pwr_pins[i][:]:
    #        str = str + '`' + p + ', '
    #    str = str[0:-2] + '], []]'
    #    writer.writeLine(str)
    writer.unindent()
    writer.writeLine("]")

    writer.writeLine("for [ref, lnd, props] in xcku-060-cmp-pins do :")
    writer.writeLine("  properties(ref) :")
    writer.writeLine("    PACKAGE_PIN => lnd")
    writer.writeLine("    for p in props do :")
    writer.writeLine("      {Ref(key(p))} => value(p)")
    writer.writeLine("val left-mapping = Vector<KeyValue<Ref, ?>>()")
    writer.writeLine("for [ref, lnd, _] in xcku-060-cmp-pins do :")
    writer.writeLine("  add(left-mapping, ref => lnd)")
    writer.writeLine("val ps = PinSpec(to-tuple(left-mapping), false)")
    writer.writeLine("package = BGA1517C100P39X39-4000X4000X351N(cmp-pad-map(ps))")
    writer.writeLine("part = xilinx-XCKU060-1FFVA1517I-prt")

    f.close()
dumpPinAndPropertyDeclarations()

