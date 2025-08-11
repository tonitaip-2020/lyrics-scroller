# Tools for scrolling lyrics in AE

## synchronizer.py

Plays an audio file in terminal, during which the sung lines can be synchronized by pressing Enter.

1. Install pre-requisites: simpleaudio (with `pip`) and ffmpeg.
2. Run `$ python3 synchronizer.py audio.wav lyrics.txt --out aligned_lines.csv`

Outputs a .csv file with three columns: start time in seconds, end time in seconds, and text.

## timer.py

Adjusts **all** timings in **all** .csv lyrics files within a folder. 

1. Execute the file with Python 3, e.g. `$ python3 timer.py`

## scroller.jsx

Adds a single text layer to AE which scrolls upwards according to .csv time stamps.

1. Create a .csv file without headers (with synchronizer.py or otherwise), and with three values per row: start time in seconds, end time, text, e.g.

```
0,2,"First line"
0.5,3,"Second line"
100,102,"Third line"
```

The values in the second column (end time) make no difference for the timing.

2. Open AE and create a new composition.
3. Run the script file with File > Script > Run Script File, and select the .jsx file.
4. Select the .csv file you want to scroll.
5. AE creates a new text layer in the selected composition.

