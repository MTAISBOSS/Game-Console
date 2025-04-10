import board
import pwmio
import asyncio

class MelodyPlayer:
    def __init__(self):
        self.NOTE_B0 = 31
        self.NOTE_C1 = 33
        self.NOTE_CS1 = 35
        self.NOTE_D1 = 37
        self.NOTE_DS1 = 39
        self.NOTE_E1 = 41
        self.NOTE_F1 = 44
        self.NOTE_FS1 = 46
        self.NOTE_G1 = 49
        self.NOTE_GS1 = 52
        self.NOTE_A1 = 55
        self.NOTE_AS1 = 58
        self.NOTE_B1 = 62
        self.NOTE_C2 = 65
        self.NOTE_CS2 = 69
        self.NOTE_D2 = 73
        self.NOTE_DS2 = 78
        self.NOTE_E2 = 82
        self.NOTE_F2 = 87
        self.NOTE_FS2 = 93
        self.NOTE_G2 = 98
        self.NOTE_GS2 = 104
        self.NOTE_A2 = 110
        self.NOTE_AS2 = 117
        self.NOTE_B2 = 123
        self.NOTE_C3 = 131
        self.NOTE_CS3 = 139
        self.NOTE_D3 = 147
        self.NOTE_DS3 = 156
        self.NOTE_E3 = 165
        self.NOTE_F3 = 175
        self.NOTE_FS3 = 185
        self.NOTE_G3 = 196
        self.NOTE_GS3 = 208
        self.NOTE_A3 = 220
        self.NOTE_AS3 = 233
        self.NOTE_B3 = 247
        self.NOTE_C4 = 262
        self.NOTE_CS4 = 277
        self.NOTE_D4 = 294
        self.NOTE_DS4 = 311
        self.NOTE_E4 = 330
        self.NOTE_F4 = 349
        self.NOTE_FS4 = 370
        self.NOTE_G4 = 392
        self.NOTE_GS4 = 415
        self.NOTE_A4 = 440
        self.NOTE_AS4 = 466
        self.NOTE_B4 = 494
        self.NOTE_C5 = 523
        self.NOTE_CS5 = 554
        self.NOTE_D5 = 587
        self.NOTE_DS5 = 622
        self.NOTE_E5 = 659
        self.NOTE_F5 = 698
        self.NOTE_FS5 = 740
        self.NOTE_G5 = 784
        self.NOTE_GS5 = 831
        self.NOTE_A5 = 880
        self.NOTE_AS5 = 932
        self.NOTE_B5 = 988
        self.NOTE_C6 = 1047
        self.NOTE_CS6 = 1109
        self.NOTE_D6 = 1175
        self.NOTE_DS6 = 1245
        self.NOTE_E6 = 1319
        self.NOTE_F6 = 1397
        self.NOTE_FS6 = 1480
        self.NOTE_G6 = 1568
        self.NOTE_GS6 = 1661
        self.NOTE_A6 = 1760
        self.NOTE_AS6 = 1865
        self.NOTE_B6 = 1976
        self.NOTE_C7 = 2093
        self.NOTE_CS7 = 2217
        self.NOTE_D7 = 2349
        self.NOTE_DS7 = 2489
        self.NOTE_E7 = 2637
        self.NOTE_F7 = 2794
        self.NOTE_FS7 = 2960
        self.NOTE_G7 = 3136
        self.NOTE_GS7 = 3322
        self.NOTE_A7 = 3520
        self.NOTE_AS7 = 3729
        self.NOTE_B7 = 3951
        self.NOTE_C8 = 4186
        self.NOTE_CS8 = 4435
        self.NOTE_D8 = 4699
        self.NOTE_DS8 = 4978
        self.REST = 0

        # Melody and durations
        self.melody = [
            self.NOTE_E5, 4, self.NOTE_B4, 8, self.NOTE_C5, 8, self.NOTE_D5, 4, self.NOTE_C5, 8, self.NOTE_B4, 8,
            self.NOTE_A4, 4, self.NOTE_A4, 8, self.NOTE_C5, 8, self.NOTE_E5, 4, self.NOTE_D5, 8, self.NOTE_C5, 8,
            self.NOTE_B4, -4, self.NOTE_C5, 8, self.NOTE_D5, 4, self.NOTE_E5, 4,
            self.NOTE_C5, 4, self.NOTE_A4, 4, self.NOTE_A4, 8, self.NOTE_A4, 4, self.NOTE_B4, 8, self.NOTE_C5, 8,
            self.NOTE_D5, -4, self.NOTE_F5, 8, self.NOTE_A5, 4, self.NOTE_G5, 8, self.NOTE_F5, 8,
            self.NOTE_E5, -4, self.NOTE_C5, 8, self.NOTE_E5, 4, self.NOTE_D5, 8, self.NOTE_C5, 8,
            self.NOTE_B4, 4, self.NOTE_B4, 8, self.NOTE_C5, 8, self.NOTE_D5, 4, self.NOTE_E5, 4,
            self.NOTE_C5, 4, self.NOTE_A4, 4, self.NOTE_A4, 4, self.REST, 4,
        ]

        # Tempo of the song
        self.tempo = 168

        # Initialize PWM for the buzzer
        self.buzzer = board.GP0  # Change this to your desired pin
        self.pwm = pwmio.PWMOut(self.buzzer, duty_cycle=0, frequency=440, variable_frequency=True)
        
    async def play_tone(frequency, duration):
        self.buzzer.frequency = frequency
        self.buzzer.duty_cycle = 32768  # 50% duty cycle
        await asyncio.sleep(duration)
        self.buzzer.duty_cycle = 0  # Turn off the buzzer

    async def play_melody(self):
        while True:  # Loop the melody indefinitely
            # Calculate the duration of a whole note in milliseconds
            wholenote = (60000 * 4) / self.tempo

            # Play the melody
            for i in range(0, len(self.melody), 2):
                note = self.melody[i]
                duration = self.melody[i + 1]

                if note == self.REST:
                    self.pwm.duty_cycle = 0
                else:
                    self.pwm.frequency = note
                    self.pwm.duty_cycle = 32768  # 50% duty cycle

                # Calculate the note duration in milliseconds
                note_duration = wholenote / abs(duration)

                # Wait for the note duration
                await asyncio.sleep(note_duration / 1000)

                # Stop the note
                self.pwm.duty_cycle = 0

                # Short pause between notes
                await asyncio.sleep(0.02)