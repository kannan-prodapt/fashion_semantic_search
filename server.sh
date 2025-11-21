#!/bin/bash

### ==============================
### CONFIG: FASTAPI BACKEND
### ==============================
APP_BACKEND="uvicorn app.main:app --host 0.0.0.0 --port 8000"
PID_BACKEND="backend.pid"
LOG_BACKEND="backend.log"

### ==============================
### CONFIG: STREAMLIT FRONTEND
### ==============================
STREAMLIT_CMD="streamlit run app/ui/amazon_ui.py --server.address 0.0.0.0 --server.port 8501"
PID_STREAMLIT="streamlit.pid"
LOG_STREAMLIT="streamlit.log"

### ==============================
### START FUNCTIONS
### ==============================

start_backend() {
    if [ -f "$PID_BACKEND" ] && kill -0 $(cat $PID_BACKEND) 2>/dev/null; then
        echo "Backend already running with PID $(cat $PID_BACKEND)"
    else
        echo "Starting Backend..."
        nohup $APP_BACKEND > $LOG_BACKEND 2>&1 &
        echo $! > $PID_BACKEND
        echo "Backend started with PID $(cat $PID_BACKEND)"
    fi
}

start_streamlit() {
    if [ -f "$PID_STREAMLIT" ] && kill -0 $(cat $PID_STREAMLIT) 2>/dev/null; then
        echo "Streamlit already running with PID $(cat $PID_STREAMLIT)"
    else
        echo "Starting Streamlit UI..."
        nohup $STREAMLIT_CMD > $LOG_STREAMLIT 2>&1 &
        echo $! > $PID_STREAMLIT
        echo "Streamlit started with PID $(cat $PID_STREAMLIT)"
    fi
}

### ==============================
### STOP FUNCTIONS
### ==============================

stop_backend() {
    if [ ! -f "$PID_BACKEND" ]; then
        echo "Backend PID not found."
    else
        PID=$(cat $PID_BACKEND)
        echo "Stopping Backend (PID $PID)..."
        kill $PID
        sleep 2
        if kill -0 $PID 2>/dev/null; then
            echo "Force killing backend..."
            kill -9 $PID
        fi
        rm -f $PID_BACKEND
        echo "Backend stopped."
    fi
}

stop_streamlit() {
    if [ ! -f "$PID_STREAMLIT" ]; then
        echo "Streamlit PID not found."
    else
        PID=$(cat $PID_STREAMLIT)
        echo "Stopping Streamlit (PID $PID)..."
        kill $PID
        sleep 2
        if kill -0 $PID 2>/dev/null; then
            echo "Force killing streamlit..."
            kill -9 $PID
        fi
        rm -f $PID_STREAMLIT
        echo "Streamlit stopped."
    fi
}

### ==============================
### MAIN COMPOSED OPERATIONS
### ==============================

start() {
    start_backend
    start_streamlit
}

stop() {
    stop_backend
    stop_streamlit
}

restart() {
    stop
    sleep 1
    start
}

### ==============================
### COMMAND LINE ARG HANDLER
### ==============================

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
