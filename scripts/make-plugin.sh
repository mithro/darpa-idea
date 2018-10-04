#Extended compiler
JSTANZA="../bin/jstanza"

#Input source files
FILES="../src/ir/sum-plugin.stanza \
       ../src/utils/errors.stanza \
       ../src/utils/plugins.stanza \
       ../src/utils/plugins-slave.stanza \
       ../src/utils/serialize.stanza \
       ../src/ir/ir-printer.stanza \
       ../src/ir/ir-serializer.stanza \
       ../src/ir/ir-reader.stanza \
       ../src/ir/ir-utils.stanza \
       ../src/ir/ir-errors.stanza \
       ../src/utils/rtm-utils.stanza \
       ../src/ir/rtm-ir.stanza"

#Compile
$JSTANZA $FILES -o sum.plugin -ccfiles runtime/rtm-utils.c -ccflags -shared
