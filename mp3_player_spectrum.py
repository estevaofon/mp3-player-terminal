import numpy as np
import pyaudio
import wave
import curses
import io
from pydub import AudioSegment
import sys
import time

class AudioVisualizer:
    def __init__(self, filepath):
        self.filepath = filepath
        self.chunk_size = 1024
        self.format = pyaudio.paInt16
        self.channels = 2
        self.rate = 44100
        self.fft_update_freq = 4
        self.audio_file = self.open_audio_file(filepath)
        self.pyaudio_instance = pyaudio.PyAudio()
        self.stream = self.open_audio_stream()

    def open_audio_file(self, filepath):
        if filepath.endswith('.mp3'):
            audio = AudioSegment.from_mp3(filepath).set_channels(self.channels).set_frame_rate(self.rate)
            audio_data = io.BytesIO()
            audio.export(audio_data, format='wav')
            audio_data.seek(0)
            return wave.open(audio_data, 'rb')
        else:
            return wave.open(filepath, 'rb')

    def open_audio_stream(self):
        return self.pyaudio_instance.open(format=self.pyaudio_instance.get_format_from_width(self.audio_file.getsampwidth()),
                                          channels=self.audio_file.getnchannels(),
                                          rate=self.audio_file.getframerate(),
                                          output=True)

    @staticmethod
    def init_colors():
        curses.start_color()
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLACK)

    def visualize_spectrum(self, stdscr, data, start_time):
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        top_info_height = 4

        music_name = self.filepath
        stdscr.addstr(0, 0, f"Music: {music_name}", curses.color_pair(2))

        elapsed_time = time.time() - start_time
        total_seconds = self.audio_file.getnframes() / self.audio_file.getframerate()
        self.display_time_and_progress(stdscr, elapsed_time, total_seconds, width)

        fft_data = self.calculate_fft(data)
        self.draw_bars(stdscr, fft_data, height, width, top_info_height)
        stdscr.refresh()

    def display_time_and_progress(self, stdscr, elapsed_time, total_seconds, width):
        stdscr.addstr(1, 0, "Time: " + time.strftime('%M:%S', time.gmtime(elapsed_time)) +
                      f" / {int(total_seconds // 60):02d}:{int(total_seconds % 60):02d}", curses.color_pair(2))
        progress_bar = self.create_progress_bar(elapsed_time, total_seconds, width)
        stdscr.addstr(2, 0, "Progress: " + progress_bar, curses.color_pair(2))

    @staticmethod
    def create_progress_bar(elapsed_time, total_seconds, width):
        progress_width = max(20, width - 20)
        progress = int((elapsed_time / total_seconds) * progress_width)
        return '[' + '#' * progress + ' ' * (progress_width - progress) + ']'

    def calculate_fft(self, data):
        audio_data = np.frombuffer(data, dtype=np.int16)
        fft_data = np.abs(np.fft.fft(audio_data)[:self.chunk_size // 2])
        return fft_data / np.max(fft_data) if np.max(fft_data) > 0 else np.zeros_like(fft_data)

    @staticmethod
    def draw_bars(stdscr, fft_data, height, width, top_info_height):
        bar_width = max(1, int(width / len(fft_data)))
        available_height = height - top_info_height
        for i, magnitude in enumerate(fft_data):
            bar_height = int(magnitude * (available_height - 1))
            for y in range(bar_height):
                try:
                    stdscr.addch(height - 2 - y, i * bar_width, '|', curses.color_pair(1))
                except curses.error:
                    pass

    def play_and_visualize(self, stdscr):
        self.init_colors()
        start_time = time.time()
        fft_frame_counter = 0

        while True:
            data = self.audio_file.readframes(self.chunk_size)
            if len(data) == 0:
                break
            self.stream.write(data)
            if fft_frame_counter % self.fft_update_freq == 0:
                self.visualize_spectrum(stdscr, data, start_time)
            fft_frame_counter += 1

    def close_resources(self):
        self.audio_file.close()
        self.stream.stop_stream()
        self.stream.close()
        self.pyaudio_instance.terminate()


def main(stdscr):
    filepath = sys.argv[1]
    visualizer = AudioVisualizer(filepath)
    visualizer.play_and_visualize(stdscr)
    visualizer.close_resources()

if __name__ == '__main__':
    curses.wrapper(main)
