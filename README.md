# Tools for scrolling lyrics in AE.

## scroller.jsx

Adds a single text layer to AE which scrolls upwards according to .csv time stamps.

1. Create a .csv file without headers, and with three values per row: start time in seconds, end time, text, e.g.

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

## timer.py

Adjusts **all** timings in **all** .csv lyrics files within a folder. 

1. Execute the file with Python 3, e.g. `$ python3 timer.py`
