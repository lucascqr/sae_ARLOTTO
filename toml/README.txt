Exemple de configuration :
le fichier station.toml décrit l'ensemble des caractéristique de la station
le fichier satellites.toml liste les satellites à recevoir on pourra ajouter le numéro norad pour lever les ambiguïtés de nommage.
La priorité est ici noté comme caractéristique du satellite, il peut donc y avoir plusieurs sat de même priorité. On pourrait plutôt
utiliser l'ordre dans le fichier pour fixer la priorité.  
le fichier planification est un exemple de résultat de l'opération de planification sur une journée après avoir levé les conflits.