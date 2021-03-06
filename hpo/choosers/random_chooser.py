##
# Copyright (C) 2012 Jasper Snoek, Hugo Larochelle and Ryan P. Adams
#
# This code is written for research and educational purposes only to
# supplement the paper entitled
# "Practical Bayesian Optimization of Machine Learning Algorithms"
# by Snoek, Larochelle and Adams
# Advances in Neural Information Processing Systems, 2012
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import numpy        as np
import numpy.random as npr

def init(expt_dir, arg_string):
    return RandomChooser()

class RandomChooser:

    def __init__(self):
        self.acquisition_functions = ['RANDOM']
        self.mean_value = None
        self.estimates = None
        self.response_shaping = False
        self.shaping_func = None

    def set_eval_time_penalty(self, est_eval_time):
        pass

    def next(self, samples, af):

        candidates = samples.get_candidates() 
        errs = samples.get_errors("completions")
        if len(errs) == 0:
            return int(candidates[0]) # return the first candidate         
        next_index = int(candidates[int(np.floor(candidates.shape[0]*npr.rand()))])
        return next_index

