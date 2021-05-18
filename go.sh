source .venv/bin/activate
screen -S botory -L -Logfile log.log python run.py $1 $2
