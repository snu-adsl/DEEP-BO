import keras
import time
import numpy as np
from math import log, sqrt
from sklearn.metrics import mean_squared_error as MSE, mean_absolute_error as MAE
from ws.apis import update_current_loss
from ws.shared.logger import *

class TestAccuracyCallback(keras.callbacks.Callback):
    
    def on_train_begin(self, logs={}):
        self.start_time = time.time()
        self.accs = []

    def on_epoch_end(self, i, logs={}):
        cur_acc = logs.get('val_accuracy')
        if cur_acc == None: # XXX: support for keras 2.2 or below
            cur_acc = logs.get('val_acc')
        
        if cur_acc == None:
            warn("No validation accuracy available in {}".format(logs))
        else:
            num_epoch = i + 1
            self.accs.append(cur_acc)
            cur_loss = 1.0 - cur_acc
            elapsed_time = time.time() - self.start_time
            max_i = np.argmax(self.accs)
            update_current_loss(num_epoch, cur_loss, elapsed_time)
            log("The test accuracy at {} epoch(s) is {}. The best is {} at epoch {}. ({:.1f} secs)".format(
                num_epoch, cur_acc, self.accs[max_i], max_i+1, elapsed_time))
              

class RMSELossCallback(keras.callbacks.Callback):
    
    def on_train_begin(self, logs={}):
        self.start_time = time.time()
        self.losses = []

    def on_epoch_end(self, i, logs={}):
        num_epoch = i + 1
        p = self.model.predict(self.validation_data[0],
                               batch_size=self.params['batch_size'])
        mse = MSE(self.validation_data[1], p)
        rmse = sqrt(mse)
        self.losses.append(rmse)
        elapsed_time = time.time() - self.start_time
        update_current_loss(num_epoch, rmse, elapsed_time, loss_type='rmse')
        log("Training {} epoches takes {:.1f} secs. Current best RMSE: {}".format(
            num_epoch, elapsed_time, min(self.losses)))


class MAELossCallback(keras.callbacks.Callback):
    
    def on_train_begin(self, logs={}):
        self.start_time = time.time()
        self.losses = []

    def on_epoch_end(self, i, logs={}):
        num_epoch = i + 1
        p = self.model.predict(self.validation_data[0],
                               batch_size=self.params['batch_size'])
        mae = MAE(self.validation_data[1], p)
        self.losses.append(mae)
        elapsed_time = time.time() - self.start_time
        update_current_loss(num_epoch, mae, elapsed_time, loss_type='mae')
        log("Training {} epoches takes {:.1f} secs. Current best MAE: {}".format(
            num_epoch, elapsed_time, min(self.losses)))