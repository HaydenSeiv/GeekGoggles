import math
import random
import os
import string
from collections import  deque
import sys
import csv
import statistics
from matplotlib import pyplot as plt
import whisper










# main
if __name__ == "__main__":
    model  = whisper.load_model("base")
    result  = model.transcribe("recording_20250409_095750.wav")
    print(result["text"])

