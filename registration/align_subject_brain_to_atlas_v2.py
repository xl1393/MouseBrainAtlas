#! /usr/bin/env python

# This must be before any other matplotlib imports
import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import numpy as np

import sys
import os

sys.path.append(os.environ['REPO_DIR'] + '/utilities')
from utilities2015 import *
from registration_utilities import parallel_where_binary, Aligner4
from metadata import *
from data_manager import *

from joblib import Parallel, delayed
import time

stack_fixed = sys.argv[1]
train_sample_scheme = int(sys.argv[2])
global_transform_scheme = int(sys.argv[3])

stack_moving = 'atlas_on_MD589'

paired_structures = ['5N', '6N', '7N', '7n', 'Amb', 'LC', 'LRt', 'Pn', 'Tz', 'VLL', 'RMC', 'SNC', 'SNR', '3N', '4N',
                    'Sp5I', 'Sp5O', 'Sp5C', 'PBG', '10N', 'VCA', 'VCP', 'DC']
singular_structures = ['AP', '12N', 'RtTg', 'SC', 'IC']
structures = paired_structures + singular_structures

label_to_name_fixed = {i+1: name for i, name in enumerate(sorted(structures))}
name_to_label_fixed = {n:l for l, n in label_to_name_fixed.iteritems()}

# label_to_name_moving = {i+1: name for i, name in enumerate(sorted(structures))}
# name_to_label_moving = {n:l for l, n in label_to_name_moving.iteritems()}

label_to_name_moving = {i+1: name for i, name in enumerate(sorted(structures) + sorted([s+'_surround' for s in structures]))}
name_to_label_moving = {n:l for l, n in label_to_name_moving.iteritems()}

# volume_fixed = {name_to_label_fixed[name]: bp.unpack_ndarray_file(os.path.join(VOLUME_ROOTDIR, '%(stack)s/score_volumes/%(stack)s_down32_scoreVolume_%(name)s_trainSampleScheme_%(scheme)d.bp' % \
#                                                     {'stack': stack_fixed, 'name': name, 'scheme':train_sample_scheme}))
#                for name in structures}

volume_fixed = {name_to_label_fixed[name]: DataManager.load_score_volume(stack=stack_fixed, label=name, downscale=32, train_sample_scheme=train_sample_scheme)
               for name in structures}

print volume_fixed.values()[0].shape

vol_fixed_xmin, vol_fixed_ymin, vol_fixed_zmin = (0,0,0)
vol_fixed_ymax, vol_fixed_xmax, vol_fixed_zmax = np.array(volume_fixed.values()[0].shape) - 1

# volume_moving = {name_to_label_moving[name]: bp.unpack_ndarray_file(os.path.join(VOLUME_ROOTDIR, '%(stack)s/score_volumes/%(stack)s_down32_scoreVolume_%(name)s.bp' % \
#                                                     {'stack': stack_moving, 'name': name}))
#                for name in structures}

volume_moving = {name_to_label_moving[name]: DataManager.load_score_volume(stack=stack_moving, label=name, downscale=32, train_sample_scheme=None)
               for name in structures}

print volume_moving.values()[0].shape

vol_moving_xmin, vol_moving_ymin, vol_moving_zmin = (0,0,0)
vol_moving_ymax, vol_moving_xmax, vol_moving_zmax = np.array(volume_moving.values()[0].shape) - 1

volume_moving_structure_sizes = {l: np.count_nonzero(vol > 0) for l, vol in volume_moving.iteritems()}

def convert_to_original_name(name):
    return name.split('_')[0]

labelIndexMap_m2f = {}
for label_m, name_m in label_to_name_moving.iteritems():
    labelIndexMap_m2f[label_m] = name_to_label_fixed[convert_to_original_name(name_m)]

label_weights_m = {}
for label_m, name_m in label_to_name_moving.iteritems():
    if 'surround' in name_m:
        label_weights_m[label_m] = 0
    else:
#         label_weights_m[label_m] = 1
        label_weights_m[label_m] = np.minimum(1e5 / volume_moving_structure_sizes[label_m], 1.)

################## Optimization ######################

aligner = Aligner4(volume_fixed, volume_moving, labelIndexMap_m2f=labelIndexMap_m2f)

aligner.set_centroid(centroid_m='volume_centroid', centroid_f='volume_centroid')
# aligner.set_centroid(centroid_m='structure_centroid', centroid_f='centroid_m', indices_m=[name_to_label_moving['SNR_R']])

gradient_filepath_map_f = {ind_f: DataManager.get_score_volume_gradient_filepath_template(stack=stack_fixed, label=label_to_name_fixed[ind_f],
                            downscale=32, train_sample_scheme=train_sample_scheme)
                            for ind_m, ind_f in labelIndexMap_m2f.iteritems()}

aligner.load_gradient(gradient_filepath_map_f=gradient_filepath_map_f, indices_f=None)

# largely the same optimization path regardless of the starting condition

# For rigid,
# grad_computation_sample_number = 1e5 is desired
# grid_search_iteration_number and grid_search_sample_number seem to be unimportant as well, set to 100
# lr1=10, lr2=.1 is best

# For affine,
# lr2 = .001 is too slow; 0.1 rises faster than 0.01
# lr1 does not matter
# plateus around iteration 100, but keep rising afterwards.
# grad_computation_sample_number does not make a difference

trial_num = 1

for trial_idx in range(trial_num):

    if global_transform_scheme == 1:

        T, scores = aligner.optimize(type='affine', max_iter_num=1000, history_len=10, terminate_thresh=1e-4,
                                     indices_m=None,
                                    grid_search_iteration_number=30,
                                     grid_search_sample_number=100,
                                     grad_computation_sample_number=1e5,
                                     lr1=10, lr2=0.1,
                                     label_weights=label_weights_m,
                                    std_tx=50, std_ty=50, std_tz=100, std_theta_xy=np.deg2rad(10))

    elif global_transform_scheme == 2:

        T, scores = aligner.optimize(type='rigid', max_iter_num=1000, history_len=10, terminate_thresh=1e-4,
                                     indices_m=None,
                                    grid_search_iteration_number=30,
                                     grid_search_sample_number=100,
                                     grad_computation_sample_number=1e5,
                                     lr1=10, lr2=0.1,
                                     label_weights=label_weights_m,
                                    std_tx=50, std_ty=50, std_tz=100, std_theta_xy=np.deg2rad(10))



# print T.reshape((3,4))
# plt.plot(scores);
# print max(scores), scores[-1]

    # Save optimization parameters as txt file
    params_fp = DataManager.get_global_alignment_parameters_filepath(stack_moving=stack_moving,
                                                                stack_fixed=stack_fixed,
                                                                train_sample_scheme=train_sample_scheme,
                                                                global_transform_scheme=global_transform_scheme,
                                                                trial_idx=trial_idx)

    DataManager.save_alignment_parameters(params_fp,
                                          T, aligner.centroid_m, aligner.centroid_f,
                                          aligner.xdim_m, aligner.ydim_m, aligner.zdim_m,
                                          aligner.xdim_f, aligner.ydim_f, aligner.zdim_f)


    # Save score evolution plot as png file
    score_plot_fp = DataManager.get_global_alignment_score_plot_filepath(stack_moving=stack_moving,
                                                                        stack_fixed=stack_fixed,
                                                                        train_sample_scheme=train_sample_scheme,
                                                                        global_transform_scheme=global_transform_scheme,
                                                                        trial_idx=trial_idx)

    fig = plt.figure();
    plt.plot(scores);
    plt.savefig(score_plot_fp, bbox_inches='tight')
    plt.close(fig)
