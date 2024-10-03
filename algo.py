# -*- coding: utf-8 -*-
"""
Created on Wed Sep 25 14:45:36 2024

@author: lucas
"""

#Rajouter une variable LAST_SELECTED qui contient la valeur de i pour la derniere fenetre selectionnée, dans le cas ou i-1 est OVERLAPS_PREVIOUS
#Permet de directement comparer avec la derniere fenetre sélectrionnée ;

=> rajouter le suivi du dernier satelitte de la journée précédente si la fenetre d'étend jusque au jour suivant

#utilisation d'un mot binaire (4 bits) pour connaitre l'état des fenetres (EXCLUDED, OVERLAPS_PREVIOUS, SELECTED, IDLE)


#Boucle while i<length(window)-1 ?

#On passe dans toute la liste des "i" fenêtres des visibilités
            
    #Si la fenetre est SELECTED ou IDLE
        #Si la fenetre i finit après le début de la fenetre i+1
            #Si i+1 est plus prioritaire
                #LAST_SELECTED = i+1
                #La fenetre i+1 devient SELECTED
                #La fenetre i devient EXCLUDED
                #Si i-1 est !OVERLAPS_PREVIOUS && !SELECTED && i>0 (pour éviter de rajouter i-1 à la liste alors que i-2 et i-1 se chevauchent et que i-2 est sélectionnée)
                    #Si i+1 et i-1 ne se chevauchent pas
                        #La fenetre i-1 devient SELECTED
            #Si i est plus prioritaire
                #La fenetre i devient SELECTED
                #La fenetre i+1 devient OVERLAPS_PREVIOUS
                #LAST_SELECTED = i
        #Sinon
            #LAST_SELECTED = i
            #Si l'écart entre la fin de i et le début de i+1 est suffisant
                #La fenetre i devient SELECTED
            #Sinon
                #La fenetre i devient SELECTED
                #La fenetre i+1 devient OVERLAPS_PREVIOUS
        #return
        
    #Sinon, si la fenêtre est OVERLAPS_PREVIOUS
        #Si la fenêtre LAST_SELECTED finit après le début de la fenêtre i+1
            #Si i+1 est plus prioritaire 
                #La fenetre LAST_SELECTED devient EXCLUDED
                #La fenetre i+1 devient SELECTED
                #LAST_SELECTED = i+1
            #Sinon
                #La fenetre i+1 devient OVERLAPS_PREVIOUS
        #Sinon
            #Si l'écart entre la fin de LAST_SELECTED et le début de i+1 n'est pas suffisant
                #La fenetre i+1 devient OVERLAPS_PREVIOUS
        #return












#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

#On passe dans toute la liste des "i" fenêtres des visibilités
    #Si la fenêtre est OVERLAPS_NEXT
        #return
        
    #Sinon, la fenêtre est IDLE
        #Si la fenêtre i finit après le début de la fenêtre i+1
            #Si i+1 est plus prioritaire 
                #La fenetre i devient OVERLAPS_NEXT
                #La fenetre i+1 devient SELECTED
            #Sinon
                #La fenetre i devient SELECTED
                #La fenetre i+1 devient OVERLAPS_PREVIOUS
        #Sinon
            #Si l'écart entre la fin de i et le début de i+1 est suffisant
                #La fenetre i devient SELECTED
            #Sinon
                #La fenetre i devient SELECTED
                #La fenetre i+1 devient OVERLAPS_PREVIOUS
        #return
            
    #Sinon, si la fenetre est SELECTED
        #Si la fenetre i finit après le début de la fenetre i+1
            #Si i+1 est plus prioritaire 
                #La fenetre i+1 devient SELECTED
                #La fenetre i devient OVERLAPS_NEXT
                #Si i-1 est !OVERLAPS_PREVIOUS (pour éviter de rajouter i-1 à la liste alors que i-2 et i-1 se chevauchent et que i-2 est sélectionnée)
                    #Si i+1 et i-1 ne se chevauchent pas
                        #La fenetre i-1 devient SELECTED
                    #Sinon
                        #La fenetre i-1 devient OVERLAPS_NEXT
            #Si i est plus prioritaire
                #La fenetre i+1 devient OVERLAPS_PREVIOUS
        #return
        
    #Sinon, Si la fenêtre est OVERLAPS_PREVIOUS
        #Si la fenêtre LAST_SELECTED finit après le début de la fenêtre i+1
            #Si i+1 est plus prioritaire 
                #La fenetre LAST_SELECTED devient OVERLAPS_NEXT
                #La fenetre i+1 devient SELECTED
            #Sinon
                #La fenetre i+1 devient OVERLAPS_PREVIOUS
        #Sinon
            #Si l'écart entre la fin de LAST_SELECTED et le début de i+1 n'est pas suffisant
                #La fenetre i+1 devient OVERLAPS_PREVIOUS
        #return