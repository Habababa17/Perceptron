import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.special import expit

# loss functions
def cross_entropy_loss(y_true, y_pred):
    samples_amount = y_true.shape[0]
    y_pred_clipped = np.clip(y_pred, 1e-9, 1 - 1e-9)
    return -np.sum(y_true * np.log(y_pred_clipped)) / samples_amount

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

        # initialize weights and biases
        for i in range(self.num_layers - 1):
            limit = np.sqrt(6 / (layers[i] + layers[i + 1])) 
            self.weights.append(np.random.uniform(-limit, limit, (layers[i], layers[i + 1])))
            self.biases.append(np.zeros((1, layers[i + 1])))

        self.weight_error_history = []
        self.bias_error_history = []
        self.weight_values_history = []

    def apply_activation(self, z, activation):
        if activation == "sigmoid":
            return expit(z)
        elif activation == "relu":
            return np.maximum(0, z)
        elif activation == "linear":
            return z
        elif activation == "cube":
            return z**3
        elif activation == "softmax":
            z_stable = z - np.max(z, axis=1, keepdims=True)
            exps = np.exp(z_stable)
            return exps / (np.sum(exps, axis=1, keepdims=True) + 1e-9)

    def apply_activation_derivative(self, a, activation):
        if activation == "sigmoid":
            return a * (1 - a)
        elif activation == "relu":
            return np.where(a > 0, 1, 0)
        elif activation == "linear":
            return 1
        elif activation == "cube":
            return 2 * a ** 2


    def forward(self, X):
        self.activations_values = [X]
        self.z_values = []

        for i in range(self.num_layers - 1):
            z = np.dot(self.activations_values[-1], self.weights[i]) + self.biases[i]
            self.z_values.append(z)
            a = self.apply_activation(z, self.activations[i])
            self.activations_values.append(a)
        return self.activations_values[-1]

    def backward(self, X, y, output, learning_rate):
        deltas = []

        if self.activations[-1] == "softmax" and self.loss_function == "cross_entropy":
            output_delta =  y - output
        else:
            output_error = y - output
            output_delta = output_error * self.apply_activation_derivative(output, self.activations[-1])

        deltas.append(output_delta)
        
        # backpropagation
        for i in range(self.num_layers - 2, 0, -1):
            z = self.z_values[i - 1]  
            delta = deltas[-1].dot(self.weights[i].T) * self.apply_activation_derivative(self.activations_values[i], self.activations[i - 1])
            deltas.append(delta)

        deltas.reverse()  

        # update weights and biases
        for i in range(self.num_layers - 1):
            weight_update = self.activations_values[i].T.dot(deltas[i]) * learning_rate
            bias_update = np.sum(deltas[i], axis=0, keepdims=True) * learning_rate

            self.weights[i] += weight_update
            self.biases[i] += bias_update
            
            # save the errors
            self.weight_error_history.append(np.linalg.norm(weight_update))
            self.bias_error_history.append(np.linalg.norm(bias_update))

        self.weight_values_history.append([w.copy() for w in self.weights])

    def train(self, X, y, epochs, learning_rate, print_loss=True):
        for epoch in range(epochs):
            output = self.forward(X)
            self.backward(X, y, output, learning_rate)
            
            if epoch % 1000 == 0 and print_loss:
                if self.loss_function == "cross_entropy":
                    loss = cross_entropy_loss(y, output)
                else:
                    loss = mean_squared_error(y, output)
                print(f'Epoch {epoch}, Loss: {loss}')
    
    def plot_error_history(self):
        weight_error_history = np.array(self.weight_error_history)
        bias_error_history = np.array(self.bias_error_history)

        num_layers = self.num_layers - 1

        for layer in range(num_layers):
            fig, ax = plt.subplots(figsize=(10, 5))
            layer_weight_errors = weight_error_history[layer::num_layers]
            ax.plot(layer_weight_errors, label=f'Weight Update Norms (Layer {layer+1} -> {layer+2})')
            ax.set_title(f'Weight Error Over Epochs (Layer {layer+1} -> {layer+2})')
            ax.set_xlabel('Epochs')
            ax.set_ylabel('Error (Norm)')
            ax.legend()
            plt.tight_layout()
            plt.show()

        for layer in range(num_layers):
            fig, ax = plt.subplots(figsize=(10, 5))
            layer_bias_errors = bias_error_history[layer::num_layers]
            ax.plot(layer_bias_errors, label=f'Bias Update Norms (Layer {layer+1} -> {layer+2})')
            ax.set_title(f'Bias Error Over Epochs (Layer {layer+1} -> {layer+2})')
            ax.set_xlabel('Epochs')
            ax.set_ylabel('Error (Norm)')
            ax.legend()
            plt.tight_layout()
            plt.show()
    
    def plot_weight_value_history(self):
        num_layers = self.num_layers - 1

        for layer in range(num_layers):
            fig, ax = plt.subplots(figsize=(10, 5))
            layer_weights = [epoch[layer] for epoch in self.weight_values_history]
            flat_weights = np.array([w.flatten() for w in layer_weights])

            for i in range(flat_weights.shape[1]):
                ax.plot(flat_weights[:, i], label=f'Weight {i+1}')

            ax.set_title(f'Weight Values for Layer {layer+1} -> {layer+2} Over Iterations')
            ax.set_xlabel('Iteration')
            ax.set_ylabel('Weight Value')
            ax.legend()
            plt.tight_layout()
            plt.show()

    def predict(self, X, regression = False):
        predictions = self.forward(X)
        if(regression):
            return predictions
        else:    
            predictions = self.forward(X)
            return np.argmax(predictions, axis=1)

    
def calculate_accuracy(y_true, y_pred):
    y_true_labels = np.argmax(y_true, axis=1)
    correct_predictions = np.sum(y_true_labels == y_pred)
    accuracy = (correct_predictions / len(y_true)) * 100
    return accuracy

def perform_tests_simple(path, random_seed=False, print_results=False, plot_results=False):
    layers = [2, 4, 2]
    activations = ["linear", "sigmoid"]  # "relu", "sigmoid" or "linear", "softmax"
    learning_rate = 0.0001
    epochs = 500
    if random_seed:
        seed = np.random.randint(1, 100)
    else:
        seed = 42
    print('seed', seed)
    loss_function = "cross_entropy"  # "cross_entropy" or "mse"

    numbers = [100, 500, 1000, 10000]
    accuracy = list()
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
        accuracy.append(calculate_accuracy(y, predictions))
        if print_results:
            print(f"Accuracy for data.simple.test.{num}: ", calculate_accuracy(y, predictions), "%")

        if plot_results:
            if num == numbers[-1]:
                plt.figure(figsize=(12, 5))

                plt.subplot(1, 2, 1)
                plt.title("Wizualizacja zbióru uczącego")
                plt.scatter(X[:, 0], X[:, 1], c=cls, cmap='viridis', edgecolor='k')
                plt.xlabel("Cecha 1")
                plt.ylabel("Cecha 2")

                plt.subplot(1, 2, 2)
                plt.title("Efekty klasyfikacji")

                x_min, x_max = X[:, 0].min() - 1, X[:, 0].max() + 1
                y_min, y_max = X[:, 1].min() - 1, X[:, 1].max() + 1
                xx, yy = np.meshgrid(np.linspace(x_min, x_max, 40), np.linspace(y_min, y_max, 40))

                Z = nn.predict(np.c_[xx.ravel(), yy.ravel()])
                Z = Z.reshape(xx.shape)

                plt.contourf(xx, yy, Z, cmap='coolwarm', alpha=0.3)

                plt.scatter(X[:, 0], X[:, 1], c=predictions, s=20, edgecolor="k", cmap='coolwarm')
                plt.title(f"Wizualizacja granicy decyzji")
                plt.show()

            nn.plot_weight_value_history()
            nn.plot_error_history()

    return sum(accuracy) / len(accuracy)

def perform_tests_three_gauss(path, random_seed=False, print_results=False, plot_results=False):
    layers = [2, 4, 3]
    activations = ["linear", "sigmoid"]
    learning_rate = 0.0001
    epochs = 1000
    if random_seed:
        seed = np.random.randint(1, 100)
    else:
        seed = 41
    print('seed', seed)
    loss_function = "cross_entropy"

    numbers = [100, 500, 1000, 10000]
    accuracy = list()
    for num in numbers:
        train_file_path = path + f"data.three_gauss.train.{num}.csv"

        data = pd.read_csv(train_file_path, delimiter=',', header=0)
        data = data.sample(frac=1).reset_index(drop=True)
        X = data[['x', 'y']].to_numpy()
        cls = data['cls'].to_numpy() - 1
        y = np.eye(3)[cls]

        nn = Network(layers, activations, loss_function=loss_function, seed=seed)
        nn.train(X, y, epochs, learning_rate, False)

        test_file_path = path + f"data.three_gauss.test.{num}.csv"
        data = pd.read_csv(test_file_path, delimiter=',', header=0)
        X = data[['x', 'y']].to_numpy()
        cls = data['cls'].to_numpy() - 1 
        y = np.eye(3)[cls]
        
        predictions = nn.predict(X)
        accuracy.append(calculate_accuracy(y, predictions))
        if print_results:
            print(f"Accuracy for data.simple.test.{num}: ", calculate_accuracy(y, predictions), "%")

        if plot_results:
            if num == numbers[-1]:
                plt.figure(figsize=(12, 5))

                plt.subplot(1, 2, 1)
                plt.title("Wizualizacja zbioru uczącego")
                plt.scatter(X[:, 0], X[:, 1], c=cls, cmap='viridis', edgecolor='k')
                plt.xlabel("Cecha 1")
                plt.ylabel("Cecha 2")

                plt.subplot(1, 2, 2)
                plt.title("Efekty klasyfikacji")

                x_min, x_max = X[:, 0].min() - 1, X[:, 0].max() + 1
                y_min, y_max = X[:, 1].min() - 1, X[:, 1].max() + 1
                xx, yy = np.meshgrid(np.linspace(x_min, x_max, 40), np.linspace(y_min, y_max, 40))

                Z = nn.predict(np.c_[xx.ravel(), yy.ravel()])
                Z = Z.reshape(xx.shape)

                plt.contourf(xx, yy, Z, cmap='coolwarm', alpha=0.3)

                plt.scatter(X[:, 0], X[:, 1], c=predictions, s=20, edgecolor="k", cmap='coolwarm')
                plt.title(f"Wizualizacja granicy decyzji")
                plt.show()
            nn.plot_weight_value_history()
            nn.plot_error_history()

    return sum(accuracy) / len(accuracy)

def perform_tests_activation(path, random_seed=False, print_results=False, plot_results=False):
    layers = [1, 2, 1]  
    activations = ["sigmoid", "linear"] 
    #learning_rate = 0.01
    epochs = 1000
    if random_seed:
        seed = np.random.randint(1, 100)
    else:
        seed = 42
    print('seed', seed)
    loss_function = "mse" 

    numbers = [100, 500, 1000, 10000]
    MSEs = list()
    for num in numbers:
        learning_rate = 1.0/num
        train_file_path = path + f"data.activation.train.{num}.csv"
        data = pd.read_csv(train_file_path, delimiter=',', header=0)
        data = data.sample(frac=1).reset_index(drop=True)  

        X = data[['x']].to_numpy() 
        y = data[['y']].to_numpy() 

        # standarization of data
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
        MSEs.append(mse)
        if print_results:
            print(f"Mean Squared Error for data.regression.test.{num}: {mse}")

        if plot_results:
            if num == numbers[-1]:
                plt.figure(figsize=(10, 6))
                plt.scatter(X, y, color='blue', label='Training Data', alpha=0.5, s=0.1)
                plt.xlabel('X')
                plt.ylabel('Y')
                plt.legend()
                plt.grid()
                plt.show()

                plt.figure(figsize=(10, 6))
                plt.scatter(X_test, y_test, color='green', label='Test Data', alpha=0.5, s=1)
                plt.plot(X_test, predictions, color='red', linewidth=1, label='Predictions', linestyle="-")
                plt.xlabel('X')
                plt.ylabel('Y')
                plt.legend()
                plt.grid()
                plt.show()

            nn.plot_weight_value_history()
            nn.plot_error_history()

    return sum(MSEs) / len(MSEs)

def perform_tests_cube(path, random_seed=False, print_results=False, plot_results=False):
    layers = [1,4,1]  
    activations = ["cube", "linear"] 
    learning_rate = 0.00000001
    epochs = 10000
    if random_seed:
        seed = np.random.randint(1, 100)
    else:
        seed = 65
    print('seed', seed)
    loss_function = "mse" 

    numbers = [100, 500, 1000, 10000]
    MSEs = list()
    for num in numbers:
        # learning_rate = 1.0/num
        train_file_path = path + f"data.cube.train.{num}.csv"
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

        test_file_path = path + f"data.cube.test.{num}.csv"
        data = pd.read_csv(test_file_path, delimiter=',', header=0)
        X_test = data[['x']].to_numpy()  
        y_test = data[['y']].to_numpy() 
        X_test_standardized = (X_test - mean_X) / std_X


        predictions_standardized = nn.predict(X_test_standardized, True)
        predictions = predictions_standardized * std_y + mean_y

        mse = mean_squared_error(y_test, predictions)
        MSEs.append(mse)
        if print_results:
            print(f"Mean Squared Error for data.regression.test.{num}: {mse}")

        if plot_results:
            if num == numbers[-1]:
                plt.figure(figsize=(10, 6))
                plt.scatter(X, y, color='blue', label='Training Data', alpha=0.5, s=0.1)
                plt.xlabel('X')
                plt.ylabel('Y')
                plt.legend()
                plt.grid()
                plt.show()

                plt.figure(figsize=(10, 6))
                plt.scatter(X_test, y_test, color='green', label='Test Data', alpha=0.5, s=1)
                plt.plot(X_test, predictions, color='red', linewidth=1, label='Predictions', linestyle="-")
                plt.xlabel('X')
                plt.ylabel('Y')
                plt.legend()
                plt.grid()
                plt.show()

            nn.plot_weight_value_history()
            nn.plot_error_history()

    return sum(MSEs) / len(MSEs)

def classification_tests(folder_path):
    iterations = 1
    accuracy = list()
    for i in range(iterations):
        accuracy.append(perform_tests_simple(folder_path, False, True, True))
    print('Wynik:')
    print(sum(accuracy)/len(accuracy))

    accuracy = list()
    for i in range(iterations):
        accuracy.append(perform_tests_three_gauss(folder_path, False, True, False))
    print('Wynik:')
    print(sum(accuracy)/len(accuracy))

    return

def regression_tests(folder_path):
    iterations = 1
    accuracy = list()
    for i in range(iterations):
        accuracy.append(perform_tests_activation(folder_path, False, True, True))
    print('Wynik:')
    print(sum(accuracy)/len(accuracy))

    accuracy = list()
    for i in range(iterations):
        accuracy.append(perform_tests_cube(folder_path, False, True, False))
    print('Wynik:')
    print(sum(accuracy)/len(accuracy))

    return

if __name__ == "__main__":
    
    folder_path = 'C:/Users/patry/Downloads/projekt1/projekt1/classification/'
    classification_tests(folder_path)
        
    folder_path = 'C:/Users/patry/Downloads/projekt1/projekt1/regression/'
    regression_tests(folder_path)
