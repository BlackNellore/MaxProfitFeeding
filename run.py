from model import diet
import time

if __name__ == "__main__":
    start_time = time.time()
    diet_opt = diet.Diet()
    diet_opt.initialize("Starting diet.py")
    diet_opt.run()
    elapsed_time = time.time() - start_time
    print(elapsed_time)

