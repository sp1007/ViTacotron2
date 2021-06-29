@echo off

setlocal

set "MELS_DIR=training_data\southernvn\mels"
set "FILELISTSDIR=training_data\southernvn\filelist"

set "TESTLIST=%FILELISTSDIR%\vn_audio_text_test_filelist.txt"
set "TRAINLIST=%FILELISTSDIR%\vn_audio_text_train_filelist.txt"
set "VALLIST=%FILELISTSDIR%\vn_audio_text_val_filelist.txt"

set "TESTLIST_MEL=%FILELISTSDIR%\vn_mel_text_test_filelist.txt"
set "TRAINLIST_MEL=%FILELISTSDIR%\vn_mel_text_train_filelist.txt"
set "VALLIST_MEL=%FILELISTSDIR%\vn_mel_text_val_filelist.txt"

if not exist %MELS_DIR% (mkdir %MELS_DIR%)

python preprocess_audio2mel.py --wav-files "%TRAINLIST%" --mel-files "%TRAINLIST_MEL%" --text-cleaners vietnamese_cleaners
python preprocess_audio2mel.py --wav-files "%TESTLIST%" --mel-files "%TESTLIST_MEL%" --text-cleaners vietnamese_cleaners
python preprocess_audio2mel.py --wav-files "%VALLIST%" --mel-files "%VALLIST_MEL%" --text-cleaners vietnamese_cleaners

endlocal