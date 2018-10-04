ROOT=`pwd`
FILES="../src/ir/ir-gen-macros.stanza ../src/utils/serialize-macros.stanza ../src/ir/rtm-ir.stanza ../src/ir/ir-gen.stanza ../src/ir/ir-printer.stanza ../src/ir/ir-serializer.stanza ../src/ir/ir-reader.stanza ../src/ir/ir-errors.stanza ../src/ir/ir-utils.stanza ../src/utils/errors.stanza ../src/utils/plugins.stanza ../src/utils/plugins-master.stanza ../src/utils/plugins-slave.stanza ../src/utils/serialize.stanza ../src/utils/dlopen.stanza ../src/utils/rtm-utils.stanza ../src/utils/structures.stanza ../src/main/flags.stanza ../src/main/errors.stanza ../src/main/driver.stanza ../src/main/launcher.stanza ../src/main/config.stanza ../src/main/jitpcb.stanza ../src/main/pass-manager.stanza ../src/main/param-manager.stanza ../src/main/passes.stanza ../src/ir/part-solver.stanza ../src/ir/ir-check.stanza ../src/ir/ir-lower.stanza ../src/ir/reader-plugin.stanza ../src/ir/pin-solver.stanza ../src/ir/pin-state.stanza ../src/ir/key-in.stanza"
#cd $ROOT
#rm -r stage
#mkdir stage
#mkdir stage/plugins
#mkdir stage/fplugins
#mkdir stage/pkgs
#mkdir stage/fast-pkgs
#cp -r runtime stage
#cp -r scripts stage
#cp License.txt stage
#cp jitpcb.params stage
#cd $ROOT/stage
#echo "Compiling auxiliary files"
#echo "Compiling pkgs"
#../jstanza $FILES -pkg pkgs
#echo "Compiling fast-pkgs"
#../jstanza $FILES -pkg fast-pkgs -optimize
#echo "Compiling jitpcb-debug"
#../jstanza jitpcb -pkg pkgs -ccfiles ../runtime/rtm-utils.c -ccflags "" -o jitpcb-debug
#echo "Compiling jitpcb"
#../jstanza jitpcb -pkg fast-pkgs -ccfiles ../runtime/rtm-utils.c -ccflags "" -o jitpcb -optimize
#echo "Compiling checker plugin"
#../jstanza rtm/ir-check -pkg pkgs -ccfiles ../runtime/rtm-utils.c -ccflags "-shared" -o plugins/checker.plugin
#../jstanza rtm/ir-check -pkg fast-pkgs -ccfiles ../runtime/rtm-utils.c -ccflags "-shared" -optimize -o fplugins/checker.plugin
#echo "Compiling parsers plugin"
#../jstanza rtm/reader-plugin -pkg pkgs -ccfiles ../runtime/rtm-utils.c -ccflags "-shared" -o plugins/parsers.plugin
#../jstanza rtm/reader-plugin -pkg fast-pkgs -ccfiles ../runtime/rtm-utils.c -ccflags "-shared" -optimize -o fplugins/parsers.plugin
#echo "Compiling key-in plugin"
#../jstanza key-in -pkg pkgs -ccfiles ../runtime/rtm-utils.c -ccflags "-shared" -o plugins/key-in.plugin
#../jstanza key-in -pkg fast-pkgs -ccfiles ../runtime/rtm-utils.c -ccflags "-shared" -optimize -o fplugins/key-in.plugin
#echo "Cleanup auxiliary files"
cd $ROOT
rm -r lstage
mkdir lstage
mkdir lstage/plugins
mkdir lstage/fplugins
mkdir lstage/pkgs
mkdir lstage/fast-pkgs
cp -r runtime lstage
cp -r scripts lstage
cp License.txt lstage
cp jitpcb.params lstage
cd $ROOT/lstage
cp $ROOT/scripts/.lstanza .stanza
cp $ROOT/scripts/lfinish.sh finish.sh
echo "Compiling pkgs"
../jstanza $FILES -pkg pkgs
echo "Compiling fast-pkgs"
../jstanza $FILES -pkg fast-pkgs -optimize
echo "Compiling jitpcb-debug"
../jstanza jitpcb -pkg pkgs -s jitpcb-debug.s
echo "Compiling jitpcb"
../jstanza jitpcb -pkg fast-pkgs -s jitpcb.s -optimize
echo "Compiling checker plugin"
../jstanza rtm/ir-check -pkg pkgs -s plugins/checker.plugin.s
../jstanza rtm/ir-check -pkg fast-pkgs -optimize -s fplugins/checker.plugin.s
echo "Compiling parsers plugin"
../jstanza rtm/reader-plugin -pkg pkgs -s plugins/parsers.plugin.s
../jstanza rtm/reader-plugin -pkg fast-pkgs -optimize -s fplugins/parsers.plugin.s
echo "Compiling key-in plugin"
../jstanza key-in -pkg pkgs -s plugins/key-in.plugin.s
../jstanza key-in -pkg fast-pkgs -optimize -s fplugins/key-in.plugin.s
rm .stanza
