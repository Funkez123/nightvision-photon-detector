# Photonendetektor und Tool zur Auswertung eines Doppelspaltexperiments

[GER]

In Python3 geschriebene Software um Daten (live - AV-USB-Converter oder als Video [zb. MP4]) von fehlerhaften Pixeln zu filtern und Photonenstatistiken zu erstellen.

1920x1080px Monitor empfohlen

GUI mit PySimpleGUI verfasst

Benötigte Bibliotheken :

- NumPy
- SciPy
- PySimpleGUI
- Matplotlib
- OpenCV

(neuste Versionen werden empfohlen)
(alle Bibliotheken lassen sich mit dem pip3-Paketmanager installieren)

oder in der Kommandozeile eingeben:

`pip3 install -r requirements.txt`

Einrichtungsfenster:

![image](https://user-images.githubusercontent.com/53939068/142772317-e7a273a9-a5c0-485c-a6f6-9bfeedc7ebb8.png)


Beispielhafte Verarbeitung der Photonen:

![image](https://user-images.githubusercontent.com/53939068/142772327-0bfe039d-136b-4957-b422-8bba2fc35582.png)


Features :

- Live-Verarbeitung von Bilddaten
- GUI für einfachere Verwendbarkeit
- Windows/Mac/Linux Support
- Anpassung der Anzeigegeschwindigkeit für zb. bessere Verwendung im Unterricht
- selbstständig skalierende Achsen der Diagramme
- Slider zur Anpassung von Verarbeitungsparameter (zb. Photonenempfindlichkeit)
- Custom-Maske zur genaueren Positionsanpassung des Interferenzmusters
