@echo off

setlocal

set "OUTPUT_FOLDER=output\southernvn"
set "FILELISTSDIR=training_data\southernvn\filelist"

set "TESTLIST=%FILELISTSDIR%\vn_audio_text_test_filelist.txt"
set "TRAINLIST=%FILELISTSDIR%\vn_audio_text_train_filelist.txt"
set "VALLIST=%FILELISTSDIR%\vn_audio_text_val_filelist.txt"

set "TESTLIST_MEL=%FILELISTSDIR%\vn_mel_text_test_filelist.txt"
set "TRAINLIST_MEL=%FILELISTSDIR%\vn_mel_text_train_filelist.txt"
set "VALLIST_MEL=%FILELISTSDIR%\vn_mel_text_val_filelist.txt"

if not exist %OUTPUT_FOLDER% (mkdir %OUTPUT_FOLDER%)

python -m multiproc train.py -m WaveGlow -o ./%OUTPUT_FOLDER%/ -lr 1e-4 --epochs 1501 -bs 1 --epochs-per-checkpoint 5 --segment-length 513 --weight-decay 0 --grad-clip-thresh 3.4028234663852886e+38 --cudnn-enabled --cudnn-benchmark --log-file nvlog.json --text-cleaners vietnamese_cleaners --training-files %TRAINLIST% --validation-files %VALLIST%

endlocal