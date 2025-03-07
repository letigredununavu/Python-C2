## SANDWORM C2

Python C2 sur le thème de Dune.


## USAGE

Create certificates for HTTPS and place them in certificates directory in the same directory as this app.

```bash
openssl req -x509 -newkey rsa:2048 -keyout key.pem -out cert.pem -days 365
```


### TODO

- Regarder arakis.py, beaucoup de redondance, tu devrais pouvoir cleaner
  - par exemple, tcp list,remove,start et http list,remove,start etc sont presques pareils, peut-être juste 1 méthode pour chaque
- Transfère de fichier via http
- Ajouter l'option https


#### P1
- Download de fichier via HTTP
- Upload de fichier via HTTP
- HTTP C2
- HTTPS C2

