if [ $# -lt 2 ]; then
    echo "Not enough arguments: Expected osx/linux 0.0.1."
    exit 2
fi

DIR=`pwd`
if [ "$1" == "linux" ] || [ "$1" == "all" ]
then
  cd /Users/patricksli/Docs/Programming/jitpcb-release
  git checkout linux
  rsync -avz --delete $DIR/lstage/ . --exclude=/.git
  git add -A
  git commit -m "version $2"
  git push
  cd $DIR
fi
if [ "$1" == "osx" ] || [ "$1" == "all" ]
then
  cd /Users/patricksli/Docs/Programming/jitpcb-release
  git checkout osx
  rsync -avz --delete $DIR/stage/ . --exclude=/.git
  git add -A
  git commit -m "version $2"
  git push
  cd $DIR
fi
if [ "$1" == "linux-rc" ] || [ "$1" == "all-rc" ]
then
  cd /Users/patricksli/Docs/Programming/jitpcb-release
  git checkout linux-rc
  rsync -avz --delete $DIR/lstage/ . --exclude=/.git
  git add -A
  git commit -m "version $2"
  git push
  cd $DIR
fi
if [ "$1" == "osx-rc" ] || [ "$1" == "all-rc" ]
then
  cd /Users/patricksli/Docs/Programming/jitpcb-release
  git checkout osx-rc
  rsync -avz --delete $DIR/stage/ . --exclude=/.git
  git add -A
  git commit -m "version $2"
  git push
  cd $DIR
fi