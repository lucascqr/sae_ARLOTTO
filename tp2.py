# -*- coding: utf-8 -*-
"""
Created on Mon Oct 14 08:09:23 2024

@author: lucas
"""

import torch
from torch.autograd import Variable
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim

NB_ITERATIONS = 10000


class Net(nn.Module):
    def __init__(self):
        super(Net, self).__init__()
        self.fc1 = nn.Linear(2, 1, True)

    def forward(self, x):
        # L = nn.LeakyReLU(0.01)
        # x = L(self.fc1(x))

        # L = nn.ReLU()
        # x = L(self.fc1(x))

        x = F.sigmoid(self.fc1(x))
        return x


def __init__(self):
    super(Net, self).__init__()
    self.fc1 = nn.Linear(2, 1, True)


net = Net()
inputs = list(map(lambda s: Variable(torch.Tensor([s])), [
    [0, 0],
    [0, 1],
    [1, 0],
    [1, 1]]))
targets = list(map(lambda s: Variable(torch.Tensor([s])), [
    [0],
    [0],
    [0],
    [1]]))

criterion = nn.MSELoss()
optimizer = optim.SGD(net.parameters(), lr=0.1)

print("Apprentissage:")
for idx in range(0, NB_ITERATIONS):
    for input, target in zip(inputs, targets):
        optimizer.zero_grad()
        output = net(input)
        loss = criterion(output, target)
        loss.backward()
        optimizer.step()
    if idx % 500 == 0:
        print("Iteration : {} Coût: {}".format(idx, loss))

print("Après l’apprentissage:")
for input, target in zip(inputs, targets):
    output = net(input)
    print("Entrée:[{},{}] S désiré :[{}] S calculé:[{}] Erreur:[{}]".format(
        int(input[0][0]),
        int(input[0][1]),
        int(target[0]),
        round(float(output[0]), 4),
        round(float(abs(target[0] - output[0])), 4)
    ))

print("**** autres tests :")
x = list(map(lambda s: Variable(torch.Tensor([s])), [
    [0.05, 0.05],
    [0.05, 0.95],
    [0.95, 0.05],
    [0.95, 0.95],
    [0.10, 0.10],
    [0.10, 0.90],
    [0.90, 0.10],
    [0.90, 0.90]
]))
for xi in x:

    yi = net(xi)
    print("Entrée:[{},{}] S calculée:[{}] ".format(
        round(float(xi[0][0]), 4),
        round(float(xi[0][1]), 4),
        round(float(yi[0]), 4)
    ))
