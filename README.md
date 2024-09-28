# Game Selector 2

Find good and bad games

## Setup (for python version)

* Install Python version >= 3.11.0
* Install the python chess package
  ```
  pip install chess
  
  pip install colorama
  
  pip install tk            (for gui)
  
  pip install psutil        (for gui)
  
  pip install Pillow        (for gui)
  
  pip install requests      (for gui)
  
  
  ```

## Help

```
usage: selector [-h] --input INPUT --output-good OUTPUT_GOOD --output-bad
                     OUTPUT_BAD --engine ENGINE [--hash HASH] [--threads THREADS]      
                     [--move-time-sec MOVE_TIME_SEC] [--score-margin SCORE_MARGIN] [-v]

Separate good and bad games

options:
  -h, --help            show this help message and exit
  --input INPUT         Input pgn filename (required=True).
  --output-good OUTPUT_GOOD
                        Output filename for good games (required=True).
  --output-bad OUTPUT_BAD
                        Output filename for bad games (required=True).
  --engine ENGINE       engine filename (required=True).
  --hash HASH           engine hash size (required=False, default=128).
  --threads THREADS     engine threads to use (required=False, default=1).
  --move-time-sec MOVE_TIME_SEC
                        movetime in seconds (required=False, default=1).
  --score-margin SCORE_MARGIN
                        score margin in pawn unit (required=False, default=7.0).       
  -v, --version         show program's version number and exit
```


## Command line

```
python selector.py --input mygames.pgn --output-good good.pgn --output-bad bad.pgn --engine stockfish.exe --hash 128 --threads 1 --move-time-sec 2
```

```
selector.exe --input mygames.pgn --output-good good.pgn --output-bad bad.pgn --engine stockfish.exe --hash 128 --threads 1 --move-time-sec 2
```




