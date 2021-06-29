@echo off

setlocal

set "INPUT_FOLDER=training_data\southernvn"
set "OUTPUT_FOLDER=training_data\southernvn\filelist"
set "AUDIO_FOLDER=training_data\southernvn\wavs"
set "MELS_FOLDER=training_data\southernvn\mels"

if not exist %INPUT_FOLDER% (mkdir %INPUT_FOLDER%)
if not exist %OUTPUT_FOLDER% (mkdir %OUTPUT_FOLDER%)
if not exist %AUDIO_FOLDER% (mkdir %AUDIO_FOLDER%)
if not exist %MELS_FOLDER% (mkdir %MELS_FOLDER%)

python prepare_vi_dataset.py -i %INPUT_FOLDER% -o %OUTPUT_FOLDER% -a %AUDIO_FOLDER% -m %MELS_FOLDER%
echo .
echo Done!

endlocal