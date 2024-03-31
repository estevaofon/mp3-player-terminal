from mutagen.mp3 import MP3
import time
import os
import sys

import pygame
song_file = sys.argv[1]

def play_mp3():
    pygame.mixer.init()
    pygame.mixer.music.load(song_file)
    pygame.mixer.music.play()

def time_elapsed():
    elapsed_time = int(time.time() - start_time)
    minutes, seconds = divmod(elapsed_time, 60)
    time_str = '{:02d}:{:02d}'.format(minutes, seconds)
    total_minutes, total_seconds = divmod(audio_length, 60)
    total_time_str = '{:02d}:{:02d}'.format(total_minutes, total_seconds)
    return f'Time elapsed: {time_str} / Total time: {total_time_str}'

def progress_bar(current, total, bar_length=50):
    """
    Display a progress bar in the terminal
    """
    percent = float(current) / total
    hashes = '#' * int(round(percent * bar_length))
    spaces = ' ' * (bar_length - len(hashes))
    progress = '[' + hashes + spaces + '] ' + time_elapsed()
    print(progress, end='\r')

# Open MP3 file
audio = MP3(song_file)

# Get audio length in seconds
audio_length = int(audio.info.length)

# Set up progress bar
bar_length = 50

# Play MP3 file
play_mp3()
os.system('cls')
print(f'Playing {song_file}')
start_time = time.time()
for i in range(audio_length):
    progress_bar(i, audio_length, bar_length)
    # Wait 1 second
    time.sleep(1)

# Finish progress bar
progress_bar(audio_length, audio_length, bar_length)
print('Done.')