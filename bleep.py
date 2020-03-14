"""
ɪ (.venv) bleepbloop › python bleep.py; play wavy.wav
"""


from math import gcd, pi

import numpy as np
from scipy.io.wavfile import write

from utility import SAMPLE_RATE, limit_amplitude


class SoundGenerator:

    # Constants
    def __init__(self, wave_type="Sine", frequency=500, amplitude=1.0, duration=5):

        # Initialize Internal Variables
        self.wave_type = str(wave_type)
        self.frequency = float(frequency)
        self.amplitude = limit_amplitude(amplitude)
        self.duration = float(duration)
        self.sample_count = self.get_sample_count()
        self.sound = np.array([])
        self.limit = np.vectorize(limit_amplitude)

        # Generate Sound
        if wave_type == "Sine":
            self.sound = self.generate_sine_wave()
        elif wave_type == "Square":
            self.sound = self.generate_square_wave()
        elif wave_type == "Sawtooth":
            self.sound = self.generate_sawtooth_wave()
        elif wave_type == "Constant":
            self.sound = self.generate_constant_wave()
        elif wave_type == "Noise":
            self.sound = self.generate_white_noise_wave()
        elif wave_type == "Combination":
            self.sound = self.sound

    def get_sample_count(self):
        return int(self.duration * SAMPLE_RATE)

    def get_single_phase_array(self):
        single_cycle_length = SAMPLE_RATE / float(self.frequency)
        omega = pi * 2 / single_cycle_length
        phase_array = np.arange(0, int(single_cycle_length)) * omega
        return phase_array

    def generate_sine_wave(self):
        # Get Phase Array
        phase_array = self.get_single_phase_array()
        # Compute Sine Values and scale by amplitude
        single_cycle = self.amplitude * np.sin(phase_array)
        # Resize to match duration
        return np.resize(single_cycle, (self.sample_count,)).astype(np.float)

    def generate_square_wave(self):
        # Use the fact that sign of sine is square wave and scale by amplitude
        return self.amplitude * np.sign(self.generate_sine_wave())

    def generate_sawtooth_wave(self):
        # Get Phase Array
        phase_array = self.get_single_phase_array()
        # Compute Saw Values and scale by amplitude
        pi_inverse = 1 / pi
        saw = np.vectorize(lambda x: 1 - pi_inverse * x)
        single_cycle = self.amplitude * saw(phase_array)
        # Resize to match duration
        return np.resize(single_cycle, (self.sample_count,)).astype(np.float)

    def generate_constant_wave(self):
        # Get Phase Array
        # phase_array = self.get_single_phase_array()
        # Assign to amplitude
        single_cycle = self.amplitude
        # Resize to match duration
        return np.resize(single_cycle, (self.sample_count,)).astype(np.float)

    def generate_white_noise_wave(self):
        # Random samples between -1 and 1
        return np.random.uniform(-1, 1, self.get_sample_count())

    def combine_sounds(self, sound_obj, operator="+"):
        # Figure out which is the longer sound
        if len(self.sound) < len(sound_obj.get_sound()):
            min_sound = np.copy(self.get_sound())
            max_sound = np.copy(sound_obj.get_sound())
        else:
            max_sound = np.copy(self.get_sound())
            min_sound = np.copy(sound_obj.get_sound())

        # Perform appropriate operation
        if operator == "+":
            max_sound[0 : len(min_sound)] = max_sound[0 : len(min_sound)] + min_sound
        elif operator == "-":
            max_sound[0 : len(min_sound)] = max_sound[0 : len(min_sound)] - min_sound
        elif operator == "*":
            max_sound[0 : len(min_sound)] = max_sound[0 : len(min_sound)] * min_sound

        # Limite sound values to within -1 and +1
        new_sound = self.limit(max_sound)

        # Calculate metadata for new sound
        new_frequency = (
            int(self.get_frequency())
            * int(sound_obj.get_frequency())
            / gcd(int(self.get_frequency()), int(sound_obj.get_frequency()))
        )
        new_duration = float(len(new_sound)) / SAMPLE_RATE
        new_amplitude = np.max(new_sound)

        # Create new sound object and return object
        return_obj = SoundGenerator(
            wave_type="Combination",
            frequency=new_frequency,
            amplitude=new_amplitude,
            duration=new_duration,
        )

        # Set sound value to new_sound
        return_obj.set_sound(new_sound)
        return return_obj

    def __add__(self, sound_obj):
        return self.combine_sounds(sound_obj, "+")

    def __sub__(self, sound_obj):
        return self.combine_sounds(sound_obj, "-")

    def __mul__(self, sound_obj):
        if isinstance(sound_obj, int) or isinstance(sound_obj, float):
            scale_factor = limit_amplitude(sound_obj)
            if scale_factor < 0:
                scale_factor = 0.0
            return_obj = SoundGenerator(
                self.wave_type,
                self.frequency,
                self.amplitude * scale_factor,
                self.duration,
            )
            sound = self.get_sound()
            return_obj.set_sound(sound * scale_factor)
            return return_obj
        return self.combine_sounds(sound_obj, "*")

    def __xor__(self, sound_obj):

        # Join two sound pieces together
        new_sound = np.append(self.get_sound(), sound_obj.get_sound())

        # Calculate metadata for new sound
        new_frequency = (
            int(self.get_frequency())
            * int(sound_obj.get_frequency())
            / gcd(int(self.get_frequency()), int(sound_obj.get_frequency()))
        )
        new_duration = self.get_duration() + sound_obj.get_duration()
        new_amplitude = np.max(new_sound)

        # Create new sound object and return object
        return_obj = SoundGenerator(
            wave_type="Join",
            frequency=new_frequency,
            amplitude=new_amplitude,
            duration=new_duration,
        )

        # Set sound value to new_sound
        return_obj.set_sound(new_sound)
        return return_obj

    def __pow__(self, sound_obj):
        # Figure out which is the longer sound
        if len(self.sound) < len(sound_obj.get_sound()):
            min_sound = np.copy(self.get_sound())
            max_sound = np.copy(sound_obj.get_sound())

        else:
            max_sound = np.copy(self.get_sound())
            min_sound = np.copy(sound_obj.get_sound())
        min_sound = np.resize(min_sound, (len(max_sound),))
        # new_frequency = int(self.get_frequency()) * int(sound_obj.get_frequency()) / gcd(int(self.get_frequency()), int(sound_obj.get_frequency()))
        new_duration = float(len(max_sound)) / SAMPLE_RATE
        # Frequency does not matter here
        min_sound_obj = SoundGenerator(
            wave_type="Temp",
            frequency=100,
            amplitude=np.max(min_sound),
            duration=new_duration,
        )
        min_sound_obj.set_sound(min_sound)
        max_sound_obj = SoundGenerator(
            wave_type="Temp",
            frequency=100,
            amplitude=np.max(max_sound),
            duration=new_duration,
        )
        max_sound_obj.set_sound(max_sound)
        return min_sound_obj * max_sound_obj

    def __str__(self):
        return (
            "WT: "
            + self.wave_type
            + " F: "
            + str(self.frequency)
            + " A: "
            + str(self.amplitude)
            + " D: "
            + str(self.duration)
        )

    def get_sound(self):
        return self.sound

    def set_sound(self, sound_array):
        self.sound = sound_array

    def get_frequency(self):
        return self.frequency

    def get_duration(self):
        return self.duration

    def shift_by(self, number_of_samples):
        sound = self.get_sound()
        sound = np.roll(sound, number_of_samples)
        sound = np.append(np.zeros(number_of_samples), sound[number_of_samples:])
        ret_sound_obj = SoundGenerator(
            self.wave_type, self.frequency, self.amplitude, self.duration
        )
        ret_sound_obj.set_sound(sound)
        return ret_sound_obj


def main():
    sin1 = SoundGenerator(wave_type="Sine", duration=3.0)
    sqr1 = SoundGenerator(
        wave_type="Square", frequency=400.0, amplitude=0.2, duration=3.0
    )
    sqr2 = SoundGenerator(
        wave_type="Square", frequency=500.0, amplitude=0.2, duration=3.0
    )
    saw1 = SoundGenerator(wave_type="Sawtooth", duration=3)

    note1 = SoundGenerator(
        wave_type="Square", frequency=400.0, amplitude=0.2, duration=5.0
    )
    note2 = SoundGenerator(
        wave_type="Square", frequency=450.0, amplitude=0.2, duration=5.0
    )
    note3 = SoundGenerator(
        wave_type="Square", frequency=600.0, amplitude=0.2, duration=5.0
    )
    note4 = SoundGenerator(
        wave_type="Square", frequency=700.0, amplitude=0.1, duration=5.0
    )
    note5 = SoundGenerator(
        wave_type="Square", frequency=800.0, amplitude=0.1, duration=5.0
    )

    chord1 = note1 + note2 + note3 + (note4 * 0.5) + note5

    join1 = sin1 ^ sqr1 ^ sqr2 ^ saw1 ^ chord1
    mod1 = SoundGenerator(
        wave_type="Square", frequency=3.0, amplitude=1.0, duration=3.0
    )
    modjoin1 = mod1 ** join1
    print(modjoin1.get_sound())
    final = np.asarray(modjoin1.get_sound() * 10000, dtype=np.int16)
    print(final)
    write("wavy.wav", SAMPLE_RATE, final)
    # write(SAMPLE_RATE modjoin1, "modjoin1")


def main2():
    fs = 1000
    t = np.linspace(0.0, 1.0, SAMPLE_RATE)
    amplitude = np.iinfo(np.int16).max
    data = amplitude * np.sin(2.0 * np.pi * fs * t)
    print(data)
    data2 = np.asarray(data, dtype=np.int16)
    print(data2)
    write("example.wav", SAMPLE_RATE, data2)


if __name__ == "__main__":
    main()
    main2()
