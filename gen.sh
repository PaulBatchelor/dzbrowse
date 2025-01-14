DZBROWSE_PATH=dzbrowse

./$DZBROWSE_PATH/dzimport.py dzfiles.txt a.db

if [ -f logfiles.txt ]
then
    ./$DZBROWSE_PATH/batchlogs.py logfiles.txt
fi

if [ -f codefiles.txt ]
then
    CODEPATH="."
    if [ "$#" -gt 0 ]
    then
        CODEPATH=$1
    else
        GIT_TOP=$(git rev-parse --show-toplevel)
        CWD=$(pwd)
        DZPATH=$(echo $CWD | sed "s|^$GIT_TOP/dz/||")
        CODEPATH=$GIT_TOP/code/$DZPATH
    fi

    ./dzbrowse/batchcode.py $CODEPATH | sqlite3 a.db
fi

./$DZBROWSE_PATH/generate.py a.db

if [ ! -f style.css ]
then
    ln -s $DZBROWSE_PATH/style.css .
fi