import numpy as np
import pyaudio
import wave
import curses
import io
from pydub import AudioSegment
import sys
import time

# Initial configuration
CHUNK_SIZE = 1024  # Chunk size for audio processing
FORMAT = pyaudio.paInt16  # Audio format
CHANNELS = 2  # Number of audio channels
RATE = 44100  # Sampling rate
FFT_UPDATE_FREQ = 4  # Perform FFT every 4 chunks for visualization optimization

# Function to open audio file (supports both WAV and MP3)
def open_audio_file(filename):
    if filename.endswith('.mp3'):
        audio = AudioSegment.from_mp3(filename)
        audio = audio.set_channels(CHANNELS)
        audio = audio.set_frame_rate(RATE)
        # Convert audio to WAV format in-memory
        audio_data = io.BytesIO()
        audio.export(audio_data, format='wav')
        audio_data.seek(0)  # Go to the beginning of the IO object
        return wave.open(audio_data, 'rb')
    else:
        return wave.open(filename, 'rb')

# Placeholder for audio file path, replace 'path_to_your_audio_file.mp3' with a direct path to your file for testing
audio_file_path = sys.argv[1]
wave_file = open_audio_file(audio_file_path)

# Initialize PyAudio
p = pyaudio.PyAudio()

# Open the stream for audio playback
stream = p.open(format=p.get_format_from_width(wave_file.getsampwidth()),
                channels=wave_file.getnchannels(),
                rate=wave_file.getframerate(),
                output=True)

def init_colors():
    """Initialize color pairs for visualization."""
    curses.start_color()
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)  # Green text on black background
    curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLACK)  # White text on black background


def visualize_spectrum(stdscr, data, start_time, total_frames, wave_file, audio_file_path):
    """Visualize the audio spectrum and playback progress with adjusted bar heights."""
    global CHUNK_SIZE, RATE

    stdscr.clear()
    height, width = stdscr.getmaxyx()

    # Reserved lines for top information (music name, time, progress)
    top_info_height = 4  # Number of lines at the top reserved for displaying information

    # Display music name using white color
    music_name = audio_file_path
    stdscr.addstr(0, 0, f"Music: {music_name}", curses.color_pair(2))

    # Display time and progress using white color
    elapsed_time = time.time() - start_time
    total_seconds = total_frames / wave_file.getframerate()
    stdscr.addstr(1, 0, "Time: " + time.strftime('%M:%S', time.gmtime(elapsed_time)) + f" / {int(total_seconds // 60):02d}:{int(total_seconds % 60):02d}", curses.color_pair(2))

    progress_width = max(20, width - 20)
    progress = int((elapsed_time / total_seconds) * progress_width)
    progress_bar = '[' + '#' * progress + ' ' * (progress_width - progress) + ']'
    stdscr.addstr(2, 0, "Progress: " + progress_bar, curses.color_pair(2))

    # FFT visualization adjusted for top info space
    audio_data = np.frombuffer(data, dtype=np.int16)
    fft_data = np.abs(np.fft.fft(audio_data)[:CHUNK_SIZE // 2])
    fft_normalized = fft_data / np.max(fft_data) if np.max(fft_data) > 0 else np.zeros_like(fft_data)

    # Calculate visualization parameters
    bar_width = max(1, int(width / len(fft_normalized)))
    available_height = height - top_info_height  # Available height for bars

    for i in range(0, len(fft_normalized)):
        magnitude = fft_normalized[i]
        bar_height = int(magnitude * (available_height - 1))  # Leave space at the bottom

        for y in range(bar_height):
            try:
                # Draw each bar in green, adjusting for the reserved top info height
                stdscr.addch(height - 2 - y, i * bar_width, '|', curses.color_pair(1))
            except curses.error:
                # Skip errors related to drawing outside of the screen bounds
                pass

    stdscr.refresh()


def main(stdscr):
    """Main function for audio playback and visualization."""
    init_colors()
    start_time = time.time()
    total_frames = wave_file.getnframes()
    fft_frame_counter = 0
    audio_file_path = sys.argv[1]

    while True:
        data = wave_file.readframes(CHUNK_SIZE)
        if len(data) == 0:  # If no more data is available, break out of the loop
            break

        stream.write(data)

        if fft_frame_counter % FFT_UPDATE_FREQ == 0:
            visualize_spectrum(stdscr, data, start_time, total_frames, wave_file, audio_file_path)
        fft_frame_counter += 1

if __name__ == '__main__':
    curses.wrapper(main)
    wave_file.close()
    stream.stop_stream()
    stream.close()
    p.terminate()
