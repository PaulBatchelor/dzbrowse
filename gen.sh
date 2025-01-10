DZBROWSE_PATH=dzbrowse

./$DZBROWSE_PATH/dzimport.py dzfiles.txt a.db

if [ -f logfiles.txt ]
then
    ./$DZBROWSE_PATH/batchlogs.py logfiles.txt
fi

./$DZBROWSE_PATH/generate.py a.db

if [ ! -f style.css ]
then
    ln -s $DZBROWSE_PATH/style.css .
fi
