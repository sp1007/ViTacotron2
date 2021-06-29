@echo off

setlocal

set "INPUT_FOLDER=training_data\southernvn"
set "OUTPUT_FOLDER=training_data\southernvn\filelist"
set "AUDIO_FOLDER=training_data\southernvn\wavs"

echo Check and create Folders ...

if not exist %INPUT_FOLDER% (mkdir %INPUT_FOLDER%)
echo %INPUT_FOLDER%

if not exist %OUTPUT_FOLDER% (mkdir %OUTPUT_FOLDER%)
echo %OUTPUT_FOLDER%

if not exist %AUDIO_FOLDER% (mkdir %AUDIO_FOLDER%)
echo %AUDIO_FOLDER%

echo Done!
echo .
echo Generate training, test and validate filelist

python prepare_vi_dataset.py -i %INPUT_FOLDER% -o %OUTPUT_FOLDER% -a %AUDIO_FOLDER%
echo .
echo Done!

endlocal