import time
import array
import math
import board
import audiobusio
from ulab import numpy as np
import audiocore
import os
import board
import busio
import sdcardio
import storage
import digitalio

new_record = True
time_f = 1
mic = audiobusio.PDMIn(board.GP3, board.GP2, sample_rate=16000, bit_depth=16)
led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT

led.value = True
print("Process is starting")
time.sleep(60)


spi = busio.SPI(board.GP18, MOSI=board.GP19, MISO=board.GP16)
cs = board.GP27_A1

sdcard = sdcardio.SDCard(spi, cs)
vfs = storage.VfsFat(sdcard)
storage.mount(vfs, "/sd")
os.listdir("/sd/")


def mean(values):
    return sum(values) / len(values)

def normalized_rms(values):
    minbuf = int(mean(values))
    samples_sum = sum(
        float(sample - minbuf) * (sample - minbuf)
        for sample in values
    )

    return math.sqrt(samples_sum / len(values))

def numpy_add(main_array, add_array):
    main_array = list(main_array)
    main_array.append(add_array)
    return np.array(main_array)

def update_config_time():
    try:
        with open('/sd/config_time.txt', 'r+') as f:
            lines = f.readlines()
            time = int(lines[0])
            new_time = time + 1
            f.seek(0)
            f.write(str(new_time))
            f.flush()
    except:
        with open('/sd/config_time.txt', 'w') as f:
            f.write(str(2))
        time = 1

    return time
        
def update_time_interval():
    global new_record, time_f
    
    if new_record == True:
        time_f = 2
        new_record = False
    else:
        time_f += 1
        
    return time_f
        

def voice_record(minute, config_time, tour):
    global new_record, time_f, mic
    new_record = True
    
    seconds = minute * 60
    ses = np.array([])
    
    try:
        os.mkdir(f"/sd/records/{config_time}_{minute}")
    except:
        pass
     
    for i in range(int(seconds / tour)):
        
        samples = array.array('H', [0] * 200)
        ses = np.array([])
        start = time.time()
        if time_f % 2 == 0:
            led.value = True
        else:
            led.value = False

        while True:
            mic.record(samples, len(samples))
            magnitude = normalized_rms(samples)
            ses = numpy_add(ses, samples)
            stop = time.time()
            
            if (stop - start == tour):
                break
        np.save(f"/sd/records/{config_time}_{minute}/{config_time}_{minute}_{time_f}.npy", ses)
        print(f"Completed interval: {config_time}_{minute}_{time_f}.npy")
        update_time_interval()
        led.value = False
    print(f"Completed duty: {config_time}_{minute}")

def main2():
    
    mic = audiobusio.PDMIn(board.GP3, board.GP2, sample_rate=16000, bit_depth=16)
    samples = array.array('H', [0] * 200)

    spi = busio.SPI(board.GP18, MOSI=board.GP19, MISO=board.GP16)
    cs = board.GP27_A1

    sdcard = sdcardio.SDCard(spi, cs)
    vfs = storage.VfsFat(sdcard)
    storage.mount(vfs, "/sd")

    ses = np.array([])

    start = time.time()
    with open("/sd/samples.txt", "w") as f:
        while True:
            mic.record(samples, len(samples))
            magnitude = normalized_rms(samples)
            samples = np.array(samples) - 33000
            ses = numpy_add(ses, samples)
            stop = time.time()

            f.flush() # Force writing of buffered data to the SD card
            
            if (stop - start == 4):
                break
    print(np.array(ses))
    np.save("/sd/data.npy", np.array(ses))

def main():
    
    try:
        os.mkdir("/sd/records/")
    except:
        pass
    
    config_time = update_config_time()
    voice_record(6, config_time, 1)
    led.value = True

    

while(True):
    main()
