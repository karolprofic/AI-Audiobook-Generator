import array
import os
import shutil
import wave
import soundfile
from ttsmms import TTS, download
from datetime import datetime


class AudiobookGenerator:
    def __init__(self, input_file, output_folder, language):
        # Input
        self.input_file = input_file
        self.output_folder = output_folder
        self.language = language

        # Values
        self.finish = False
        self.start_time = None
        self.end_time = None
        self.paragraphs = []
        self.total_paragraphs = 0
        self.processed_paragraphs = 0
        self.status = ""

    def start(self):
        """
        Start the audiobook generation process.
        """
        self.finish = False
        self.start_time = datetime.now()

        method_order = ["clear", "load_file", "generate_audio", "merge_audio"]
        for method in method_order:
            result = getattr(self, method)()
            if result != 0:
                return result

        self.end_time = datetime.now()
        self.change_status('Audiobook generated successfully')
        return 0

    def clear(self):
        """
        Clear the output folder and prepare for audiobook generation.
        """
        output_path = os.path.join(self.output_folder, "output")
        slices_path = os.path.join(output_path, "slices")

        # Remove output folder if exist
        try:
            shutil.rmtree(output_path)
        except OSError as e:
            return self.change_status(f'Error while cleaning output folder "{output_path}": {e}')

        # Create now, empty output folder
        try:
            os.makedirs(output_path)
            os.makedirs(slices_path)
        except OSError as e:
            return self.change_status(f'Error while creating output folder "{output_path}": {e}')

        return 0

    def load_file(self):
        """
        Load paragraphs from the input file.
        """
        try:
            with open(self.input_file, 'r', encoding='utf-8') as file:
                text = file.read()
            self.paragraphs = text.split('\n')
            self.total_paragraphs = len(self.paragraphs)
        except FileNotFoundError:
            return self.change_status(f"Error: File '{self.input_file}' not found.")
        except UnicodeDecodeError:
            return self.change_status(f"Error: Unable to read the file '{self.input_file}' with utf-8 encoding.")
        except Exception as e:
            return self.change_status(f"Error: {e}")

        return 0

    def change_status(self, status):
        """
        Change the status of the audiobook generation process.
        """
        self.status = status
        self.finish = True
        return 1

    @staticmethod
    def create_silent_file(filepath, duration):
        """
        Create a silent audio file when paragraphs is empty.
        Audio length is provided in seconds as duration parameters.
        """
        sample_width = 2
        frame_rate = 44100
        with wave.open(filepath, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(sample_width)
            wav_file.setframerate(frame_rate)
            wav_file.setnframes(int(frame_rate * duration))
            empty_data = array.array('h', [0] * int(frame_rate * duration))
            wav_file.writeframes(empty_data.tobytes())

    @staticmethod
    def resample_file(filepath):
        """
        Resample the audio file to be compliant with PCM 16 bit.
        """
        data, samplerate = soundfile.read(filepath)
        soundfile.write(filepath, data, samplerate, subtype='PCM_16')

    def generate_audio(self):
        """
        Generate audio files for each paragraph using TTS.
        """
        output_path = os.path.join(self.output_folder, "output", "slices")
        model_path = download(self.language, "./data")
        tts = TTS(model_path)

        for i in range(0, self.total_paragraphs):
            filepath = os.path.join(output_path, f"{i}.wav")
            if len(self.paragraphs[i]) > 0:
                print(f"{i} of {self.total_paragraphs} | len {len(self.paragraphs[i])}")
                tts.synthesis(self.paragraphs[i], wav_path=filepath)
                self.resample_file(filepath)
            else:
                self.create_silent_file(filepath, 1)
                self.resample_file(filepath)
            self.processed_paragraphs = i + 1

        return 0

    def merge_audio(self):
        """
        Merge individual audio files into a single audiobook file.
        """
        output_path = os.path.join(self.output_folder, "output", "slices")
        output_file = os.path.join(self.output_folder, "output", "audiobook.wav")

        with wave.open(output_file, 'wb') as wav_out:
            for i in range(0, self.total_paragraphs):
                filepath = os.path.join(output_path, f"{i}.wav")
                with wave.open(filepath, 'rb') as wav_in:
                    if not wav_out.getnframes():
                        wav_out.setparams(wav_in.getparams())
                    wav_out.writeframes(wav_in.readframes(wav_in.getnframes()))

        return 0

    def progress(self):
        """
        Calculate the progress value of audiobook generation in percentages.
        """
        try:
            result = round((self.processed_paragraphs / self.total_paragraphs) * 100)
        except ZeroDivisionError:
            result = 0

        if result == 100 and not self.finish:
            return 99

        return result

    def summary(self):
        """
        Provide information about the generation process after it is finished.
        """
        if not self.finish:
            return "The generation of the audiobook has not yet been completed."

        minutes_elapsed = 0.0
        audio_filepath = os.path.join(self.output_folder, "output", "audiobook.wav")
        if self.start_time and self.end_time:
            duration = self.end_time - self.start_time
            seconds_elapsed = duration.total_seconds()
            minutes_elapsed = round(seconds_elapsed / 60, 1)

        return (f"Audiobook generation completed!\n"
                f"Path: {audio_filepath}\n"
                f"Time elapsed: {minutes_elapsed} minutes\n")
