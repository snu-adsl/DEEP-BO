from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import numpy as np
from ws.shared.logger import *

class ResultsRepository(object):
    def __init__(self, goal_metric):
       
        self.result = {}
        self.goal_metric = goal_metric

        self.result['error'] = []
        if goal_metric == 'accuracy':
            self.result['accuracy'] = []
        #self.result['metrics'] = []

        # list of the estimated execution time of a candidate
        #self.result['est_exec_time'] = []
        self.result['exec_time'] = []
        self.result['opt_time'] = []

        self.result['model_idx'] = []  # for tracing selected candidates
        self.result['select_trace'] = []  # for tracing arm selection
        self.result['train_epoch'] = []

        self.result['num_duplicates'] = []
        #self.result['force_terminate'] = False # whether it found a goal or not

        #debug("result initialized")

    def append(self, select_index, test_error, opt_time, exec_time, 
               metrics=None, est_exec_time=None, 
               train_epoch=None, 
               test_acc=None):
        
        #if test_acc == None:
        #    self.curr_acc = 1.0 - test_error
        #else:
        #    self.curr_acc = test_acc

        #if metrics is None:
        #    metrics = -1
        #self.result['metrics'].append(metrics)

        self.result['model_idx'].append(select_index)
        self.result['error'].append(test_error)
        if self.goal_metric == 'accuracy' and test_acc != None:
            self.result['accuracy'].append(test_acc)

        self.result['exec_time'].append(exec_time)
        self.result['opt_time'].append(opt_time)

        if train_epoch != None:
            self.result['train_epoch'].append(train_epoch)
       
        #if est_exec_time is None:
        #   est_exec_time = -1 
        #self.result['est_exec_time'].append(est_exec_time)

        #debug("result appended")

    def count_duplicates(self, shelves):
        selects = []
        for s in shelves:
            selects.append(s['model_idx'])
        num_duplicate = len(selects) - len(set(selects))

        self.result['num_duplicates'].append(num_duplicate)

    def update_trace(self, optimizer, acquistion_func):        
        self.result['select_trace'].append(optimizer + '_' + acquistion_func)

    def feed_selection(self, arm_selector):        
        self.result['mean_arr'] = arm_selector.values
        self.result['count_arr'] = arm_selector.counts

    def get_elapsed_time(self):        
        elapsed_time = 0
        if len(self.result['exec_time']) > 0:
            elapsed_time += sum(self.result['exec_time'])
        if len(self.result['opt_time']) > 0:
            elapsed_time += sum(self.result['opt_time'])

        return elapsed_time 

    def get_current_status(self):
        return self.result

    def get_values(self, property):
        if property in self.result:
            return self.result[property]
        else:
            return None

    def get_value(self, property, index):
        if property in self.result:
            if len(self.result[property]) != 0:
                if len(self.result[property]) > index:
                    return self.result[property][index]
        return None

    def get_total_duration(self, index):
        time = self.result['opt_time'][index] + self.result['exec_time'][index]
        return time


class BatchResultsRepository(ResultsRepository):
    def __init__(self):
        return super(BatchResultsRepository, self).__init__('accuracy')

    def update_batch_result(self, bandits):
        
        self.result['model_idx'] = [ b['local_result'].get_values('model_idx') for b in bandits ]
        self.result['error'] = [ b['local_result'].get_values('error') for b in bandits ]
        self.result['accuracy'] = [ b['local_result'].get_values('accuracy') for b in bandits ]

        #self.result['est_exec_time'] = [ b['local_result'].get_values('est_exec_time') for b in bandits ]
        self.result['exec_time'] = [ b['local_result'].get_values('exec_time') for b in bandits ]
        self.result['opt_time'] = [ b['local_result'].get_values('opt_time') for b in bandits ]

        self.result['iters'] = [ b['cur_iters'] for b in bandits ]
        self.result['num_duplicates'] = [ b['num_duplicates'] for b in bandits ]
        self.result['select_trace'] = [ b['local_result'].get_values('select_trace') for b in bandits ]      