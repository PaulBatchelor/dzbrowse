# eventually, this will evolve into a more versatile
# shell script

DZFILES="dzfiles.txt"

if [ "$#" -gt 0 ]
then
    DZFILES=$1
fi

DBFILE=""

if [ "$#" -gt 1 ]
then
    DBFILE=$2
fi

while read -r LINE
do
    if [ "$DBFILE" == "" ]
    then
        dagzet $LINE
    else
        dagzet $LINE | sqlite3 $DBFILE
    fi

    if [[ ! $? -eq 0 ]]
    then
        exit 1
    fi
done < $DZFILES
