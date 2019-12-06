from model import diet
import time

if __name__ == "__main__":
    start_time = time.time()
    diet.initialize("Starting diet.py")
    diet.run()
    elapsed_time = time.time() - start_time
    print(elapsed_time)

