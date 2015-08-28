import os
import time

from preprocess_utility import *

t = time.time()

script_root = os.environ['GORDON_REPO_DIR']+'/notebooks/'
arg_tuples = [[i] for i in range(8)]
run_distributed3(script_root+'/find_optimal_transformation_executable.py', arg_tuples)

print 'total', time.time() - t, 'seconds'
