from model import diet
import time
import logging

if __name__ == "__main__":
    start_time = time.time()

    fmt_str = "%(asctime)s: %(levelname)s: %(funcName)s Line:%(lineno)d %(message)s"
    logging.basicConfig(filename="activity.log",
                        level=logging.DEBUG,
                        filemode="w",
                        format=fmt_str)

    diet_opt = diet.Diet()
    diet_opt.initialize("Starting diet.py")
    diet_opt.run()
    elapsed_time = time.time() - start_time
    print(elapsed_time)

