#!/bin/python
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import os, sys, time
import numpy as np

from .neuralnetwork import NeuralNet, NeuralTrainer
from .learn import train_minibatch
from .build_network import build_network

__all__ = [
	"NeuralOptimizer"
]


class NeuralOptimizer:
	"""Class to build a neural network and perform basic functions"""

	def __init__(self, model_layers, output_shape, optimization):
		self.model_layers = model_layers
		self.optimization = optimization
		self.output_shape = output_shape
		
		self.optimal_loss = 1e20
		self.models = []
		
	def sample_network(self):
		"""generate a network, sampling from the ranges provided by
			hyperparameter search"""
		new_model_layers = []
		for current_layer in self.model_layers:
			
			layers = {}
			for key in current_layer.keys():
				if not isinstance(current_layer[key], dict):
					layers[key] = current_layer[key]
				else:
					settings = current_layer[key]                        
					start = settings['start']
					MIN = settings['bounds'][0]
					MAX = settings['bounds'][1]
					if 'scale' not in settings.keys():
						settings['scale'] = (MAX-MIN)/4
					if 'odd' in settings:
						odd = settings['odd']
					else:
						odd = False
					if odd:
						if 'multiples' in settings:
							multiples = settings['multiples']
						else:
							multiples = 2
						offset = 1
					else:
						if 'multiples' in settings:
							multiples = settings['multiples']
						else:
							multiples = 1
						offset = 0

					good_sample = False
					while not good_sample:
						if isinstance(start, int):
							sample = start + np.round(settings['scale'] * np.random.normal(0, 1))
							if (sample >= MIN) & (sample <= MAX) & (np.mod(sample, multiples) == offset):
								good_sample = True
						else:
							sample = start + settings['scale'] * np.random.normal(0,1)
							if (sample >= MIN) & (sample <= MAX):
								good_sample = True
							
					if isinstance(start, int):
						layers[key] = int(sample)
					else:
						layers[key] = sample
			new_model_layers.append(layers)
		
		return new_model_layers
	

	def update_model_layers(self,new_model_layers):
		"""update the means of the network hyperparameters"""

		for i in range(len(self.model_layers)):
			for key in self.model_layers[i].keys():
				if isinstance(self.model_layers[i][key], dict):
					 self.model_layers[i][key]['start'] = new_model_layers[i][key]  
	
	
	def sample_optimization(self):
		""" generate an optimization dictionary from the ranges in 
		hyperparameter search"""

		new_optimization = {}
		for key in self.optimization.keys():
			if not isinstance(self.optimization[key], dict):
				new_optimization[key] = self.optimization[key]
			else:
				settings = self.optimization[key]    
				start = settings['start']
				MIN = settings['bounds'][0]
				MAX = settings['bounds'][1]
				if 'scale' not in settings.keys():
					settings['scale'] = (MAX-MIN)/4
				if 'transform' not in settings.keys():
					settings['transform'] = 'linear'

				good_sample = False
				while not good_sample:
					sample = start + np.random.uniform(-settings['scale'], settings['scale'])
					if (sample >= MIN) & (sample <= MAX):
						good_sample = True
				
				if settings['transform'] == 'linear':
					new_optimization[key] = sample
				else:
					new_optimization[key] = 10**sample
		return new_optimization
	
	
	def update_optimization(self, new_optimization):
		"""update the means of the optimization hyperparameters"""
		
		for key in self.optimization.keys():
			if isinstance(self.optimization[key], dict):
				if 'transform' in self.optimization[key].keys():
					if self.optimization[key]['transform'] == 'log':
						self.optimization[key]['start'] = np.log10(new_optimization[key])   
					else:
						self.optimization[key]['start'] = new_optimization[key]
				else:
					self.optimization[key]['start'] = new_optimization[key]
					


	def train_model(self, data, model_layers, optimization, num_epochs, batch_size, verbose):

		# generate new network
		net, placeholders = build_network(model_layers, self.output_shape)

		# build network
		nnmodel = NeuralNet(net, placeholders)

		# build trainer
		nntrainer = NeuralTrainer(nnmodel, optimization, save=None, file_path=None)

		# train network
		train_minibatch(nntrainer, {'train': data['train']}, 
								batch_size=batch_size, num_epochs=num_epochs, 
								patience=[], verbose=verbose, shuffle=True)
	
		# test model
		loss = nntrainer.test_model(data['valid'], "test", verbose=1)

		return loss


	def optimize(self, data, num_trials=30, batch_size=128, num_epochs=20, verbose=0):

		start_time = time.time()
		print('---------------------------------------------------------')
		print('Running baseline model')
		model_layers, optimization = self.get_optimal_model()   
		self.print_model(model_layers, optimization)
		print('')
		loss = self.train_model(data, model_layers, optimization, num_epochs=num_epochs, 
									 batch_size=batch_size, verbose=verbose)
		self.optimal_loss = loss
		print("    loss = " + str(loss))
		print('    took ' + str(time.time() - start_time) + ' seconds')
		print('')

		for trial_index in range(num_trials):
			start_time = time.time()
			print('---------------------------------------------------------')
			print('trial ' + str(trial_index+1) + ' out of ' + str(num_trials))
			print('---------------------------------------------------------')

			try:
				# sample network and optimization
				new_model_layers = self.sample_network()
				new_optimization = self.sample_optimization()
				self.print_model(new_model_layers, new_optimization)
				print('')

				# train over a set number of epochs to compare models
				loss = self.train_model(data, new_model_layers, new_optimization, num_epochs=num_epochs, 
											 batch_size=batch_size, verbose=verbose)
	
				self.models.append([loss, new_model_layers, new_optimization])

				print("Results:")
				print("loss = " + str(loss))
				print('took ' + str(time.time() - start_time) + ' seconds')
				if loss < self.optimal_loss:
					print("Lower loss found. Updating parameters")
					self.optimal_loss = loss 
					self.update_optimization(new_optimization)
					self.update_model_layers(new_model_layers)

			except:
				print('failed trial -- negative network size sampled')
			print('')
		print('---------------------------------------------------------')


	def get_optimal_model(self):

		model_layers = []
		for current_layer in self.model_layers:
			layers = {}
			for key in current_layer.keys():
				if not isinstance(current_layer[key], dict):
					layers[key] = current_layer[key]
				else:
					layers[key] = current_layer[key]['start']                        
			model_layers.append(layers)
		
		optimization = {}
		for key in self.optimization.keys():
			if not isinstance(self.optimization[key], dict):
				optimization[key] = self.optimization[key]
			else:
				if 'transform' in self.optimization[key].keys():
					if self.optimization[key]['transform'] == 'log':
						optimization[key] = 10**self.optimization[key]['start']
					else:
						optimization[key] = self.optimization[key]['start']
				else:
					optimization[key] = self.optimization[key]['start']
		return model_layers, optimization


	def print_optimal_model(self):
		
		model_layers, optimization = self.get_optimal_model()
		self.print_model(model_layers, optimization)


	def print_model(self, model_layers, optimization):
		print('')
		print('Model layers:')
		for layer in model_layers:
			for key in layer.keys():
				if isinstance(layer[key], str):
					if key == 'name':
						print(key + ': ' + layer[key])
				elif isinstance(layer[key], (int, float)):
					print(key + ': ' + str(layer[key]))

		print('')
		print('Optimization:')
		for key in optimization.keys():
			if isinstance(optimization[key], (int, float)):
				print(key + ': ' + str(optimization[key]))
