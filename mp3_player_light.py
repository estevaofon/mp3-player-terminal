import time
import os
import sys
import pygame
from mutagen.mp3 import MP3

if len(sys.argv) < 2:
    print("Usage: python script.py <path_to_mp3_file>")
    sys.exit(1)

song_file = sys.argv[1]

def play_mp3():
    pygame.init()
    pygame.mixer.init()
    pygame.mixer.music.load(song_file)
    pygame.mixer.music.play()

def time_elapsed(start_time, audio_length):
    elapsed_time = int(time.time() - start_time)
    minutes, seconds = divmod(elapsed_time, 60)
    total_minutes, total_seconds = divmod(audio_length, 60)
    time_str = '{:02d}:{:02d}'.format(minutes, seconds)
    total_time_str = '{:02d}:{:02d}'.format(total_minutes, total_seconds)
    return f'Time elapsed: {time_str} / Total time: {total_time_str}'

def progress_bar(current, total, start_time, audio_length, bar_length=50):
    percent = float(current) / total
    hashes = '#' * int(round(percent * bar_length))
    spaces = ' ' * (bar_length - len(hashes))
    progress = '[' + hashes + spaces + '] ' + time_elapsed(start_time, audio_length)
    print(progress, end='\r')

try:
    audio = MP3(song_file)
    audio_length = int(audio.info.length)
except Exception as e:
    print(f"Error loading MP3 file: {e}")
    sys.exit(1)

bar_length = 50
play_mp3()
os.system('cls' if os.name == 'nt' else 'clear')
print(f'Playing {song_file}')
start_time = time.time()

for i in range(audio_length):
    progress_bar(i, audio_length, start_time, audio_length, bar_length)
    time.sleep(1)

progress_bar(audio_length, audio_length, start_time, audio_length, bar_length)
print('\nDone.')
