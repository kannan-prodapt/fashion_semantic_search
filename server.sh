#!/bin/bash

APP="uvicorn app.main:app --host 0.0.0.0 --port 8000"
PIDFILE="server.pid"
LOGFILE="app.log"

start() {
    if [ -f "$PIDFILE" ] && kill -0 $(cat $PIDFILE) 2>/dev/null; then
        echo "Server already running with PID $(cat $PIDFILE)"
        exit 1
    fi

    echo "Starting server..."
    nohup $APP > $LOGFILE 2>&1 &
    echo $! > $PIDFILE
    echo "Server started with PID $(cat $PIDFILE)"
}

stop() {
    if [ ! -f "$PIDFILE" ]; then
        echo "PID file not found. Is the server running?"
        exit 1
    fi

    PID=$(cat $PIDFILE)
    echo "Stopping server with PID $PID..."
    kill $PID

    # Optional: force kill if not stopping
    sleep 2
    if kill -0 $PID 2>/dev/null; then
        echo "Force killing server..."
        kill -9 $PID
    fi

    rm -f $PIDFILE
    echo "Server stopped."
}

restart() {
    stop
    sleep 1
    start
}

case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    *)
        echo "Usage: $0 {start|stop|restart}"
        ;;
esac

