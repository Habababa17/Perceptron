import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

#loss functions
def cross_entropy_loss(y_true, y_pred):
    samples_amount = y_true.shape[0]
    #y_pred_clipped = np.clip(y_pred, 1e-9, 1 - 1e-9)
    return -np.sum(y_true * np.log(y_pred)) / samples_amount

def mean_squared_error(y_true, y_pred):
    return np.mean((y_true - y_pred) ** 2)

class Network:
    def __init__(self, layers, activations, loss_function="mse", seed=None):
        if seed:
            np.random.seed(seed)  
        
        self.num_layers = len(layers)
        self.weights = []
        self.biases = []
        self.activations = activations  
        self.loss_function = loss_function
        
        #reate weights and biases
        for i in range(self.num_layers - 1):
            self.weights.append(np.random.randn(layers[i], layers[i + 1]))
            self.biases.append(np.zeros((1, layers[i + 1])))

        self.weight_error_history = []
        self.bias_error_history = []

    #activation functions
    def apply_activation(self, z, activation):
        if activation == "sigmoid":
            return 1 / (1 + np.exp(-z))
        elif activation == "relu":
            return np.maximum(0, z)
        elif activation == "linear":
            return z

    #derivatives
    def apply_activation_derivative(self, a, activation):
        if activation == "sigmoid":
            return a * (1 - a)
        elif activation == "relu":
            return np.where(a > 0, 1, 0)
        elif activation == "linear":
            return 1

    #forward
    def forward(self, X):
        self.activations_values = [X]
        self.z_values = []
        
        for i in range(self.num_layers - 1):
            z = np.dot(self.activations_values[-1], self.weights[i]) + self.biases[i]
            self.z_values.append(z)
            a = self.apply_activation(z, self.activations[i])
            self.activations_values.append(a)
        
        return self.activations_values[-1]

    #backward
    def backward(self, X, y, output, learning_rate):
        deltas = []

        output_error = y - output  
        output_delta = output_error * self.apply_activation_derivative(output, self.activations[-1])

        deltas.append(output_delta)
        
        #backpropagation
        for i in range(self.num_layers - 2, 0, -1):
            z = self.z_values[i - 1]  
            delta = deltas[-1].dot(self.weights[i].T) * self.apply_activation_derivative(self.activations_values[i], self.activations[i - 1])
            deltas.append(delta)

        deltas.reverse()  

        #update weights and biases
        for i in range(self.num_layers - 1):
            weight_update = self.activations_values[i].T.dot(deltas[i]) * learning_rate
            bias_update = np.sum(deltas[i], axis=0, keepdims=True) * learning_rate
            
            self.weights[i] += weight_update
            self.biases[i] += bias_update
            
            #save the errors
            self.weight_error_history.append(np.linalg.norm(weight_update))
            self.bias_error_history.append(np.linalg.norm(bias_update))
    
    def train(self, X, y, epochs, learning_rate, print_loss=True):
        for epoch in range(epochs):

            output = self.forward(X)
            
            self.backward(X, y, output, learning_rate)
            
            #loss at every 1000 epochs
            if epoch % 1000 == 0 and print_loss:
                if self.loss_function == "cross_entropy":
                    loss = cross_entropy_loss(y, output)
                else:
                    loss = mean_squared_error(y, output)
                print(f'Epoch {epoch}, Loss: {loss}')

    # Function to plot weight and bias error history
    def plot_error_history(self):
        weight_error_history = np.array(self.weight_error_history)
        bias_error_history = np.array(self.bias_error_history)

        # Plotting
        fig, axs = plt.subplots(2, figsize=(10, 8))

        # Plot weight updates
        axs[0].plot(weight_error_history, label='Weight Update Norms')
        axs[0].set_title('Weight Error Over Epochs')
        axs[0].set_xlabel('Epochs')
        axs[0].set_ylabel('Error (Norm)')
        axs[0].legend()

        # Plot bias updates
        axs[1].plot(bias_error_history, label='Bias Update Norms')
        axs[1].set_title('Bias Error Over Epochs')
        axs[1].set_xlabel('Epochs')
        axs[1].set_ylabel('Error (Norm)')
        axs[1].legend()

        plt.tight_layout()
        plt.show()

    def predict(self, X, regression = False):
        predictions = self.forward(X)
        if(regression):
            return predictions
        else:    
            return (predictions >= 0.5).astype(int)
    
    
def calculate_accuracy(y_true, y_pred):
    size = len(y_true[0])
    correct_predictions = np.sum(y_true == y_pred)
    accuracy = correct_predictions / len(y_true) * 100 / size
    return accuracy



def perform_tests_simple(path):
    #Accuracy for data.simple.test.100:  99.0 %
    #Accuracy for data.simple.test.500:  99.4 %
    #Accuracy for data.simple.test.1000:  99.6 %
    #Accuracy for data.simple.test.10000:  99.64 %
    layers = [2, 4, 2]
    activations = ["linear","sigmoid"]  #"relu", "sigmoid" or "linear"
    learning_rate = 0.001
    epochs = 10000
    seed = 42
    loss_function = "cross_entropy"  #"cross_entropy" or "mse"

    numbers = [100, 500, 1000, 10000]
    for num in numbers:
        train_file_path = path + f"data.simple.train.{num}.csv"

        data = pd.read_csv(train_file_path, delimiter=',', header=0)
        data = data.sample(frac=1).reset_index(drop=True)
        X = data[['x', 'y']].to_numpy()
        cls = data['cls'].to_numpy() - 1 
        y = np.eye(2)[cls]

        nn = Network(layers, activations, loss_function=loss_function, seed=seed)
        nn.train(X, y, epochs, learning_rate, False)

        test_file_path = path + f"data.simple.test.{num}.csv"

        data = pd.read_csv(test_file_path, delimiter=',', header=0)
        X = data[['x', 'y']].to_numpy()
        cls = data['cls'].to_numpy() - 1 
        y = np.eye(2)[cls]
        predictions = nn.predict(X)
    
        print(f"Accuracy for data.simple.test.{num}: ", calculate_accuracy(y, predictions), "%")

    return

def perform_tests_three_gauss(path):
    #Accuracy for data.simple.test.100:  95.0 %
    #Accuracy for data.simple.test.500:  94.91111111111111 %
    #Accuracy for data.simple.test.1000:  94.93333333333334 %
    #Accuracy for data.simple.test.10000:  94.92777777777779 %
    layers = [2, 6, 3]
    activations = ["linear", "sigmoid"]  #"relu", "sigmoid" or "linear"
    learning_rate = 0.003
    epochs = 10000
    seed = 42
    loss_function = "cross_entropy"  #"cross_entropy" or "mse"

    numbers = [100, 500, 1000, 10000]
    for num in numbers:
        train_file_path = path + f"data.three_gauss.train.{num}.csv"

        data = pd.read_csv(train_file_path, delimiter=',', header=0)
        data = data.sample(frac=1).reset_index(drop=True)
        X = data[['x', 'y']].to_numpy()
        cls = data['cls'].to_numpy() - 1 
        y = np.eye(3)[cls]

        nn = Network(layers, activations, loss_function=loss_function, seed=seed)
        nn.train(X, y, epochs, learning_rate, False)

        test_file_path = path + f"data.three_gauss.train.{num}.csv"

        data = pd.read_csv(test_file_path, delimiter=',', header=0)
        X = data[['x', 'y']].to_numpy()
        cls = data['cls'].to_numpy() - 1 
        y = np.eye(3)[cls]
        predictions = nn.predict(X)
    
        print(f"Accuracy for data.simple.test.{num}: ", calculate_accuracy(y, predictions), "%")

    return

def perform_tests_activation(path):
    #Mean Squared Error for data.regression.test.100: 2104.4524425570726
    #Mean Squared Error for data.regression.test.500: 2247.5073269826034
    #Mean Squared Error for data.regression.test.1000: 2436.7308308206007
    #Mean Squared Error for data.regression.test.10000: 2322.3700445755876
    layers = [1, 1]  
    activations = ["linear"] 
    learning_rate = 0.0001
    epochs = 10000
    seed = 42
    loss_function = "mse" 

    numbers = [100, 500, 1000, 10000]  
    for num in numbers:
        train_file_path = path + f"data.activation.train.{num}.csv"
        data = pd.read_csv(train_file_path, delimiter=',', header=0)
        data = data.sample(frac=1).reset_index(drop=True)  

        X = data[['x']].to_numpy() 
        y = data[['y']].to_numpy() 

        #standarization of data
        mean_X = np.mean(X, axis=0)
        std_X = np.std(X, axis=0)
        X_standardized = (X - mean_X) / std_X
        
        mean_y = np.mean(y, axis=0)
        std_y = np.std(y, axis=0)
        y_standardized = (y - mean_y) / std_y

        nn = Network(layers, activations, loss_function=loss_function, seed=seed)
        nn.train(X_standardized, y_standardized, epochs, learning_rate, False)  

        test_file_path = path + f"data.activation.test.{num}.csv"
        data = pd.read_csv(test_file_path, delimiter=',', header=0)
        X_test = data[['x']].to_numpy()  
        y_test = data[['y']].to_numpy() 
        X_test_standardized = (X_test - mean_X) / std_X


        predictions_standardized = nn.predict(X_test_standardized, True)
        predictions = predictions_standardized * std_y + mean_y

        mse = mean_squared_error(y_test, predictions)
        print(f"Mean Squared Error for data.regression.test.{num}: {mse}")

    return


if __name__ == "__main__":
    

#    train_file_path = folder_path + f"data.simple.train.1000.csv"
#    data = pd.read_csv(train_file_path, delimiter=',', header=0)
#    data = data.sample(frac=1).reset_index(drop=True)
#
#    X = data[['x', 'y']].to_numpy()
#    cls = data['cls'].to_numpy() - 1 
#    y = np.eye(2)[cls]
#
#    #parameters
#    layers = [2, 4, 4, 2]
#    activations = ["relu", "relu", "sigmoid"]  #"relu", "sigmoid" or "linear"
#    learning_rate = 0.05
#    epochs = 10000
#    seed = 42
#    loss_function = "cross_entropy"  #"cross_entropy" or "mse"
#
#    #initialize and train the network
#    nn = Network(layers, activations, loss_function=loss_function, seed=seed)
#    nn.train(X, y, epochs, learning_rate)
#
#    #plot the error history
#    # nn.plot_error_history()
#
#    test_file_path = folder_path + f"data.simple.test.100.csv"
#    data = pd.read_csv(test_file_path, delimiter=',', header=0)
#    X = data[['x', 'y']].to_numpy()
#    cls = data['cls'].to_numpy() - 1 
#    y = np.eye(2)[cls]
#    predictions = nn.predict(X)
#
#    print("Accuracy: ", calculate_accuracy(y, predictions), "%")

    folder_path = 'S:/SN/projekt1/classification/'
    #perform_tests_simple(folder_path)
    #perform_tests_three_gauss(folder_path)
    folder_path = 'S:/SN/projekt1/regression/'
    perform_tests_activation(folder_path)

