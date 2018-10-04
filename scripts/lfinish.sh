STANZA=`stanza path`
echo "Linking jitpcb-debug"
gcc -std=gnu99 jitpcb-debug.s $STANZA/runtime/driver.c ../runtime/rtm-utils.c -o jitpcb-debug -lm -D PLATFORM_LINUX -ldl -fPIC
echo "Linking jitpcb"
gcc -std=gnu99 jitpcb.s $STANZA/runtime/driver.c ../runtime/rtm-utils.c -o jitpcb -lm -D PLATFORM_LINUX -ldl -fPIC
rm jitpcb-debug.s
rm jitpcb.s
echo "Linking checker plugin"
gcc -std=gnu99 plugins/checker.plugin.s $STANZA/runtime/driver.c ../runtime/rtm-utils.c -o plugins/checker.plugin -lm -D PLATFORM_LINUX -ldl -fPIC -shared
gcc -std=gnu99 fplugins/checker.plugin.s $STANZA/runtime/driver.c ../runtime/rtm-utils.c -o fplugins/checker.plugin -lm -D PLATFORM_LINUX -ldl -fPIC -shared
rm plugins/checker.plugin.s
rm fplugins/checker.plugin.s
echo "Linking parsers plugin"
gcc -std=gnu99 plugins/parsers.plugin.s $STANZA/runtime/driver.c ../runtime/rtm-utils.c -o plugins/parsers.plugin -lm -D PLATFORM_LINUX -ldl -fPIC -shared
gcc -std=gnu99 fplugins/parsers.plugin.s $STANZA/runtime/driver.c ../runtime/rtm-utils.c -o fplugins/parsers.plugin -lm -D PLATFORM_LINUX -ldl -fPIC -shared
rm plugins/parsers.plugin.s
rm fplugins/parsers.plugin.s
echo "Linking key-in plugin"
gcc -std=gnu99 plugins/key-in.plugin.s $STANZA/runtime/driver.c ../runtime/rtm-utils.c -o plugins/key-in.plugin -lm -D PLATFORM_LINUX -ldl -fPIC -shared
gcc -std=gnu99 fplugins/key-in.plugin.s $STANZA/runtime/driver.c ../runtime/rtm-utils.c -o fplugins/key-in.plugin -lm -D PLATFORM_LINUX -ldl -fPIC -shared
rm plugins/key-in.plugin.s
rm fplugins/key-in.plugin.s
echo "Cleanup auxiliary files"
rm finish.sh
