import time
import threading

end_connection = threading.Event()

def start_timer(duration):
    print(f"Timer started for {duration} seconds.")
    if not end_connection.wait(timeout=duration):
        print("Timer finished.")
    else:
        print("Timer interrupted.")

if __name__ == "__main__":
    duration = 10  # Set timer duration in seconds
    timer_thread = threading.Thread(target=start_timer, args=(duration,))
    timer_thread.start()
