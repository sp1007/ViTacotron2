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

python -m multiproc train.py -m Tacotron2 -o ./%OUTPUT_FOLDER%/ -lr 1e-3 --epochs 1501 -bs 12 --epochs-per-checkpoint 5 --weight-decay 1e-6 --grad-clip-thresh 1.0 --cudnn-enabled --cudnn-benchmark --log-file nvlog.json --text-cleaners vietnamese_cleaners --training-files %TRAINLIST% --validation-files %VALLIST% --anneal-steps 500 1000 1500 --anneal-factor 0.1

endlocal