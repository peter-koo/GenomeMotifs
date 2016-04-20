#/bin/python
import theano.tensor as T
from lasagne.init import Constant, Normal, Uniform, GlorotNormal
from lasagne.init import GlorotUniform, HeNormal, HeUniform
from build_network import build_network

def binary_conv_autoencoder_model(shape, num_labels):

	
	input_var = T.tensor4('inputs')
	target_var = T.dmatrix('targets')

    # create model
	layer1 = {'layer': 'input',
	          'input_var': input_var,
	          'shape': shape,
  			  'name': 'input'
  			  }
	layer2 = {'layer': 'convolution', 
	          'num_filters': 200, 
	          'filter_size': (8, 1),
	          'W': GlorotUniform(),
	          'b': Constant(0.05),
	          'norm': 'batch', 
	          'activation': 'prelu',
	          'pool_size': (4, 1),
  			  'name': 'conv1'
  			  }
	layer3 = {'layer': 'convolution', 
	          'num_filters': 200, 
	          'filter_size': (8, 1),
	          'W': GlorotUniform(),
	          'b': Constant(0.05),
	          'norm': 'batch', 
	          'activation': 'prelu',
	          'pool_size': (4, 1),
  			  'name': 'conv2'
  			  }
  	layer5 = {'layer': 'dense', 
	          'num_units': 100, 
	          'W': GlorotUniform(),
	          'b': Constant(0.05), 
	          'norm': 'batch',
	          'activation': 'prelu',
	          'dropout': .5,
  			  'name': 'dense'
  			  }
	layer6 = {'layer': 'dense', 
	          'num_units': num_labels, 
	          'W': GlorotUniform(),
	          'b': Constant(0.05),
	          'activation': 'sigmoid',
  			  'name': 'output'
  			  }

	model_layers = [layer1, layer2, layer3, layer5, layer6]
	network = build_network(model_layers, autoencode=1)

	# optimization parameters
	optimization = {"objective": "mse",
	                "optimizer": "adam"
#	                "optimizer": "nesterov_momentum",
#	                "learning_rate": 0.1,	                
#	                "rho": .9,
#	                "epsilon": 1e-6,
#	                "weight_norm": 7, 
#	                "momentum": 0.975,
#	                "l1": 1e-7,
#	                "l2": 1e-8
	                }

	                
	return network, input_var, target_var, optimization
