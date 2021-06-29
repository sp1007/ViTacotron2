import argparse
import os
import glob
import random

TRAIN_RATIO = 0.7
TEST_RATIO = 0.2

def parse_args(parser):
    """
    Parse commandline arguments.
    """
    parser.add_argument('-i', '--input', type=str, required=True,
                        help='path to the input text files')
    parser.add_argument('-o', '--output', required=True,
                        help='output folder to save text files')
    parser.add_argument('-a', '--audio', required=True,
                        help='audio folder to save wavs files')
    parser.add_argument('-m', '--mels', required=True,
                        help='mels folder to save pt files')

    return parser

def create_filelist(output_folder, target, data):
    #print(data)
    with open(output_folder + '/' + 'vn_audio_text_' + target + '_filelist.txt', 'w', encoding='utf-8') as f:
        for item in data:
            f.write('{}|{}\n'.format(item['audio'], item['text']))
    with open(output_folder + '/' + 'vn_mel_text_' + target + '_filelist.txt', 'w', encoding='utf-8') as f:
        for item in data:
            f.write('{}|{}\n'.format(item['mel'], item['text']))

def parse_line(line, audio_folder, mel_folder):
    cols = line.split('|')
    wav_name = cols[0].replace('\\','/').split('/')[-1]
    return {"text":cols[1], "audio": audio_folder + '/' + wav_name, 'mel': mel_folder + '/' + wav_name.split('.')[0] + '.pt'}

# create arg parser
parser = argparse.ArgumentParser(description='Prepare Vietnamese dataset')
parser = parse_args(parser)
args, _ = parser.parse_known_args()

AUDIO_FOLDER = args.audio.replace('\\', '/')
MELS_FOLDER = args.mels.replace('\\', '/')

# let go if input folder is existed
if os.path.exists(args.input):

    # init data
    data = []

    #get all input filenames
    filenames = glob.glob(args.input + "/*.txt")

    # loop all input files
    for fname in filenames:
        with open(fname, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            # loop all lines to get info
            for line in lines:
                line=line.strip()
                if line:
                    data.append(parse_line(line, AUDIO_FOLDER, MELS_FOLDER))
            #print(len(data))
    
    # shuffle data
    random.shuffle(data)

    # calc indice
    train_data_index = int(TRAIN_RATIO * len(data))
    test_data_index = train_data_index + int(TEST_RATIO * len(data))

    #write to filelists
    create_filelist(args.output, 'train', data[:train_data_index])
    create_filelist(args.output, 'test', data[train_data_index : test_data_index])
    create_filelist(args.output, 'val', data[test_data_index:])