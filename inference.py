# *****************************************************************************
#  Copyright (c) 2018, NVIDIA CORPORATION.  All rights reserved.
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are met:
#      * Redistributions of source code must retain the above copyright
#        notice, this list of conditions and the following disclaimer.
#      * Redistributions in binary form must reproduce the above copyright
#        notice, this list of conditions and the following disclaimer in the
#        documentation and/or other materials provided with the distribution.
#      * Neither the name of the NVIDIA CORPORATION nor the
#        names of its contributors may be used to endorse or promote products
#        derived from this software without specific prior written permission.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
#  ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
#  WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#  DISCLAIMED. IN NO EVENT SHALL NVIDIA CORPORATION BE LIABLE FOR ANY
#  DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
#  (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
#  LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#  ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#  (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# *****************************************************************************

from tacotron2.text import text_to_sequence
import models
import torch
import argparse
import numpy as np
from scipy.io.wavfile import write

import sys

import time
from dllogger.logger import LOGGER
import dllogger.logger as dllg
from dllogger.autologging import log_hardware, log_args

from apex import amp

def parse_args(parser):
    """
    Parse commandline arguments.
    """
    parser.add_argument('-i', '--input', type=str, required=True,
                        help='full path to the input text (phareses separated by new line); \
                        if not provided then use default text')
    parser.add_argument('-o', '--output', required=True,
                        help='output folder to save audio (file per phrase)')
    parser.add_argument('--tacotron2', type=str,
                        help='full path to the Tacotron2 model checkpoint file')
    parser.add_argument('--waveglow', type=str,
                        help='full path to the WaveGlow model checkpoint file')
    parser.add_argument('-s', '--sigma-infer', default=0.6, type=float)
    parser.add_argument('-sr', '--sampling-rate', default=22050, type=int,
                        help='Sampling rate')
    parser.add_argument('--amp-run', action='store_true',
                        help='inference with AMP')
    parser.add_argument('--log-file', type=str, default='nvlog.json',
                        help='Filename for logging')
    parser.add_argument('--include-warmup', action='store_true',
                        help='Include warmup')
    parser.add_argument('--stft-hop-length', type=int, default=256,
                        help='STFT hop length for estimating audio length from mel size')


    return parser


def load_checkpoint(checkpoint_path, model_name):
    assert os.path.isfile(checkpoint_path)

    print("Loading checkpoint '{}'".format(checkpoint_path))
    checkpoint_dict = torch.load(checkpoint_path, map_location='cpu')
    model.load_state_dict(checkpoint_dict['state_dict'])
    print("Loaded '{}' checkpoint '{}'" .format(model_name, checkpoint_path))
    return model


def checkpoint_from_distributed(state_dict):
    """
    Checks whether checkpoint was generated by DistributedDataParallel. DDP
    wraps model in additional "module.", it needs to be unwrapped for single
    GPU inference.
    :param state_dict: model's state dict
    """
    ret = False
    for key, _ in state_dict.items():
        if key.find('module.') != -1:
            ret = True
            break
    return ret


def unwrap_distributed(state_dict):
    """
    Unwraps model from DistributedDataParallel.
    DDP wraps model in additional "module.", it needs to be removed for single
    GPU inference.
    :param state_dict: model's state dict
    """
    new_state_dict = {}
    for key, value in state_dict.items():
        new_key = key.replace('module.', '')
        new_state_dict[new_key] = value
    return new_state_dict


def load_and_setup_model(model_name, parser, checkpoint, amp_run):
    model_parser = models.parse_model_args(model_name, parser, add_help=False)
    model_args, _ = model_parser.parse_known_args()

    model_config = models.get_model_config(model_name, model_args)
    model = models.get_model(model_name, model_config, to_cuda=True)

    if checkpoint is not None:
        state_dict = torch.load(checkpoint)['state_dict']
        if checkpoint_from_distributed(state_dict):
            state_dict = unwrap_distributed(state_dict)

        model.load_state_dict(state_dict)

    if model_name == "WaveGlow":
        model = model.remove_weightnorm(model)

    model.eval()

    if amp_run:
        model, _ = amp.initialize(model, [], opt_level="O3")

    return model


# taken from tacotron2/data_function.py:TextMelCollate.__call__
def pad_sequences(batch):
    # Right zero-pad all one-hot text sequences to max input length
    input_lengths, ids_sorted_decreasing = torch.sort(
        torch.LongTensor([len(x) for x in batch]),
        dim=0, descending=True)
    max_input_len = input_lengths[0]

    text_padded = torch.LongTensor(len(batch), max_input_len)
    text_padded.zero_()
    for i in range(len(ids_sorted_decreasing)):
        text = batch[ids_sorted_decreasing[i]]
        text_padded[i, :text.size(0)] = text

    return text_padded, input_lengths


def prepare_input_sequence(texts):

    d = []
    for i,text in enumerate(texts):
        d.append(torch.IntTensor(
            text_to_sequence(text, ['english_cleaners'])[:]))

    text_padded, input_lengths = pad_sequences(d)
    if torch.cuda.is_available():
        text_padded = torch.autograd.Variable(text_padded).cuda().long()
        input_lengths = torch.autograd.Variable(input_lengths).cuda().long()
    else:
        text_padded = torch.autograd.Variable(text_padded).long()
        input_lengths = torch.autograd.Variable(input_lengths).long()

    return text_padded, input_lengths


class MeasureTime():
    def __init__(self, measurements, key):
        self.measurements = measurements
        self.key = key

    def __enter__(self):
        torch.cuda.synchronize()
        self.t0 = time.perf_counter()

    def __exit__(self, exc_type, exc_value, exc_traceback):
        torch.cuda.synchronize()
        self.measurements[self.key] = time.perf_counter() - self.t0


def main():
    """
    Launches text to speech (inference).
    Inference is executed on a single GPU.
    """
    parser = argparse.ArgumentParser(
        description='PyTorch Tacotron 2 Inference')
    parser = parse_args(parser)
    args, _ = parser.parse_known_args()

    LOGGER.set_model_name("Tacotron2_PyT")
    LOGGER.set_backends([
        dllg.StdOutBackend(log_file=None,
                           logging_scope=dllg.TRAIN_ITER_SCOPE, iteration_interval=1),
        dllg.JsonBackend(log_file=args.log_file,
                         logging_scope=dllg.TRAIN_ITER_SCOPE, iteration_interval=1)
    ])
    LOGGER.register_metric("tacotron2_items_per_sec", metric_scope=dllg.TRAIN_ITER_SCOPE)
    LOGGER.register_metric("tacotron2_latency", metric_scope=dllg.TRAIN_ITER_SCOPE)
    LOGGER.register_metric("waveglow_items_per_sec", metric_scope=dllg.TRAIN_ITER_SCOPE)
    LOGGER.register_metric("waveglow_latency", metric_scope=dllg.TRAIN_ITER_SCOPE)
    LOGGER.register_metric("latency", metric_scope=dllg.TRAIN_ITER_SCOPE)

    log_hardware()
    log_args(args)

    tacotron2 = load_and_setup_model('Tacotron2', parser, args.tacotron2,
                                     args.amp_run)
    waveglow = load_and_setup_model('WaveGlow', parser, args.waveglow,
                                    args.amp_run)

    texts = []
    try:
        f = open(args.input, 'r')
        texts = f.readlines()
    except:
        print("Could not read file")
        sys.exit(1)

    if args.include_warmup:
        sequence = torch.randint(low=0, high=148, size=(1,50),
                                 dtype=torch.long).cuda()
        input_lengths = torch.IntTensor([sequence.size(1)]).cuda().long()
        for i in range(3):
            with torch.no_grad():
                _, mel, _, _, mel_lengths = tacotron2.infer(sequence, input_lengths)
                _ = waveglow.infer(mel)

    LOGGER.iteration_start()

    measurements = {}

    sequences_padded, input_lengths = prepare_input_sequence(texts)

    with torch.no_grad(), MeasureTime(measurements, "tacotron2_time"):
        _, mel, _, _, mel_lengths = tacotron2.infer(sequences_padded, input_lengths)

    with torch.no_grad(), MeasureTime(measurements, "waveglow_time"):
        audios = waveglow.infer(mel, sigma=args.sigma_infer)
        audios = audios.float()

    tacotron2_infer_perf = mel.size(0)*mel.size(2)/measurements['tacotron2_time']
    waveglow_infer_perf = audios.size(0)*audios.size(1)/measurements['waveglow_time']

    LOGGER.log(key="tacotron2_items_per_sec", value=tacotron2_infer_perf)
    LOGGER.log(key="tacotron2_latency", value=measurements['tacotron2_time'])
    LOGGER.log(key="waveglow_items_per_sec", value=waveglow_infer_perf)
    LOGGER.log(key="waveglow_latency", value=measurements['waveglow_time'])
    LOGGER.log(key="latency", value=(measurements['tacotron2_time']+
                                     measurements['waveglow_time']))

    for i, audio in enumerate(audios):
        audio_path = args.output + "audio_"+str(i)+".wav"
        write(audio_path, args.sampling_rate,
              audio.data.cpu().numpy()[:mel_lengths[i]*args.stft_hop_length])

    LOGGER.iteration_stop()
    LOGGER.finish()

if __name__ == '__main__':
    main()
