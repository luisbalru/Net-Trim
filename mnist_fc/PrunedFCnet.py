"""
   Basic fully connected neural network for classification of data.
   The default network creates a 4 layers fully connected network, (784-300-100-10),
   for classification of MNSIT data.
"""

import tensorflow as tf
import numpy as np
from BasicFCnet import BasicFCSoftmaxModel


class PrunedFCSoftmaxModel(BasicFCSoftmaxModel):
    def __init__(self):
        BasicFCSoftmaxModel.__init__(self)

    # =========================================================================
    # build the neural network
    def create_network(self, initial_weights=None, initial_biases=None, weight_masks=None, bias_masks=None):
        if weight_masks is None:
            BasicFCSoftmaxModel.create_network(initial_weights, initial_biases)
        else:
            self._create_masked_network(initial_weights, initial_biases, weight_masks, bias_masks)

    def _add_masked_fully_connected_layer(self, x, weight, bias, weight_mask, bias_mask, func=''):
        w = tf.Variable(weight.astype(np.float32), dtype=tf.float32)
        b = tf.Variable(bias.astype(np.float32), dtype=tf.float32)

        mask_w = tf.constant(weight_mask, dtype=tf.float32)
        mask_b = tf.constant(bias_mask, dtype=tf.float32)

        self._fw_signals += [x]
        self._nn_weights += [w]
        self._nn_biases += [b]

        w = tf.multiply(w, mask_w)
        b = tf.multiply(b, mask_b)
        output = tf.matmul(x, w) + b
        if func == 'relu':
            output = tf.nn.relu(output)
        elif func == 'softmax':
            self._logit = output
            output = tf.nn.softmax(output)

        return output

    # create a fully connected neural network with given initial parameters
    def _create_masked_network(self, initial_weights, initial_biases, weight_masks, bias_masks):
        self._nn_weights = []
        self._nn_biases = []

        input_len = initial_weights[0].shape[0]
        output_len = initial_weights[-1].shape[1]
        self._graph = tf.Graph()
        with self._graph.as_default():
            self._input = tf.placeholder(tf.float32, shape=[None, input_len])
            self._target = tf.placeholder(tf.float32, shape=[None, output_len])
            self._keep_prob = tf.placeholder(tf.float32)

            num_layers = len(initial_weights)

            x = self._input
            self._fw_signals = []
            for n in range(num_layers):
                # add a fully connected layer, relu (for hidden layers) or softmax (for output layer)
                x = tf.nn.dropout(x, self._keep_prob)
                if n == num_layers - 1:
                    # create the output layer
                    x = self._add_masked_fully_connected_layer(x, initial_weights[n], initial_biases[n],
                                                               weight_masks[n], bias_masks[n], func='softmax')
                else:
                    # create a fully connected layer with relu activation function
                    x = self._add_masked_fully_connected_layer(x, initial_weights[n], initial_biases[n],
                                                               weight_masks[n], bias_masks[n], func='relu')

            # output of the neural network
            self._output = x
            self._fw_signals += [self._logit]
            self._fw_signals += [self._output]

            # loss function
            self._loss = tf.reduce_mean(
                tf.nn.softmax_cross_entropy_with_logits(labels=self._target, logits=self._logit))

            # accuracy of the model
            matches = tf.equal(tf.argmax(self._target, 1), tf.argmax(self._logit, 1))
            self._accuracy = tf.reduce_mean(tf.cast(matches, tf.float32))
