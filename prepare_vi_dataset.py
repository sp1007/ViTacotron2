import argparse
import os
import glob
import pandas as pd

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
                        help='audio folder to save text files')

    return parser

# create arg parser
parser = argparse.ArgumentParser(description='Prepare Vietnamese dataset')
parser = parse_args(parser)
args, _ = parser.parse_known_args()

AUDIO_FOLDER = args.audio.replace('\\', '/')

# let go if input folder is existed
if os.path.exists(args.input):

    #get all input filenames
    filenames = glob.glob(args.input + "/*.txt")

    # init general list
    general_list = None

    # loop all input files
    for fname in filenames:
        #open csv file as pandas object
        print("Open file: ", fname)
        f = pd.read_csv(fname, sep='|', header=None)
        #copy all items into general list
        if general_list==None:
            general_list = f
        else:
            general_list = pd.concat(general_list, f)

    # fix audio folder path
    for r in range(len(general_list)):
        tmp = general_list[0][r].replace('\\','/').split('/')[-1]
        general_list[0][r] = AUDIO_FOLDER + '/' + tmp

    #shuffle rows
    general_list = general_list.sample(frac=1).reset_index(drop=True)

    # now, generate files
    train_data_index = int(TRAIN_RATIO * len(general_list))
    test_data_index = train_data_index + int(TEST_RATIO * len(general_list))

    with open(args.output + '/' + 'vn_audio_text_train_filelist.txt', 'w', encoding='utf-8') as f:
        for i, name in enumerate(general_list[0][:train_data_index]):
            f.write('{}|{}\n'.format(name, general_list[1][i]))

    with open(args.output + '/' + 'vn_audio_text_test_filelist.txt', 'w', encoding='utf-8') as f:
        for i, name in enumerate(general_list[0][train_data_index:test_data_index]):
            f.write('{}|{}\n'.format(name, general_list[1][i]))

    with open(args.output + '/' + 'vn_audio_text_val_filelist.txt', 'w', encoding='utf-8') as f:
        for i, name in enumerate(general_list[0][test_data_index:]):
            f.write('{}|{}\n'.format(name, general_list[1][i]))            
