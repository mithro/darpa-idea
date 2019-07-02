# Generates a function to add bypass capacitors to an FPGA according to ug583-bypassing.csv
# Presently just uses xcku060ffva1517pkg.csv to figure out the power rails
# Supply other xilinx provided ***pkg.csv files to generate bypassing for other part numbers

from collections import defaultdict

part_numbers_to_process = ("xcku060ffva1517",)

def readCSV(fname):
    f = open(fname)
    lines = f.readlines()
    f.close()
    rows = [[entry.strip() for entry in line.split(',')] for line in lines]
    return rows

def readBypassCapTable():
    fname = "ug583-bypassing.csv"
    rows = readCSV(fname)
    # First 2 rows are headers
    # First row is name of the rail to put a capacitor on
    # Second row is the size of capacitor to put on it
    # All other rows are the number of capacitors of the designated size to put on the designated rail for the designated part
    rails = rows.pop(0)
    def soft_cast(f):
        try:
            return float(f)
        except:
            return f
    cap_sizes = [soft_cast(val) for val in rows.pop(0)]
    cap_designations = tuple(zip(rails, cap_sizes))

    # Key:   Part number:string
    # Value: Dict:
    #       Key:   (rail name:string, cap value:float)
    #       Value: Number of capacitors:int
    rval = defaultdict(dict)

    def homogenizePN(pn):
        return pn.lower().replace("-","")
    for row in rows:
        pn = homogenizePN(row[0])
        for i in range(1,len(row)):
            rval[pn][cap_designations[i]] = int(row[i])
    return rval
# Key:   Part number:string
# Value: Dict:
#       Key:   (rail name:string, cap value:float)
#       Value: Number of capacitors:int
bypass_cap_table = readBypassCapTable()
print(bypass_cap_table)

def readRailsForPart(pn):
    csv_name = pn+"pkg.csv"
    rows = readCSV(csv_name)
    header = rows.pop(0)
    rail_names = [k[0] for k in bypass_cap_table[pn].keys()]
    rval = {}
    for row in rows:
        pin_name = row[1]
        rail_name = None
        # Special case: the HXIO rails are all labeled VREF_NN where NN is an index
        if pin_name.startswith("VREF"):
            test_name = row[4]+"IO"
            if test_name in rail_names:
                rail_name = test_name
        else:
            for test_name in rail_names:
                if pin_name.startswith(test_name):
                    rail_name = test_name
                    break
        if rail_name is not None:
            rval[pin_name] = rail_name
    return rval

# Key:   Part number:string
# Value: Dictionary
#       Key:   Pin name (string)
#       Value: Rail to apply bypass caps from (String)
pin_table = {}
for pn in part_numbers_to_process:
    pin_table[pn] = readRailsForPart(pn)

class Indenter(object):
    def __init__(self):
        self.__indent = 0
    def indent(self):
        self.__indent += 1
    def undent(self):
        self.__indent -= 1
    def print(self, *args):
        print(("  " * self.__indent), *args)

def stanzifyName(s):
    s = s.replace('_','-')
    s = s.replace(' ', '-')
    s = s.lower()
    return s

def generateBypassModule(pn):
    printer = Indenter()
    printer.print("defn bypass-%s (cmp:Ref):"%pn)
    printer.indent()
    printer.print("inside pcb-module:")
    printer.indent()
    caps = bypass_cap_table[pn]
    rails = pin_table[pn]
    # Key: (pin-name, size)
    # Value: stanza statement
    gen_cap_stmts = {}
    for (outer_rail, size), q in caps.items():
        for unstanzified_pin_name, inner_rail in rails.items():
            if outer_rail == inner_rail:
                pin_name = stanzifyName(unstanzified_pin_name)
                gen_cap_stmt = "cap-strap(cmp.%s, cmp.gnd, %0.1f)"%(pin_name,size)
                if q == 0:
                    continue
                elif q == 1:
                    pass
                if q >= 2:
                    gen_cap_stmt = "for i in 0 to %u do: "%q + gen_cap_stmt
                gen_cap_stmts[pin_name, size] = gen_cap_stmt
    sorted_keys = sorted(gen_cap_stmts.keys())
    for key in sorted_keys:
        printer.print(gen_cap_stmts[key])
    printer.undent() # inside pcb-module
    printer.undent() # function def

for pn in part_numbers_to_process:
    generateBypassModule(pn)
