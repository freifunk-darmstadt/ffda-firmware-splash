ffda-firmware-splash
====================

Frontend für Gluon-Image Downloads

Schnöde Ordnerstrukturen, die die gängigen Webserver generieren in Kombination mit kryptischen Zeichenketten in den gesuchten Dateinamen erleichtern neuen Freifunkern die Suche nach dem passenden Image für den eigenen Router überhaupt nicht. Das Ziel des Firmware-Splash Projektes ist es diese Ordnerstrukturen, in einer zeitgemäßen Webseite aufbereitet, darzustellen und eine Entscheidungshilfe bei der Auswahl von Branch und benötigtem Image zu bieten.


#### Benutzung

Viele Werte in diesem Skript sind derzeit noch hardkodiert, so dass derzeit folgende Ordnerstrukur erwartet wird:
- target
  - stable
    - factory
    - sysupgrade
  - beta
    - factory
    - sysupgrade
  - experimental
    - factory
    - sysupgrade

target ist hierbei ein Symlink auf das Verzeichnis, in dem die verschiedenen Branches zu finden sind:
`ln -s /srv/www/firmware /home/gluon/ffda-firmware-splash/target`

Als einzige Python-Abhängigkeit verwendet das Skript derzeit die Template-Engine Jinja2, die entweder systemweit oder in einem virtualenv installiert werden kann.
`apt-get install python-jinja2`
oder
`pip install -r requirements.txt`

Die Ausgabe der statischen Webseite erfolgt nach STDOUT und sollte auf den passenden Zielort umgeleitet werden. Die Ordner aus www/* sollten ebenfalls am Zielort verfügbar gemacht werden (cp, symlink, alias).
`python worker.py > /srv/www/firmware/index.html`
