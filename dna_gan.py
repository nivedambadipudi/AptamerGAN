# -*- coding: utf-8 -*-
"""DNA_GAN.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/17d4elO1HUUY_USPusdS4ERmPbEGye4sW
"""

import os
import numpy as np
import torchvision.transforms as transforms
from torchvision.utils import save_image
from torch.utils.data import DataLoader
import torch.autograd as autograd
from torch.autograd import Variable
import torch.nn as nn
import torch.nn.functional as F
import torch
import torchvision
import matplotlib.pyplot as plt

class Opt(object):
  Seq_len = 33
  batch_size = 32
  latent_dim = 100
  n_critic = 5
  n_epochs = 1000

shape = (4, Opt.Seq_len)
device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
!mkdir models

class Generator(nn.Module):
    def __init__(self):
        super(Generator, self).__init__()
        def block(in_feat, out_feat, normalize=True):
            layers = [nn.Linear(in_feat, out_feat)]
            if normalize:
                layers.append(nn.BatchNorm1d(out_feat, 0.8))
            layers.append(nn.LeakyReLU(0.2, inplace=True))
            return layers
        self.model = nn.Sequential(
            *block(Opt.latent_dim, 128, normalize=False),
            *block(128, 256),
            *block(256, 512),
            *block(512, 1024),
            nn.Linear(1024, 4 * Opt.Seq_len)
        )

    def forward(self, z):
        x = self.model(z)
        x = x.view(-1, Opt.Seq_len, 4)
        return x

class Discriminator(nn.Module):
    def __init__(self):
        super(Discriminator, self).__init__()
        self.model = nn.Sequential(
            nn.Linear(Opt.Seq_len * 4, 512),
            nn.LeakyReLU(0.2, inplace=True),
            nn.Linear(512, 256),
            nn.LeakyReLU(0.2, inplace=True),
            nn.Linear(256, 1)
        )

    def forward(self, x):
        data_flat = x.view(x.shape[0], -1)
        validity = self.model(data_flat)
        return validity

import random
import numpy as np

nucleotides = np.array(['A', 'T', 'C', 'G'])
mapping_dict = {'A': [1, 0, 0, 0], 'T': [0, 0, 0, 1], 'C': [0, 1, 0, 0], 'G': [0, 0, 1, 0]}

dataset = np.array([''.join(np.random.choice(nucleotides, size=Opt.Seq_len)) for _ in range(10000)])

def map_to_vectors(sequence):
    return np.array([mapping_dict[nucleotide] for nucleotide in sequence])

vector_dataset = np.array([map_to_vectors(sequence) for sequence in dataset])

print(vector_dataset.shape)

dataloader = DataLoader(vector_dataset, batch_size=Opt.batch_size)

generator = Generator()
discriminator = Discriminator()

generator_optimizer = torch.optim.RMSprop(generator.parameters(), lr=0.00005)
discriminator_optimizer = torch.optim.RMSprop(discriminator.parameters(), lr=0.00005)

Tensor = torch.FloatTensor

# Commented out IPython magic to ensure Python compatibility.
for epoch in range(Opt.n_epochs):
    for step, data in enumerate(dataloader):
        real_data = Variable(data.float())
        discriminator_optimizer.zero_grad()

        z = Variable(Tensor(np.random.normal(0, 1, (data.shape[0], Opt.latent_dim))))
        fake_data = generator(z).detach().round()

        discriminator_loss = torch.mean(discriminator(fake_data)) - torch.mean(discriminator(real_data))
        discriminator_loss.backward()
        discriminator_optimizer.step()

        for p in discriminator.parameters():
            p.data.clamp_(-0.01, 0.01)

        if step % Opt.n_critic == 0:
            # train Generator
            generator_optimizer.zero_grad()
            # generate a batch of fake images
            critics_fake_imgs = generator(z)
            # Adversarial loss
            generator_loss = -torch.mean(discriminator(critics_fake_imgs))
            generator_loss.backward()
            generator_optimizer.step()

        if step % 5 == 0:
            print('[%d/%d][%d/%d]\tLoss_D: %.4f\tLoss_G: %.4f'
#                   % (epoch, Opt.n_epochs, step, len(dataloader), discriminator_loss.item(), generator_loss.item()))


torch.save(generator, "models/wgan_gp_netG.pkl")
torch.save(discriminator, "models/wgan_gp_netD.pkl")

"""# New Section"""

model = torch.load("models/wgan_gp_netG.pkl")
dis = torch.load("models/wgan_gp_netD.pkl")

latent_z = Variable(Tensor(np.random.normal(0, 1, (data.shape[0], Opt.latent_dim))))
print(model(latent_z).round())

nucleotides = np.array(['A', 'T', 'C', 'G'])

# Define a reverse mapping dictionary
reverse_mapping_dict = {tuple([1, 0, 0, 0]): 'A',
                        tuple([0, 0, 0, 1]): 'T',
                        tuple([0, 1, 0, 0]): 'C',
                        tuple([0, 0, 1, 0]): 'G'}

# Reverse mapping function
def vectors_to_sequence(vector_sequence):
    return ''.join(reverse_mapping_dict[tuple(vector)] for vector in vector_sequence)

# Apply reverse mapping to the dataset
string_dataset = np.array([vectors_to_sequence(sequence) for sequence in model(latent_z).round()])

# Print the resulting string dataset
print(string_dataset[9])