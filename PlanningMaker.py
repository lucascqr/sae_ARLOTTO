# -*- coding: utf-8 -*-
"""
Created on Wed Sep 25 14:45:36 2024

@author: lucas
"""

#utilisation d'un mot binaire (4 bits) pour connaitre l'état des fenetres (chevauche, exclue, choisie, attente)

#On passe dans toute la liste des "i" fenetres des visibilités
    #Si la fenetre est exclue ou chev
        #return
        
    #Si la fenetre est en attente
        #On regarde si la fenetre i finit après le de début de la fenetre i+1
            #Si c'est le cas, on fais le choix en fonction de la priorité de chaque satellite
                #Si i+1 est plus prioritaire on choisi i+1
                #Sinon on choisit i et on exclu i+1
            #Sinon, on choisi la fenetre i
            
    #Si la fenetre est déjà choisie
        #On regarde si la fenetre i finit après le de début de la fenetre i+1
            #Si c'est le cas, on fais le choix en fonction de la priorité de chaque satellite
                #Si i+1 est plus prioritaire on choisi i+1
                    #Si i-1 est exclue et ne chevauche pas 
                        #Si i+1 et i-1 ne se chevauchent pas
                            #On rajoute i-1 à la liste
                
        
