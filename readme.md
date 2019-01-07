### Embedded Systems Intermediate Representation ###

The Embedded Systems Intermediate Representation is a data format for formally describing the properties of electrical components with sufficient enough detail as to enable automatic generation and optimization. 

### Installing JitPCB on Linux ###

The distribution includes precompiled binaries for the Linux operating system, and so the following instructions will be targeted for Linux. 

JitPCB requires Stanza 0.12.13. Please visit www.lbstanza.org to download and install the appropriate version for Linux. 

Extract the contents of the distribution to a folder called mydir/myjitpcb. Then within that folder run the following command:

    ./jitpcb install

The above command will create a configuration file called '.jitpcb' in the user's home directory.

Next, include the following two lines in your .stanza configuration file,

    pkg-dirs = ("/fullpathto/mydir/myjitpcb/pkgs")
    fast-pkg-dirs = ("/fullpathto/mydir/myjitpcb/fast-pkgs")

where '/fullpathto/mydir/myjitpcb' is the fully resolved path to the 'mydir/myjitpcb' folder. 

### Running the Supplied Example ###

The distribution comes with an example design called 'examples/decouple-test.esir'. 

The following command reads in the design, verifies wellformedness, and then exports the design to the Mentor Graphics Key-In format. 

./jitpcb process examples/decouple-test -passes key-in

This produces the output file 'examples/decouple-test.kyn'.

### Components and Modules ###

Every ESIR consists of a collection of 'components' which each represent a single circuit component. As an example, here is the definition of an operational amplifier.

    pcb-component opamp :
      pin vs+
      pin vs-
      pin vout
      pin v+
      pin v-

It is named 'opamp', and has five pins: the positive and negative power supply pins, vs+ and vs-, the positive and negative input pins, v+ and v-, and the output pin, vout. 

Here is an example of a simple resistor :

    pcb-component resistor :
      pin a
      pin b

A 'module' represents a circuit board, and represents a collection of components and the connections between them. Here is an example of a board that instantiates two resistors and one opamp:

    pcb-module mydesign :
      inst r1 : resistor
      inst r2 : resistor
      inst opamp : opamp

      net n1 (r1.a, opamp.v+)
      net n2 (r1.b, opamp.v-)
      net n3 (opamp.vout, r2.a)
      net n4 (opamp.vs-, r2.b)

The 'inst' statement instantiates a component. The following statement:

    inst r1 : resistor

creates an instance of the 'resistor' component called 'r1'. 

The 'net' statement creates a connection between pins in the design. The following statement:

    net n1 (r1.a, opamp.v+)

creates a connection between the 'a' pin of 'r1' and the 'v+' pin of 'opamp'. This connection is named 'n1'. 

We use the following command to designate a particular module as the top-level module for the circuit board.

    make-board(mydesign)

### Type System Overview ###

The ESIR type system is comprised of three separate mechanisms: the pin type system, the capability system, and the electrical model system. 

The pin type system allows us to define and reuse groups of pins. 

The capability system allows us to specify annotate the particular features supported by a component and by which pins. 

The electrical model system allows us to annotate a component with its electrical properties for use in simulation and part substitution. 

During component selection, a part is defined to be substitutable with another part, if the proposed part supports a superset of the required capabilities and is annotated with a compatible electrical model.

### The Pin Type System ###

There are three different categories of pin types supported: single pins, arrays of pins, and bundles of pins. The following is an example of a connector component with twenty pins. 

   pcb-component connector :
     port p : pin[20]

To refer to these pins within a net we use the '[]' notation. The following module instantiates a connector and connects the first pin to its last pin.

    pcb-module mydesign :
      inst c : connector
      net n (c.p[0], c.p[19])

A 'bundle' definition allows us to define and reuse a group of related pins, such as the positive and negative rails for a power connection. Here is an example of a bundle called 'dual', which consists of a 'pos' and 'neg' pin.

    pcb-bundle dual :
      pin pos
      pin neg

Given that definition, the 'opamp' component shown earlier can be redefined as the follows:

    pcb-component opamp :
      port vs : dual
      port vin : dual
      pin vout

The dot operator ('.') is used to refer to a field within a bundle. Here is the rewritten 'mydesign' module shown earlier to reflect the changes made to the 'opamp' component:

    pcb-module mydesign :
      inst r1 : resistor
      inst r2 : resistor
      inst opamp : opamp

      net n1 (r1.a, opamp.vin.pos)
      net n2 (r1.b, opamp.vin.neg)
      net n3 (opamp.vout, r2.a)
      net n4 (opamp.vs.neg, r2.b)

The types can be recursively constructed. The following is an example of an array of twenty 'dual' ports. 

    port p : dual[20]

The following is an array of ten arrays of twenty 'dual' ports. 

    port p : dual[10][20]

Note that the type 'pin' corresponds to a single pin. The syntax:

    pin p

is equivalent to the following:

    port p : pin

### The Capability System ###

The capability system allows us to annotate components with the features that it supports, and also indicate which pins that it supports them on. 

Capabilities need to first be defined. The following creates a capability called 'usb', which has a pin type 'dual'.

    pcb-capability usb : dual

After a capability has been defined, we can indicate which capabilities a component supports by using the 'support' statement.

    pcb-component proc :
      port p : pin[10]
      supports usb :
        usb.pos => p[0]
        usb.neg => p[1]
      supports usb :
        option :
          usb.pos => p[2]
          usb.neg => p[3]
        option :
          usb.pos => p[2]
          usb.neg => p[4]

The above example indicates that the 'proc' component can support up to two 'usb' capabilities. The first is supported on pins 'p[0]' and 'p[1]'. The second is supported  *either* on pins 'p[2]' and 'p[3]', or on pins 'p[2]' and 'p[4]'. 

These supported capabilities must then be explicitly requested when instantiating a component. The following example demonstrates instantiating two 'proc' components and wiring a 'usb' capability of one to a 'usb' capability of the other.

    pcb-module mydesign :
      inst proc-a : proc with :
        require myusb : usb
      inst proc-b : proc with :
        require myusb : usb
      net n1 (proc-a.myusb.pos, proc-b.myusb.pos)
      net n2 (proc-a.myusb.neg, proc-b.myusb.neg)

The system is free to choose which pins on each 'proc' to assign the 'usb' capability to. 

If desired, the user can also explicitly specify which pins to satisfy a capability using. The following request:

  inst proc-a : proc with :
    require myusb : usb with :
      proc-a.myusb.neg => p[4]

specifies that the 'proc-a' instance of component 'proc' requires a 'usb' capability. This capability must map the 'neg' pin to pin 'p[4]'. From the definition of 'proc', this implies that the 'pos' pin must necessarily then be mapped to 'p[2]'. 

### The Electrical Model System ###

The electrical model system provides a way to annotate components with their electrical properties. 

There are currently three types of models supported: resistors, capacitors, and inductors.

A resistor is specified by its resistance (in ohms), tolerance (in percent), and maximum power (in watts). The following is an example of annotating a component as a resistor.

    pcb-component resistor :
      pin a
      pin b
      emodel = Resistor(10.0, 5.0, 1.0)

A capacitor is specified by its capacitance (in microfarads), tolerance (in percent), maximum voltage (in volts), whether it is polarized, whether it has low ESR, its temperature coefficient (which can be either X7R or X5R), and its dielectric (which can either Ceramic, Tantalum, or Electrolytic). The following is an example:

    emodel = Capacitor(10.0, 5.0, 3.3, false, false, `X7R, `Ceramic)

An inductor is specified by its inductance (in microhenries), tolerance (in percent), and maximum current (in amps). The following is an example:

    emodel = Inductor(10.0, 5.0, 1.0)

