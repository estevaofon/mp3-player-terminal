import numpy as np
import pyaudio
import wave
import curses
import io
from pydub import AudioSegment
import sys
import time

# Define a class for audio visualization
class AudioVisualizer:
    def __init__(self, filepath):
        # Constructor initializes the audio file path and basic settings
        self.filepath = filepath
        self.chunk_size = 1024  # Size of data chunks to read and process
        self.format = pyaudio.paInt16  # Audio format for PyAudio
        self.channels = 2  # Number of audio channels (e.g., stereo)
        self.rate = 44100  # Sample rate (frequency of samples per second)
        self.fft_update_freq = 4  # Frequency of FFT calculations for visualization
        self.audio_file = self.open_audio_file(filepath)  # Open the audio file
        self.pyaudio_instance = pyaudio.PyAudio()  # Create a PyAudio instance
        self.stream = self.open_audio_stream()  # Open the audio stream for playback

    def open_audio_file(self, filepath):
        # Opens an audio file and converts it to WAV format if necessary
        if filepath.endswith('.mp3'):
            # If the file is an MP3, convert it to WAV format
            audio = AudioSegment.from_mp3(filepath).set_channels(self.channels).set_frame_rate(self.rate)
            audio_data = io.BytesIO()
            audio.export(audio_data, format='wav')
            audio_data.seek(0)
            return wave.open(audio_data, 'rb')
        else:
            # If the file is already a WAV, open it directly
            return wave.open(filepath, 'rb')

    def open_audio_stream(self):
        # Opens an audio stream for playback
        return self.pyaudio_instance.open(format=self.pyaudio_instance.get_format_from_width(self.audio_file.getsampwidth()),
                                          channels=self.audio_file.getnchannels(),
                                          rate=self.audio_file.getframerate(),
                                          output=True)

    @staticmethod
    def init_colors():
        # Initializes color pairs for visual output in the terminal
        curses.start_color()
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)  # Green for the spectrum bars
        curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLACK)  # White for text

    def visualize_spectrum(self, stdscr, data, start_time):
        # Visualizes the audio spectrum on the terminal
        stdscr.clear()  # Clear the terminal
        height, width = stdscr.getmaxyx()  # Get terminal size
        top_info_height = 4  # Reserved space at the top for information

        # Display the music name
        music_name = self.filepath
        stdscr.addstr(0, 0, f"Music: {music_name}", curses.color_pair(2))

        # Calculate and display elapsed time and total duration
        elapsed_time = time.time() - start_time
        total_seconds = self.audio_file.getnframes() / self.audio_file.getframerate()
        self.display_time_and_progress(stdscr, elapsed_time, total_seconds, width)

        # Perform FFT on the audio data and draw the spectrum bars
        fft_data = self.calculate_fft(data)
        self.draw_bars(stdscr, fft_data, height, width, top_info_height)
        stdscr.refresh()

    def display_time_and_progress(self, stdscr, elapsed_time, total_seconds, width):
        # Displays the playback time and progress bar
        stdscr.addstr(1, 0, "Time: " + time.strftime('%M:%S', time.gmtime(elapsed_time)) +
                      f" / {int(total_seconds // 60):02d}:{int(total_seconds % 60):02d}", curses.color_pair(2))
        progress_bar = self.create_progress_bar(elapsed_time, total_seconds, width)
        stdscr.addstr(2, 0, "Progress: " + progress_bar, curses.color_pair(2))

    @staticmethod
    def create_progress_bar(elapsed_time, total_seconds, width):
        # Creates a progress bar string based on the current playback position
        progress_width = max(20, width - 20)
        progress = int((elapsed_time / total_seconds) * progress_width)
        return '[' + '#' * progress + ' ' * (progress_width - progress) + ']'

    def calculate_fft(self, data):
        # Calculates the FFT of the audio data for visualization
        audio_data = np.frombuffer(data, dtype=np.int16)
        fft_data = np.abs(np.fft.fft(audio_data)[:self.chunk_size // 2])
        return fft_data / np.max(fft_data) if np.max(fft_data) > 0 else np.zeros_like(fft_data)

    @staticmethod
    def draw_bars(stdscr, fft_data, height, width, top_info_height):
        # Draws the spectrum bars on the terminal
        bar_width = max(1, int(width / len(fft_data)))
        available_height = height - top_info_height
        for i, magnitude in enumerate(fft_data):
            bar_height = int(magnitude * (available_height - 1))
            for y in range(bar_height):
                try:
                    stdscr.addch(height - 2 - y, i * bar_width, '|', curses.color_pair(1))
                except curses.error:
                    # Ignore errors for drawing outside the screen bounds
                    pass

    def play_and_visualize(self, stdscr):
        # Main loop for audio playback and visualization
        self.init_colors()
        start_time = time.time()
        fft_frame_counter = 0

        while True:
            data = self.audio_file.readframes(self.chunk_size)
            if len(data) == 0:
                break  # Stop if there's no more data to read
            self.stream.write(data)  # Play the audio data
            # Update the visualization periodically based on the FFT update frequency
            if fft_frame_counter % self.fft_update_freq == 0:
                self.visualize_spectrum(stdscr, data, start_time)
            fft_frame_counter += 1

    def close_resources(self):
        # Closes all resources (audio file, stream, PyAudio)
        self.audio_file.close()
        self.stream.stop_stream()
        self.stream.close()
        self.pyaudio_instance.terminate()

def main(stdscr):
    # Entry point for the curses application
    filepath = sys.argv[1]  # Get the audio file path from command line arguments
    visualizer = AudioVisualizer(filepath)
    visualizer.play_and_visualize(stdscr)  # Start the visualization
    visualizer.close_resources()  # Clean up resources after visualization

if __name__ == '__main__':
    curses.wrapper(main)  # Initialize curses and call the main function
