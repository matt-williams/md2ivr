#!/usr/local/bin/python3

# Heavily based on https://github.com/mozilla/TTS/blob/master/notebooks/DDC_TTS_and_MultiBand_MelGAN_Example.ipynb

import time
import torch
import io
import numpy as np
import scipy

from TTS.tts.utils.generic_utils import setup_model
from TTS.utils.io import load_config
from TTS.tts.utils.text.symbols import symbols, phonemes
from TTS.utils.audio import AudioProcessor
from TTS.tts.utils.synthesis import synthesis
from TTS.vocoder.utils.generic_utils import setup_generator

# model paths
TTS_MODEL = "data/tts_model.pth.tar"
TTS_CONFIG = "data/config.json"
VOCODER_MODEL = "data/vocoder_model.pth.tar"
VOCODER_CONFIG = "data/config_vocoder.json"

# load configs
TTS_CONFIG = load_config(TTS_CONFIG)
VOCODER_CONFIG = load_config(VOCODER_CONFIG)

# load the audio processor
TTS_CONFIG.audio['stats_path'] = 'data/scale_stats.npy'
ap = AudioProcessor(**TTS_CONFIG.audio)

# LOAD TTS MODEL
# multi speaker
speaker_id = None
speakers = []

# load the model
num_chars = len(phonemes) if TTS_CONFIG.use_phonemes else len(symbols)
model = setup_model(num_chars, len(speakers), TTS_CONFIG)

# load model state
cp =  torch.load(TTS_MODEL, map_location=torch.device('cpu'))

# load the model
model.load_state_dict(cp['model'])
model.eval()

# set model stepsize
if 'r' in cp:
    model.decoder.set_r(cp['r'])

# LOAD VOCODER MODEL
vocoder_model = setup_generator(VOCODER_CONFIG)
vocoder_model.load_state_dict(torch.load(VOCODER_MODEL, map_location="cpu")["model"])
vocoder_model.remove_weight_norm()
vocoder_model.inference_padding = 0

ap_vocoder = AudioProcessor(**VOCODER_CONFIG['audio'])
vocoder_model.eval()

def text_to_speech(text):
    t_1 = time.time()
    waveform, alignment, mel_spec, mel_postnet_spec, stop_tokens, inputs = synthesis(model, text, TTS_CONFIG, False, ap, speaker_id, style_wav=None, truncated=False, enable_eos_bos_chars=TTS_CONFIG.enable_eos_bos_chars)
    # mel_postnet_spec = ap._denormalize(mel_postnet_spec.T)
    waveform = vocoder_model.inference(torch.FloatTensor(mel_postnet_spec.T).unsqueeze(0))
    waveform = waveform.flatten()
    waveform = waveform.numpy()
    waveform = (waveform * 32768).astype(np.int16, order='C')
    buf = io.BytesIO()
    scipy.io.wavfile.write(buf, TTS_CONFIG.audio['sample_rate'], waveform)
    audio = buf.read()
    print("Converted text \"{}\" to {:.2f}s / {}kB of audio".format(text[:40] + (text[40:] and "..."), len(waveform) / ap.sample_rate, len(audio) // 1024))
    return audio

if __name__ == "__main__":
    sentence =  "Bill got in the habit of asking himself “Is that thought true?” and if he wasn’t absolutely certain it was, he just let it go."
    audio = text_to_speech(sentence)
    with open('test.wav', 'wb') as f:
        f.write(audio)
