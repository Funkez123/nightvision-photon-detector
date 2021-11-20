# -*- coding: utf-8 -*-
### wichtig für Unix basierte Systeme -  Verarbeitung deutscher Umlaute

# importieren von Bibliotheken

import cv2
import numpy as np
import os, time
from matplotlib.ticker import NullFormatter
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
matplotlib.use('TkAgg')
from scipy.stats import poisson
from scipy.special import factorial
import scipy.stats as stats
import scipy.special
import math
import PySimpleGUI as sg
import os.path
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
matplotlib.use('TkAgg')

##############################################################################

############# VARIABLEN-DEKLARIERUNG #######################################

hotpixel_th = 130  ##Schwellenwert für das Erste Hotpixel abbild und dessen Differenz  (130 klappt ganz gut)
filename = "empty" ## Platzhalter für die Verwendete Videodatei
max_x = 0 ## maximalwert der Photonen für die Poissonverteilung (bessere Skalierung des Graphen)
videoanzeigen = False ## Zeigt das Ausgangsvideo bei der Verarbeitung standartmäßig nicht
nphotons = 0  ## Deklarierung der Variable für die Anzahl der Photonen (bei 0)
slider_fps = 25  ## Bilder Pro sekunde, die standartmäßig für die Verarbeitung verwendet werden
empfindlichkeit = 11  ## Photonenempfindlichkeits-Schwellwert bei einer Lichtintensitätsabweichung von x+11 (von 0-255)
min_photons = 5 ## photonenmindestanzahl (auch im slider) um keine Daten bei ausgeschaltetem Nachtsichtgerät zu sammeln
imghisto_array = []  ## Histogram - Array
pho_smoothing = 200     ## N(x)-Diagramm Smoothing, bzw rückläufig die Anzahl der Photonen für die Erstellung des Diagramms
yx_coords = [0,0]     ## 2-Dimensionales Array
sg_graph_flag = None   ## Flagge für die Erstellung des Diagramms in (PySimpleGUI)
webcam_select = 0 ## 0 als die Standartwebcam
video_var = 0 ## Nummer des aktuell dargestellten Frames links / bzw dessen Zustand in den einzelnen Bearbeitungsstadien
##############################################################################


########################### Startseite - Benutzeroberfläche ##################

sg.theme('Lightgrey')  ## Die Benutzeroberfläche sieht mit Themes etwas besser aus

################## Rechte Spalte UI #######################

file_list_column = [
    [
        sg.Text("Videoverzeichnis"),
        sg.In(size=(25, 1), enable_events=True, key="-FOLDER-"),
        sg.FolderBrowse(), ### Dateibrowser
    ],
    [
        sg.Listbox(
            values=[], enable_events=True, size=(40, 20), key="-FILE LIST-"
        )
    ],
]
################################################################################

#####################  Linke Spalte UI ###################

second_column = [
    [sg.Text("Ausgewähltes Video : ")],
    [sg.Text(size=(45, 2), key="-TOUT-")],
    [sg.Text("_________________________")],
    [sg.Image(key="-IMAGE-")],
    [sg.Button("Mit Videodatei fortfahren")],
    [sg.Button("Mit Webcam fortfahren")],
    [sg.Text(" ")],
    [sg.Text("Falls mehrere Webcams eingerichtet sind, bitte Nummer variieren:")],
    [sg.Text("Verwendung von Webcam-Nummer : ")],
    [sg.Slider((0,4),webcam_select,1,orientation="h",size=(20,15),key="webcam_key")],
    [sg.Text('Anzeigegeschwindigkeit (höher = schneller):', size=(35, 1), font='Helvetica 14')],
    [sg.Slider((1,100),slider_fps,1,orientation="h",size=(40,15),key="fps_key")],
]


################### Gesamtes Layout / Zusammensetzung der ersten Seite ###################

layout = [
    [sg.Text('Photonenkamera-Software-V0.15',justification='center', size=(42, 1), font='Helvetica 22'),sg.Button('Version')],
    [sg.Text(" ",justification='center')],
    [sg.Text("Videodatei bitte auswählen oder Zugang zur Webcam bestätigen.",justification='center')],
    [sg.Text("Photonenerkennung startet automatisch sobald eine der Optionen ausgewählt wird.",justification='center')],
    [sg.Text("Bitte nur Videodateien in 720x576px Auflösung auswählen",justification='center')],
    [sg.Text("Unterstützte Formate : MP4 | MOV | MPV",justification='center', font='Helvetica 12')],

    [
        sg.Column(file_list_column),
        sg.VSeperator(),   ## Vertikale Trennung zwischen Layoutspalten
        sg.Column(second_column),
    ]
]

window = sg.Window("Photonenanalyse-Tool", layout)  ## zeigt die Seite an

########################################################################

############       Eventloop der ersten Seite ##########################

while True:   #### Auswahl der Videodatei oder der Webcam als Quelle ####

    event, values = window.read()
    if event == "Exit" or event == sg.WIN_CLOSED:
        webcamvar = False
        break

    if event == "Mit Videodatei fortfahren" or event == sg.WIN_CLOSED:
        webcamvar = False
        break

    if event == "Mit Webcam fortfahren":
        webcamvar = True
        break

    if event == 'Version':
        sg.popup_scrolled(sg.get_versions())


### Bestimmt ob ein Webcam oder der Videofeed-verwendet wird

    if values["fps_key"]:
        slider_fps = values['fps_key']

    if values["webcam_key"]:
        webcam_select = values['webcam_key']

# Erstellt eine Liste der verfügbaren Ordner bzw Dateien ##

    if event == "-FOLDER-":
        folder = values["-FOLDER-"]
        try:
            # Liste der Dateien im Verzeichnis ....

            file_list = os.listdir(folder)

        except:
            file_list = []  ## ...außer die Liste ist leer

        fnames = [
            f
            for f in file_list
            if os.path.isfile(os.path.join(folder, f))  ## Pfad zu den Dateien
            and f.lower().endswith((".mp4", ".mpg", ".mpv"))  ## Dateitypen mp4 und mpg als Quelle

        ]

        window["-FILE LIST-"].update(fnames)  ##aktualisiert die Ordneransicht mit den Vorhanden dateien

    elif event == "-FILE LIST-":  # Wenn eine Datei ausgewählt wurde, dann :

        try:
            filename = os.path.join(
                values["-FOLDER-"], values["-FILE LIST-"][0]

            )

            window["-TOUT-"].update(filename)  ## Diese Datei als Text anzeigen
            window["-IMAGE-"].update(filename=filename)  ## Diese Datei in einer Variable festhalten


        except:
            pass

window.close()    ##### Fenster schließen wenn es fertig ist

#####################################################################################


########################### Teil Zwei des Codes #####################################

######## kontrolliert ob die Webcam oder das Video der Videoinput sein sollet

if webcamvar == False:    ### Photonenerkennung mit Video
    if filename != "empty":
        cap = cv2.VideoCapture(filename)
        num_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)  ## Anzahl der Frames des Videos herausfinden
    else:
        sg.Popup('Keine Videodatei ausgewählt, bitte wiederholen..', keep_on_top=True)

if webcamvar == True:    ## Webcam einrichtung
    cap = cv2.VideoCapture(webcam_select)
################ Hotpixel-Korrektur ################


# ließt den ersten Frame und speichert diesen als hotpixel_vorlage
success, image = cap.read()
if success:
    computeresolution = [720,576]
    image = cv2.resize(image,computeresolution, interpolation=cv2.INTER_LINEAR)
    cv2.imwrite("hotpixel_vorlage.jpg", image)  # speichert Frame als JPG

# ließt diesen Frame
src = cv2.imread('hotpixel_vorlage.jpg', 0)
cv2.destroyAllWindows()
# berechnet ein B/W Bild mit einem festgelegten Schwellenwert
th, dst = cv2.threshold(src, hotpixel_th, 255, cv2.THRESH_BINARY);
# speichert ihn als opencv-thresh-binary.jpg (für referenz später)
cv2.imwrite("opencv-thresh-tobinary.jpg", dst);

# src = cv2.imread('v1.png',0)
mask = dst
mask_inv = cv2.bitwise_not(mask)  ##Bitwise_not operation bildet Inversion der Maske

frame_width = int(cap.get(3))  ##fragt die breite und höhe für das speichern des Videos an
frame_height = int(cap.get(4))

size = [frame_width, frame_height]

################################################################################

###### Einrichtung von Variablen/Arrays bevor der Code weiter ausgeführt wird

count = 0  ## Zähler variable für den einzelnen Frame
phot_anzahl = np.array([]) ### Array mit den Anzahlen der Photonen je Frame (erweitert sich automatisch)

#################################################################################


Photonen_column = [                 ### Layout der linken Spalte im Fenster
          [sg.Text('Photonenanalyse-Software', font='Helvetica 22')],
          [sg.Text('Die Verarbeitung der Bilddaten startet automatisch:', size=(40, 1), font='Helvetica 14')],
          [sg.Text('Videofeed links: aktueller Verarbeitungsschritt', size=(40, 1), font='Helvetica 12')],
          [sg.Text('Videofeed rechts : Interferenzmuster-Photonen', size=(40, 1), font='Helvetica 12')],
          [sg.Text('Ausgangsvideodaten:', size=(25, 1), font='Helvetica 16')],
          [sg.Image(filename='', key='-image-')],
          [sg.Text('Videofeed Nr.: ', size=(20, 1), font='Helvetica 12'),
          sg.Slider((0,5),video_var,1,orientation="h",size=(20,15),key="left_vid")],
          [sg.Text('Frame-Nummer:', size=(40, 1), font='Helvetica 12'),
          sg.Text(count, size=(10, 1), font='Helvetica 12', key='framecount')],
          [sg.Button("Ausgangsvideo anzeigen"),
          sg.VSeperator(),   ## Vertikale Trennung zwischen Layoutspalten
          sg.Button("Vorgang stoppen"),
          sg.VSeperator(),   ## Vertikale Trennung zwischen Layoutspalten
          sg.Button("Poissonverteilung / Matplotlib")],
          [sg.Text('Photonenempfindlichkeit: ', size=(20, 1), font='Helvetica 20'),
          sg.Slider((0,50),empfindlichkeit,1,orientation="h",size=(20,15),key="Photonenempfindlichkeit")],
          [sg.Text('Mindestphotonenpixel: ', size=(20, 1), font='Helvetica 20'),
          sg.Slider((0,10),5,1,orientation="h",size=(20,15),key="Mindestphotonenpixel")],
          [sg.Text('Verarbeitungsgeschwindigkeit: ', size=(25, 1), font='Helvetica 16')],
          [sg.Slider((1,100),slider_fps,1,orientation="h",size=(50,15),key="fps_key2")]

]


matplotlib_column = [   ### Layout der rechten Spalte
        [sg.Text('Photonenanzahl im aktuellen Frame:', size=(40, 1), font='Helvetica 16'),
        sg.Text(nphotons, size=(10, 1), font='Helvetica 16', key='matplotcolumnphotontext')],
        [sg.Text(' ', size=(40, 1), font='Helvetica 16')],
        [sg.Text(' ', size=(10, 1), font='Helvetica 16'),
        sg.Image(filename='', key='-image_right-')],
        [sg.Button("N(x)-Diagramm"),
        sg.Text('Photonensmoothing: ', size=(20, 1), font='Helvetica 16'),
        sg.Slider((0,300),pho_smoothing,1,orientation="h",size=(20,15),key="Photonensmoothing")],
        [sg.Checkbox('Automatisch N(x)-Graph aktualisieren (50 Frames Interval)', default=True, key="refresh_checkbox")],
        [sg.Canvas(size=(600,300),key='canvas')]
]


layout = [
[
    sg.Column(Photonen_column),
    sg.VSeperator(),   ## Vertikale Trennung zwischen Layoutspalten
    sg.Column(matplotlib_column),
]
]

window = sg.Window('Photonenerkennung', layout, no_titlebar=False, location=(0, 0))  ## GUI einrichtung

image_elem = window['-image-']                                ## Aktualisieren der Bildelemente in der GUI
image_elem_right = window['-image_right-']

######################################################

############### Zeichnen der Histogramme ########################


def draw_poisson_histo():  # definiert eine neuen Befehl (kann global aufgerufen werden)
    sample = np.random.poisson(phot_anzahl)  ## erstellt eine Menge von Zahlenwerten für das Histogram
    bin = np.arange(0,max_x,2)  ## Array für die einzelnen Balken des Histograms, Interval 1, von 0 bis maximalwert der Photonen
    ## Bin-/Intervall-Größe absichtlich auf 2 statt 1 gestellt um die Lesbarkeit zu verbessern (wird später durch Lambda * 2 für die Poissonverteilung kompensiert)
    fig, ax1 = plt.subplots()
    fig.subplots_adjust(left=0.2, wspace=0.6)
    ax1.set_ylabel('Photonenwahrscheinlichkeit')
    n, bins, patches = ax1.hist( sample, bins=bin, color='lightgreen', label='Photonenverteilung')  ## Das Histogram der Photonenverteilung
    y_max1 = n.max() ##findet den Höchsten Wert aus der Photonenverteilung für die Skalierung der Poisson verteilung
    t = np.arange(0, max_x, 0.1)  ## zweites Array für die Poissonverteilung (genaueres Interval als das für die Photonenverteilung)
    lmd = (np.median(sample))  ## Auslesen des Erwartungswertes aus dem Histogram
    first = (np.power(lmd,t)/scipy.special.factorial(t)) ## (Lambda ^ x) / X!
    second = np.power(2.71828,-lmd)  ## Eulersche Zahl ^ - Lambda
    d = first * second  ## Berechnet den Wahrscheinlichkeitswert für P(X=x) mit der Poisson-Formel
    y_max2 = max(d)  ## maximalwert der Poisson verteilung
    ax2 = ax1.twinx()
    ax2.set_ylabel('Poissonverteilung')
    ax2.set_xlabel('Photonenanzahl')
    ax2.plot(t, d, color='red', label='Poisson')   ##plottet den zweiten Graphen
    plt.title('Häufigkeitsverteilung')
    fig.tight_layout()
    plt.show() ## zeigt die Diagramme an

#################################################################################


def draw_interference_histo():  ## Zeichnet das Interferenz-Diagramm in einem neuen Fenster

    fig, sub1 = plt.subplots()

    bin = np.arange(0,dimension[0],1)
    n, bins, patches = sub1.hist(imghisto_array[(np.size(imghisto_array)-int(pho_smoothing)):np.size(imghisto_array)], bins=bin, color='lightgreen', label='X-Verteilung')
    sub2 = sub1.twinx()
    sub2.plot(bins[0:179], n, label='erfasste Lichtintensität')
    sub1.set_ylabel('erfasste Lichtintensität')
    sub2.set_xlabel('x-Koordinaten der Frames')
    plt.show()

#####################################################

################# Funktionen für das neuzeichnen des Graphen in PySimpleGUI #######################

def fig_maker(window): # sollte man eigentlich threaden damit es nicht alles kurz aufhängt
    fig, sub1 = plt.subplots()
    bin = np.arange(0,dimension[0],1)
    n, bins, patches = sub1.hist(imghisto_array[(np.size(imghisto_array)-int(pho_smoothing)):np.size(imghisto_array)], bins=bin, color='lightgreen', label='X-Verteilung')
    sub2 = sub1.twinx()
    sub2.plot(bins[0:179], n, label='N(x)-Diagramm')
    sub2.set_ylabel('erfasste Lichtintensität')
    plt.title('N(x)-Diagramm')
    window.write_event_value('-THREAD-', 'done.')
    time.sleep(0.01)

    return plt.gcf()  ## gibt das Diagramm aus


def draw_figure(canvas, figure, loc=(0, 0)):
    figure_canvas_agg = FigureCanvasTkAgg(figure, canvas)
    figure_canvas_agg.draw()
    figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)
    return figure_canvas_agg


def delete_sg_graph_flag(sg_graph_flag):
    sg_graph_flag.get_tk_widget().forget()
    plt.close('all')

###############################################################

############# Hauptloop des Programms #########################

while cap.isOpened():
    ret, frame = cap.read()  ##ließt aktuellen Frame

    if frame is None: ## If - Abfrage um zu schauen ob es noch weitere Frames gibt die man bearbeitet kann (zum Vermeiden von OpenCV2 Fehlern)
        draw_poisson_histo()
        draw_interference_histo() ## Interferenz-Histogram
        break

    else:

        ###### "Ließt" das Fenster für die PySimpleGUI verwendung von OPENCV2 , aka Synchronizierung der Fensteraktualisierung

        event, values = window.read(timeout=0)
        if event in ('Exit', None):
            break
        ret, frame = cap.read()
        if not ret:  # Falls keine Daten mehr vorhanden sind, dann :
            draw_poisson_histo()  ## wenn das Video fertig ist wird der Matplotlib Graph gezeichnet
            break

        time.sleep(float(1/slider_fps))  ## berechnet die "sleep" um die FPS zu erreichen, aka 1/fps
        # if - Falls der Frame lesbar ist, dann / sonst:
        computeresolution = [720,576]
        frame = cv2.resize(frame,computeresolution, interpolation=cv2.INTER_LINEAR)
        masked = cv2.bitwise_and(frame, frame, mask=mask_inv)  ## Bildet die Maske ab -- Differenzbild
        if not ret:
            print("Can't receive frame (stream end?). Exiting ...")
            break

        gray = cv2.cvtColor(masked, cv2.COLOR_BGR2GRAY)  ##Graustufenkonvertierung für einheitliches 0-255 Bild
        median = cv2.medianBlur(gray, 5)  ## medianBlur filter für ein "glatteres" Bild ohne große Hotpixelfehler

        m = cv2.mean(median);  ## Mittelwert des Bildes für späteren Schwellenwert eintreffender Photonen
        ##print(m)

        th2, photons = cv2.threshold(median, round(m[0] + empfindlichkeit), 255,  ## Slider bestimmt die Empfindlichkeit
                                     cv2.THRESH_BINARY);  ## Kontrastbild der Photonen mit Korrektur

        gray2 = cv2.cvtColor(photons, cv2.COLOR_GRAY2BGR)
        medianphotons = cv2.medianBlur(gray2, 1)

    ##### reduced resolution method ####

        framed = photons
        dimension = (180,144)
        framedresize = cv2.resize(framed,dimension, interpolation=cv2.INTER_LINEAR)

        correctionmask = np.zeros(framedresize.shape[:2], dtype="uint8")
        cv2.rectangle(correctionmask, (65,75),(130,100), 1,-1)  ## Standartmäßige Maske wenn sonst nicht anders bestimmt

        framed2 = cv2.bitwise_and(framedresize, framedresize, mask=correctionmask)
        nphotons = cv2.countNonZero(framed2) ### Zählung der Photonen im Bild
        InterferenceBig = cv2.resize(framed2,(360,288), interpolation=cv2.INTER_NEAREST)  ## Hochskalierung des Bildes zur besseren Sichtbarkeit in der UI

        window['framecount'].update(count)

    ##################################

    ########### Photonen-Array-Erstellung und Checkup #######################################

        if nphotons > min_photons:
            phot_anzahl = np.append(phot_anzahl,[nphotons]) ### erstellt ein langes Array mit allen Photonenanzahlen, neuste Anzahl an das Ende des Array angehangen
            window['matplotcolumnphotontext'].update(nphotons)   ### Aktualisiert die Photonenanzahl im Text der UI

            imghisto_array = np.append(imghisto_array,[yx_coords[1]])    #### entnimmt die X-Koordinaten der Photonen

            if nphotons > max_x:   ## aktualisiert die maximale Photonenanzahl (später für Statistik bedeutsam)
                max_x = nphotons

        ###########################   Video-Konvertierung für PySimpleGUI (Links )#############################

        def video_left_select(slider_vid_wert):
            if slider_vid_wert == 0:
                imgbytes = cv2.imencode('.png', cv2.resize(frame,(540,432), interpolation=cv2.INTER_NEAREST))[1].tobytes()  # ließt die Daten der OpenCV frames aus, schreibt diese in ein Array und bereitet es für PySimpleGUI vor
                image_elem.update(data=imgbytes)
            elif slider_vid_wert == 1:
                imgbytes = cv2.imencode('.png',cv2.resize(masked,(540,432), interpolation=cv2.INTER_NEAREST))[1].tobytes()  # ließt die Daten der OpenCV frames aus, schreibt diese in ein Array und bereitet es für PySimpleGUI vor
                image_elem.update(data=imgbytes)
            elif slider_vid_wert == 2:
                imgbytes = cv2.imencode('.png', cv2.resize(gray,(540,432), interpolation=cv2.INTER_NEAREST))[1].tobytes()  # ließt die Daten der OpenCV frames aus, schreibt diese in ein Array und bereitet es für PySimpleGUI vor
                image_elem.update(data=imgbytes)
            elif slider_vid_wert == 3:
                imgbytes = cv2.imencode('.png',cv2.resize(median,(540,432), interpolation=cv2.INTER_NEAREST))[1].tobytes()  # ließt die Daten der OpenCV frames aus, schreibt diese in ein Array und bereitet es für PySimpleGUI vor
                image_elem.update(data=imgbytes)
            elif slider_vid_wert == 4:
                imgbytes = cv2.imencode('.png', cv2.resize(photons,(540,432), interpolation=cv2.INTER_NEAREST))[1].tobytes()  # ließt die Daten der OpenCV frames aus, schreibt diese in ein Array und bereitet es für PySimpleGUI vor
                image_elem.update(data=imgbytes)
            elif slider_vid_wert == 5:
                imgbytes = cv2.imencode('.png', cv2.resize(medianphotons,(540,432), interpolation=cv2.INTER_NEAREST))[1].tobytes()  # ließt die Daten der OpenCV frames aus, schreibt diese in ein Array und bereitet es für PySimpleGUI vor
                image_elem.update(data=imgbytes)

        video_left_select(video_var) ## wählt das gezeigte Video links aus
        ######################################################################################

        ################################ Video rechts (Konvertierung )#########################################

        imgbytes_right = cv2.imencode('.png', InterferenceBig)[1].tobytes()  # ließt die Daten der OpenCV frames aus, schreibt diese in ein Array und bereitet es für PySimpleGUI vor
        image_elem_right.update(data=imgbytes_right)

        ########################################################################################

        ##############  Abfrage der UI-Werte (aka. Knöpfe / Schieberegler / Checkboxen ... ) ########

        if values["refresh_checkbox"] == True:
            if count % 50 == 0:   ## Aktualisierung nach 50 Frames (% = Modulo-Operator)
                if sg_graph_flag is not None:
                    delete_sg_graph_flag(sg_graph_flag)
                fig = fig_maker(window)
                sg_graph_flag = draw_figure(window['canvas'].TKCanvas, fig)

        if event == "Ausgangsvideo anzeigen":
            videoanzeigen = True

        if videoanzeigen == True:
           cv2.imshow('mask auf dem Video', gray)  ## zeigt alle Bilder und stufen
           cv2.imshow('resize method', framedresize)

        if event == "Vorgang stoppen":
               break

        if event == "Poissonverteilung / Matplotlib":
            draw_poisson_histo()

        if event == "N(x)-Diagramm":
            if sg_graph_flag is not None:
                delete_sg_graph_flag(sg_graph_flag)
            fig = fig_maker(window)
            sg_graph_flag = draw_figure(window['canvas'].TKCanvas, fig)

        if values["Photonenempfindlichkeit"]:
            empfindlichkeit = values["Photonenempfindlichkeit"]

        if values["Photonensmoothing"]:
            pho_smoothing = values["Photonensmoothing"]

        if values["fps_key2"]:
            slider_fps = values['fps_key2']

        if values["left_vid"]:
            video_var = values['left_vid']

        if values["Mindestphotonenpixel"]:
            min_photons = values["Mindestphotonenpixel"]
    #############################################################

    ######################## Findet X Coordinaten der Photonen ###################

        yx_coords = (np.where(framed2 > 0))

 ############################################################################

        count += 1  ## Fügt dem Framezähler 1 hinzu

    if cv2.waitKey(5) == ord('q'):  ## gibt jedem Frame 5ms zeit
        videoanzeigen = False
        cv2.destroyAllWindows()

cap.release()  ## openCV - Ende der Darstellung im Fenster
cv2.destroyAllWindows()
