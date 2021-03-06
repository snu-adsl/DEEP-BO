import time
import os
import logging
import json

from sklearn.preprocessing import StandardScaler, RobustScaler, MinMaxScaler, MaxAbsScaler
from sklearn.metrics import mean_squared_error as MSE, mean_absolute_error as MAE
from math import log, sqrt

logging.basicConfig(level=logging.DEBUG)

try:
    import keras
    from keras.models import Sequential
    from keras.layers import Dense, Dropout, Flatten
    from keras.layers import Conv2D, MaxPooling2D
    from keras.layers.normalization import BatchNormalization as BatchNorm
    from keras.callbacks import EarlyStopping
    from keras import backend as K
except:
    raise ImportError("For this example you need to install keras.")


def print_layers(params):
    for i in range(1, params['n_layers'] + 1):
        print("layer {} | size: {:>3} | activation: {:<7} | extras: {}".format(i,
                                                                               params['layer_{}_size'.format(
                                                                                   i)],
                                                                               params['layer_{}_activation'.format(
                                                                                   i)],
                                                                               params['layer_{}_extras'.format(i)]['name'])
              )
    if params['layer_{}_extras'.format(i)]['name'] == 'dropout':
        print(
            "- rate: {:.1%}".format(params['layer_{}_extras'.format(i)]['rate']), )


def print_params(params):
    print({k: v for k, v in params.items() if not k.startswith('layer_')})
    print_layers(params)


def make_dict_layer_extras(param, layer_extra_name):
    layer_number = layer_extra_name.split('_')[1]
    if param[layer_extra_name] == 'None':
        param[layer_extra_name] = {'name': 'None'}
    elif param[layer_extra_name] == 'batchnorm':
        param[layer_extra_name] = {'name': 'batchnorm'}
    else:
        param[layer_extra_name] = {
            'name': 'dropout', 'rate': param['dropout_rate_{}'.format(layer_number)]}


def config_to_params(input_config):
    params = input_config

    if 'layer_1_extras' in params:
        make_dict_layer_extras(params, 'layer_1_extras')
    if 'layer_2_extras' in params:
        make_dict_layer_extras(params, 'layer_2_extras')
    if 'layer_3_extras' in params:
        make_dict_layer_extras(params, 'layer_3_extras')
    if 'layer_4_extras' in params:
        make_dict_layer_extras(params, 'layer_4_extras')
    if 'layer_5_extras' in params:
        make_dict_layer_extras(params, 'layer_5_extras')

    try:
        params.pop('dropout_rate_1', None)
        params.pop('dropout_rate_2', None)
        params.pop('dropout_rate_3', None)
        params.pop('dropout_rate_4', None)
        params.pop('dropout_rate_5', None)
    except:
        print()
    return(params)


class KerasRegressionWorker(object):
    def __init__(self, dataset, **kwargs):
        self.data = dataset
        self.loss_type = 'RMSE'
        if 'loss_type' in kwargs:
            self.loss_type = kwargs['loss_type']
        if 'run_id' in kwargs:
            self.run_id = kwargs['run_id']
        # super().__init__(**kwargs)
        pass

    def compute(self, config, budget, working_directory, epoch_cb, *args, **kwargs):
        """
        Simple example for a compute function using a feed forward network.
        It is trained on the kin8nm dataset.
        The input parameter "config" (dictionary) contains the sampled configurations passed by the bohb optimizer
        """
        params = config_to_params(config)
        n_iterations = budget

        print("Total iterations:", n_iterations)
        y_train = self.data['y_train']
        y_valid = self.data['y_valid']
        y_test = self.data['y_test']

        if params['scaler'] != 'None':
            scaler = eval("{}()".format(params['scaler']))
            x_train_ = scaler.fit_transform(self.data['x_train'].astype(float))
            x_valid_ = scaler.transform(self.data['x_valid'].astype(float))
            x_test_ = scaler.transform(self.data['x_test'].astype(float))
        else:
            x_train_ = self.data['x_train']
            x_valid_ = self.data['x_valid']
            x_test_ = self.data['x_test']

        input_dim = x_train_.shape[1]

        model = Sequential()
        model.add(Dense(params['layer_1_size'], init=params['init'],
                        activation=params['layer_1_activation'], input_dim=input_dim))

        for i in range(int(params['n_layers']) - 1):
            extras = 'layer_{}_extras'.format(i + 1)
            if params[extras]['name'] == 'dropout':
                model.add(Dropout(params[extras]['rate']))
            elif params[extras]['name'] == 'batchnorm':
                model.add(BatchNorm())

            model.add(Dense(params['layer_{}_size'.format(i + 2)], init=params['init'],
                            activation=params['layer_{}_activation'.format(i + 2)]))

        model.add(Dense(1, init=params['init'], activation='linear'))
        model.compile(optimizer=params['optimizer'], loss=params['loss'])

        validation_data = (x_valid_, y_valid)
        early_stopping = EarlyStopping(monitor='val_loss', patience=5, verbose=0)
        h = model.fit(x_train_, y_train,
                      epochs=int(round(n_iterations)),
                      batch_size=params['batch_size'],
                      shuffle=params['shuffle'],
                      validation_data=validation_data,
                      callbacks=[early_stopping, epoch_cb])

        p = model.predict(x_test_, batch_size=params['batch_size'])
        mse = MSE(y_test, p)
        rmse = sqrt(mse)
        mae = MAE(y_test, p)
        print("# {} | RMSE: {:.4f}, MAE: {:.4f}".format(self.run_id, rmse, mae))
        
        loss = None
        if self.loss_type == 'MAE':
            loss = mae
        elif self.loss_type == 'MSE':
            loss = mse
        else:
            # set default loss
            loss = rmse
            self.loss_type = 'RMSE' 

        return ({'cur_loss': loss,
                 'loss_type': self.loss_type,
                 'cur_iter': len(h.history['loss']),
                 'iter_unit': 'epoch',
                 'early_stop': model.stop_training,
                 'info': {
                     'params': params,
                     'rmse': rmse,
                     'mae': mae}})

    @staticmethod
    def get_configspace():
        import ConfigSpace as CS
        import ConfigSpace.hyperparameters as CSH
        """
		It builds the configuration space with the needed hyperparameters.
		It is easily possible to implement different types of hyperparameters.
		Beside float-hyperparameters on a log scale, it is also able to handle categorical input parameter.
		:return: ConfigurationsSpace-Object
		"""
        cs = CS.ConfigurationSpace()

        scaler = CSH.CategoricalHyperparameter(
            'scaler', ['None', 'StandardScaler', 'RobustScaler', 'MinMaxScaler', 'MaxAbsScaler'])
        init = CSH.CategoricalHyperparameter('init', ['uniform', 'normal', 'glorot_uniform',
                                                      'glorot_normal', 'he_uniform', 'he_normal'])
        batch_size = CSH.CategoricalHyperparameter(
            'batch_size', [16, 32, 64, 128, 256])
        shuffle = CSH.CategoricalHyperparameter('shuffle', [True, False])
        loss = CSH.CategoricalHyperparameter(
            'loss', ['mean_absolute_error', 'mean_squared_error'])
        optimizer = CSH.CategoricalHyperparameter(
            'optimizer', ['rmsprop', 'adagrad', 'adadelta', 'adam', 'adamax'])

        cs.add_hyperparameters(
            [scaler, init, batch_size, shuffle, loss, optimizer])

        n_layers = CSH.UniformIntegerHyperparameter(
            'n_layers', lower=1, upper=5, default_value=2)

        layer_sizes = [
            CSH.UniformIntegerHyperparameter('layer_{}_size'.format(
                l), lower=2, upper=100, default_value=16, log=True)
            for l in range(1, 6)
        ]

        layer_activations = [
            CSH.CategoricalHyperparameter('layer_{}_activation'.format(l), [
                                          'relu', 'sigmoid', 'tanh'])
            for l in range(1, 6)
        ]

        layer_extras = [
            CSH.CategoricalHyperparameter('layer_{}_extras'.format(l), [
                                          'None', 'dropout', 'batchnorm'])
            for l in range(1, 6)
        ]

        dropout_rates = [
            CSH.UniformFloatHyperparameter('dropout_rate_{}'.format(
                l), lower=0.1, upper=0.5, default_value=0.2, log=False)
            for l in range(1, 6)
        ]

        cs.add_hyperparameters(
            [n_layers] + layer_sizes + layer_activations + layer_extras + dropout_rates)

        conditions = [CS.GreaterThanCondition(
            layer_sizes[n], n_layers, n) for n in range(1, 5)]

        conditions = conditions + \
            [CS.GreaterThanCondition(layer_activations[n], n_layers, n)
             for n in range(1, 5)]

        conditions = conditions + \
            [CS.GreaterThanCondition(layer_extras[n], n_layers, n)
             for n in range(1, 5)]

        equal_conditions = [CS.EqualsCondition(
            dropout_rates[n], layer_extras[n], 'dropout') for n in range(0, 5)]

        greater_size_conditions = [CS.GreaterThanCondition(
            dropout_rates[n], n_layers, n) for n in range(1, 5)]

        for c in conditions:
            cs.add_condition(c)

        cs.add_condition(equal_conditions[0])

        for j in range(0, 4):
            cond = CS.AndConjunction(
                greater_size_conditions[j], equal_conditions[j+1])
            cs.add_condition(cond)

        return cs


if __name__ == "__main__":
    from datasets import load_data
    
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
            print("Training {} epoches takes {:.1f} secs. Current min loss: {}".format(
                num_epoch, elapsed_time, min(self.losses)))

    start_time = time.time()
    gpu_id = 0
    os.environ['CUDA_DEVICE_ORDER'] = "PCI_BUS_ID"
    os.environ['CUDA_VISIBLE_DEVICES'] = str(gpu_id)

    dataset = load_data('kin8nm')
    worker = KerasRegressionWorker(dataset, run_id=str(gpu_id))
    cs = worker.get_configspace()
    history = RMSELossCallback()
    config = cs.sample_configuration().get_dictionary()
    print("Configuration: {}".format(config))
    res = worker.compute(config=config, budget=27,
                         epoch_cb=history, working_directory='.', params=config)
    elapsed = time.time() - start_time
    prev_res = None
    save_file = "best_kin8nm_mlp.json"
    if os.path.exists(save_file):
        with open(save_file, 'r') as saved:
            try:
                prev_res = json.load(saved)
            except:
                prev_res = None
    
    if prev_res is None:
        with open(save_file, 'w') as created:
            json.dump(res, created)        

    if prev_res != None and prev_res['cur_loss'] >= res['cur_loss']:
        with open(save_file, 'w') as updated:
            json.dump(res, updated)

    print_params(res['info']['params'])
    print("Result: {}".format(res))
    print("Elapsed time: {}, Final RMSE: {:.5f}".format(
        elapsed, res['cur_loss']))
