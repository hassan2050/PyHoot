# PyHoot

*Kahoot clone based on Python, updated*

First, you will need to copy the sample_config.py to config.py.  Edit the config.py to match your server.  The 'uriprefix' setting will be added to every url.

## How to start the server:

Go to the PyHoot directory and click on `Start Server (Windows).bat` from the PyHoot Directory.
It will start the server on your IP address with port 80, meaning that you can join the game from any device in the same network as your server by writing the address in the address line.
If you don't know your own IP address you can see it on the third line on the window that will be opened.

###If you are using command line \ shell (recommended for experts and Linux users):###

Start the command line or shell in your system and change the directory where you put the directory of files (named PyHoot).
Write the next command in the command line \ shell:

```python3 pyhoot.py```

This command will enable you to use different arguments than the default ones, you can do it using the next script.

```python3 pyhoot.py --[name of argument]=[the value of the arguement]```
In this way, you'll be able to add as many arguments as you want.

To shutdown the server use <kbd>CTRL</kbd> + <kbd>Break</kbd>

Arguments list:

        -h, --help            show this help message and exit
        --address ADDRESS [ADDRESS ...]
                            The address(es) we will connect to, default
                            ['localhost:8080']
        --buff-size BUFF_SIZE
                            Buff size for each time, default 1024
        --base BASE           Base directory
        --io-mode {select, poll}
                            IO that will be used, default select.
                            In windows only select available.
        --log-level {DEBUG,INFO,WARNING,CRITICAL,ERROR}
                            Log level
        --log-file FILE       Logfile to write to, otherwise will log to console.
