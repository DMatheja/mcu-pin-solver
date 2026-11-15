# Neuro-Symbolische Hardware-Verifikation von LLM-generiertem Embedded-C++-Code mittels AST-Analyse und Z3 MaxSMT

**Thema:** Konzeption, Architektur und Implementierung einer datengetriebenen Pre-Build-Pin-Verifikation für PlatformIO (`mcu-pin-solver`)  
**Projekt-Repository:** `https://github.com/DMatheja/mcu-pin-solver.git`  
**PlatformIO Registry:** `dmatheja/mcu-pin-solver` (Version `0.1.0`)

---

## Kurzfassung

Große Sprachmodelle (Large Language Models, LLMs) sind inzwischen in der Lage, in kürzester Zeit funktionalen und syntaktisch korrekten Embedded-C++-Code für Mikrocontroller zu erzeugen. Bei der Vergabe physikalischer Anschlussnummern (GPIOs) unterlaufen ihnen jedoch regelmäßig gravierende Fehler: Sie verwenden Pins, an denen intern der Programmspeicher hängt, nutzen analoge Eingänge parallel zu einer aktiven WLAN-Schnittstelle, obwohl sich beide im Chip dieselbe Hardware teilen, oder überschreiben Leitungen, die eigentlich für den Bootvorgang oder die USB-Kommunikation reserviert sind. Da ein regulärer C++-Compiler Pin-Nummern lediglich als gewöhnliche Ganzzahlen betrachtet, bleiben solche Fehler beim Übersetzen unbemerkt und führen erst auf der realen Platine zu Abstürzen oder unerklärlichem Fehlverhalten.

Die vorliegende Studienarbeit dokumentiert Entwurf, Umsetzung und Architektur von **mcu-pin-solver**, einem Werkzeug zur automatisierten Hardware-Prüfung vor dem eigentlichen Kompiliervorgang. Der Grundgedanke folgt dem von Kambhampati et al. beschriebenen **LLM-Modulo-Prinzip** [1]: Das Sprachmodell erzeugt weiterhin den Programmcode, die Prüfung auf physikalische Zulässigkeit wird jedoch vollständig an ein deterministisches, mathematisches Prüfverfahren ausgelagert. Hierzu zerlegt ein C++-Syntaxbaum-Parser auf Basis von `tree-sitter-cpp` [6] das Projekt (inklusive mehrerer Quell- und Header-Dateien) in formale Pin-Anforderungen und aktive Peripheriemodule. Anschließend prüft der SMT-Solver **Z3** [3, 4] diese Anforderungen gegen eine austauschbare JSON-Hardwarebeschreibung des Zielchips. Bei einem Konflikt bricht ein PlatformIO-Pre-Build-Hook den Build sofort ab und formuliert einen präzisen, minimal-invasiven Reparaturvorschlag, mit dem das Sprachmodell den Code gezielt korrigieren kann.

---

## Inhaltsverzeichnis

- [[#1. Einleitung und Problemstellung]]
  - [[#1.1 Warum ein C++-Compiler Hardware-Fehler nicht sieht]]
  - [[#1.2 Typische Fehlerklassen in LLM-generiertem Embedded-Code]]
  - [[#1.3 Zielsetzung der Arbeit]]
- [[#2. Theoretische Grundlagen und Lösungsansatz]]
  - [[#2.1 Warum statistische Sprachmodelle allein scheitern — und was „neuro-symbolisch“ bedeutet]]
  - [[#2.2 Das LLM-Modulo-Prinzip]]
  - [[#2.3 Abstrakter Syntaxbaum (AST) statt reiner Textsuche]]
  - [[#2.4 SAT, SMT und MaxSMT mit Z3]]
- [[#3. Systemüberblick und Ablauf im Build-Prozess]]
- [[#4. Detaillierte Architektur und Begründung der Entwurfsentscheidungen]]
  - [[#4.1 Deklarative Hardware-Profile]]
  - [[#4.2 Quelltextanalyse mit Tree-Sitter]]
  - [[#4.3 Formale Prüfung und Reparaturberechnung mit Z3]]
  - [[#4.4 Berichtsgenerierung und Kommandozeilensteuerung]]
  - [[#4.5 Integration als PlatformIO-Bibliothek]]
- [[#5. Evaluierung anhand von Testszenarien und Praxisbetrieb]]
  - [[#5.1 Automatisierte Szenario-Testsuite]]
  - [[#5.2 Praxisbetrieb über die PlatformIO Registry]]
- [[#6. Kritische Würdigung, Grenzen und Ausblick]]
  - [[#6.1 Erreichte Qualität und bekannte Grenzen des aktuellen Stands]]
  - [[#6.2 Ideen für weiterführende Ausbaustufen]]
- [[#7. Literaturverzeichnis]]

---

## 1. Einleitung und Problemstellung

### 1.1 Warum ein C++-Compiler Hardware-Fehler nicht sieht

In der klassischen Anwendungsentwicklung fängt ein Compiler zusammen mit seinem Typsystem bereits vor der Ausführung einen Großteil typischer Programmierfehler ab. Wer einer Funktion einen falschen Datentyp übergibt oder ein nicht existierendes Symbol referenziert, erhält sofort eine eindeutige Fehlermeldung. In der Mikrocontroller-Programmierung — insbesondere im weit verbreiteten Arduino- und PlatformIO-Ökosystem — greift dieser Schutzmechanismus bei der Hardware-Ansteuerung kaum.

Der Grund liegt in der Art, wie Anschlüsse eines Mikrocontrollers im Quelltext repräsentiert werden. Ein LED-Ausgang, ein analoger Sensor oder ein Bus-Signal wird fast immer als schlichte Ganzzahl notiert, etwa als Makro `#define STATUS_LED 12` oder als Konstante `const int SOIL_SENSOR = 5;`. Aus Sicht des C++-Compilers ist die Zahl `12` ebenso gültig wie die Zahl `8`. Dass auf einem bestimmten Mikrocontroller — etwa dem Espressif ESP32-C3 — an GPIO `12` fest der interne SPI-Flash-Speicher angeschlossen ist [7] und ein Umschalten dieses Pins das laufende Programm zum Absturz bringt, liegt außerhalb des Sichtfelds des Compilers.

### 1.2 Typische Fehlerklassen in LLM-generiertem Embedded-Code

Wer sich von einem Sprachmodell ein Firmware-Gerüst generieren lässt, stößt in der Praxis immer wieder auf fünf charakteristische Fehlerarten, die aus dem Zusammenspiel von C++-Quelltext und elektronischer Chip-Architektur entstehen:

1. **Verwendung intern reservierter System-Pins:** Auf vielen modernen System-on-Chips sind einzelne GPIO-Nummern nach außen überhaupt nicht frei verfügbar, weil darüber der externe oder integrierte Flash-Speicher sowie optionaler PSRAM über die internen SPI0/SPI1-Controller angebunden sind — beispielsweise GPIO `12–17` beim ESP32-C3 [7] oder die Quad-/Octal-SPI-Leitungen GPIO `26–37` beim ESP32-S3 [8]. Ebenso halluzinieren Sprachmodelle gelegentlich Pin-Nummern, die auf dem gewählten Chip schlicht nicht herausgeführt sind (wie GPIO `22–25` beim ESP32-S3 [8] oder GPIO `32` beim ESP32-C3 [7]).
2. **Kontextabhängige Peripheriekonflikte:** Manche Pins sind im Grundzustand völlig legitim, verlieren ihre Nutzbarkeit jedoch sobald im Programm ein bestimmtes Hardware-Subsystem gestartet wird. Ein bekanntes Beispiel bei ESP32-Mikrocontrollern ist der zweite Analog-Digital-Wandler (`ADC2`): Sobald das WLAN-Modul (`WiFi.begin(...)` oder `WiFi.softAP(...)`) aktiviert wird, beansprucht der Funk-Treiber interne Pfade des `ADC2`-Subsystems [7]. Während `analogRead(5)` auf einem ESP32-C3 ohne WLAN funktioniert, schlägt die Messung fehl, sobald eine Funkverbindung aufgebaut wird; nur `ADC1` (beim ESP32-C3 GPIO `0–4` [7], beim ESP32-S3 GPIO `1–10` [8]) bleibt dauerhaft nutzbar. Ein verwandtes Problem entsteht beim nativen USB-Serial-Controller (`Serial.begin(...)`): Auf dem ESP32-C3 belegt die USB-Verbindung die Pins `18` und `19` [7], auf dem ESP32-S3 die Pins `19` und `20` [8]. Werden diese Leitungen gleichzeitig als normale digitale Ausgänge genutzt, bricht entweder die USB-Kommunikation ab oder der Ausgang funktioniert nicht.
3. **Verletzung der Pin-Multiplexing-Fähigkeiten:** Nicht jeder physikalische Anschluss beherrscht jede elektrische Funktion. Wird `analogRead(...)` auf einen Pin ohne Analog-Digital-Wandler gelegt (etwa GPIO `6` beim ESP32-C3 [7]), liefert der Aufruf zur Laufzeit keine gültigen Messwerte.
4. **Doppelbelegungen versus gewollte Bus-Teilung:** Zwei unabhängige Verbraucher — beispielsweise eine Status-LED und ein Relais — dürfen niemals denselben Pin beanspruchen. Anders verhält es sich jedoch bei seriellen Bussen wie **I2C** oder **SPI**: Mehrere Sensoren und Displays teilen sich hier ausdrücklich dieselbe Takt- (`SCL`) und Datenleitung (`SDA`). Ein Prüfwerkzeug muss daher unterscheiden können, wann zwei Signale kollidieren und wann sie denselben Bus gemeinsam nutzen.
5. **Unbedachte Belegung von Boot- und Strapping-Pins:** Mikrocontroller lesen während des Einschaltens oder Resets bestimmte Pins (sogenannte *Strapping-Pins*, etwa GPIO `2, 8, 9` beim ESP32-C3 [7] oder `0, 3, 45, 46` beim ESP32-S3 [8]) ein, um den Startmodus (normaler Flash-Boot oder Download-Modus) festzulegen. Zieht eine angeschlossene Schaltung einen solchen Pin beim Start auf einen ungünstigen Spannungspegel, startet der Chip nicht in die Firmware.

### 1.3 Zielsetzung der Arbeit

Vor diesem Hintergrund entstand im Rahmen dieser Studienarbeit das Softwarepaket **mcu-pin-solver**. Es verfolgt vier konkrete Ziele:

- **Vollständige Erklärbarkeit und Transparenz:** Das Gesamtsystem soll bewusst kompakt und modular aufgebaut bleiben, sodass jede Komponente ohne unnötige Abstraktionsschichten nachvollziehbar ist.
- **Prüfung vor der Kompilierung:** Fehlerhafte Pin-Zuweisungen sollen innerhalb des regulären PlatformIO-Build-Ablaufs erkannt und blockiert werden, bevor Toolchain und Linker anlaufen.
- **Konstruktive statt bloß ablehnender Rückmeldung:** Das System soll nicht nur mitteilen, *dass* ein Fehler vorliegt, sondern automatisch eine gültige Alternativbelegung berechnen, die möglichst wenige bereits funktionierende Pins des Programms anfasst.
- **Unabhängigkeit von einzelnen Chips:** Sämtliche Hardware-Eigenheiten müssen sauber von der Python-Programmlogik getrennt in deklarativen JSON-Dateien liegen, sodass sich neue Mikrocontroller (wie STM32, RP2040 oder AVR) ohne Änderung am Quellcode des Validators ergänzen lassen.

---

## 2. Theoretische Grundlagen und Lösungsansatz

Um das Zusammenspiel der Komponenten von **mcu-pin-solver** vollständig zu verstehen, lohnt sich vorab ein Blick auf die verwendeten Konzepte aus der Künstlichen Intelligenz, dem Compilerbau und der formalen Logik.

### 2.1 Warum statistische Sprachmodelle allein scheitern — und was „neuro-symbolisch“ bedeutet

Moderne LLMs gehören zu den *neuronalen* (statistischen) Systemen: Sie berechnen anhand gelernter Wahrscheinlichkeiten aus großen Textkorpora, welche Token-Folge als Nächstes plausibel erscheint. Wie Kambhampati et al. herausarbeiten, agieren autoregressive Sprachmodelle damit prinzipiell als hochentwickelte statistische Mustererkenner und können weder verlässliche mehrstufige Planung noch eine echte formale Selbstverifikation leisten [1]. Ein Sprachmodell versteht ausgezeichnet, wie eine Arduino-Schleife aufgebaut ist, wie man einen Wi-Fi-Access-Point initialisiert und welche API-Aufrufe zusammenpassen. Es besitzt jedoch keinen eingebauten, fehlerfreien Mechanismus zur Bedingungsprüfung (*Constraint Satisfaction*): Wenn ein ESP32-C3 zufällig in vielen Trainingsbeispielen `LED = 12` oder `SENSOR = 5` verwendet hat, reproduziert das Modell diese Zahlen selbst dann, wenn drei Zeilen weiter unten `WiFi.begin(...)` steht und der Nutzer im Prompt das Datenblatt beigefügt hat.

Dem gegenüber stehen *symbolische* Verfahren aus der klassischen Künstlichen Intelligenz (in der Einteilung nach Garcez und Lamb die „erste Welle“ der KI [2]): Algorithmen, die mit expliziten Regeln, logischen Formeln und mathematischen Beweisern arbeiten. Sie können keinen kreativen Programmcode entwerfen, liefern auf einem wohldefinierten Regelwerk jedoch deterministische, überprüfbare Aussagen darüber, ob Bedingungen erfüllt sind oder sich widersprechen.

Ein System, das die Mustererkennung neuronaler Modelle („zweite Welle“) mit der transparenten, formalen Beweiskraft symbolischer Logik zu einer **dritten Welle** integriert, bezeichnen Garcez und Lamb als **neuro-symbolische KI** [2]. Genau diese Arbeitsteilung greift im Projekt: Das Sprachmodell übernimmt die kreative Software-Synthese, während ein symbolischer Prüfer den physikalischen Realitätsabgleich erzwingt.

### 2.2 Das LLM-Modulo-Prinzip

Die konkrete Software-Architektur dieser Kopplung folgt den von Kambhampati et al. auf der ICML 2024 vorgestellten **LLM-Modulo-Frameworks** [1]. Der Begriff ist bewusst in Anlehnung an *SAT Modulo Theories* (SMT) [5] gewählt: So wie ein SMT-Verfahren einen allgemeinen booleschen Suchkern mit spezialisierten Theorielösern verbindet, kombiniert eine LLM-Modulo-Architektur ein LLM als universellen, aber unvollkommenen Ideengeber (*approximate knowledge / candidate generator*) mit externen modellbasierten Kritikern und Verifizierern [1].

In einer bidirektionalen Schleife übernimmt jeder Akteur genau die Aufgabe, die er strukturell beherrscht [1]:

1. **Generierung:** Das LLM schreibt den C++-Code inklusive erster Pin-Vorschläge.
2. **Extraktion:** Ein deterministischer Parser übersetzt den Quelltext in ein formales Hardware-Modell (welche Pins werden angefordert, für welche Funktion werden sie genutzt und welche Chip-Module werden gestartet?).
3. **Formale Verifikation:** Ein symbolischer Kritiker (hier der Z3-Solver [3, 4]) prüft, ob sämtliche Hardware-Regeln gleichzeitig erfüllbar sind.
4. **Reparatur-Feedback:** Ist das Ergebnis zulässig (**`SAT`**, abgeleitet von *satisfiable*, erfüllbar), wird der Code ohne Eingriff kompiliert. Gibt es einen Widerspruch (**`UNSAT`**, *unsatisfiable*), bricht die Pipeline ab und generiert eine exakt spezifizierte Korrekturanweisung (einen sogenannten Repair-Prompt), mit der das LLM den Code im nächsten Schritt reparieren kann.

Der entscheidende Vorteil dieses Ansatzes liegt darin, dass zwei weit verbreitete Fehlannahmen vermieden werden [1]: Weder verlässt man sich überoptimistisch auf bloßes „Self-Checking“ durch das Sprachmodell selbst, noch degradiert man das LLM zu einem starren Syntax-Übersetzer — stattdessen entsteht ein eng verzahnter Generate-Verify-Repair-Kreislauf unter formaler Kontrolle.

### 2.3 Abstrakter Syntaxbaum (AST) statt reiner Textsuche

Um aus C++-Code zuverlässig Pin-Definitionen und Funktionsaufrufe zu gewinnen, könnte man zunächst an einfache Textmuster denken, also an **reguläre Ausdrücke (Regex)**. Bei näherer Betrachtung scheitert eine reine Textsuche auf dem gesamten Quelltext jedoch an der Struktur der Programmiersprache C++:

- Ein Kommentar wie `// Früher stand hier WiFi.begin()` oder eine Bildschirmausgabe `Serial.println("WiFi.begin()");` enthält zwar die exakte Zeichenfolge `WiFi.begin`, aktiviert aber in Wahrheit kein WLAN-Modul.
- Eine Schleife `for (int i = 0; i < 10; i++)` oder ein Zähler `unsigned long counter = 0;` sieht auf Textebene genauso aus wie eine Pin-Deklaration `const int LED = 8;`.

Ein **Parser** — im Projekt umgesetzt mittels **Tree-Sitter** [6] — löst dieses Problem, indem er den Quelltext gemäß der formalen C++-Grammatik einliest und daraus einen **Konkreten beziehungsweise Abstrakten Syntaxbaum (Abstract Syntax Tree, AST)** aufbaut. In diesem Baum besitzt jedes Sprachkonstrukt einen eindeutigen Knotentyp: Kommentare liegen in `comment`-Knoten, Zeichenketten in `string_literal`-Knoten, Schleifen in `for_statement`-Knoten und echte Funktionsaufrufe in `call_expression`-Knoten. Ein Werkzeug, das direkt auf diesem Syntaxbaum arbeitet, verwechselt niemals einen Kommentar oder eine Textausgabe mit ausführbarem Programmcode.

### 2.4 SAT, SMT und MaxSMT mit Z3

Bei der anschließenden mathematischen Prüfung kommen drei aufeinander aufbauende Konzepte der formalen Logik zum Einsatz [5]:

- **SAT (Boolean Satisfiability):** Prüft, ob es für eine Reihe von Wahrheitswerten (`wahr`/`falsch`) eine Belegung gibt, sodass eine aussagenlogische Formel wahr wird.
- **SMT (Satisfiability Modulo Theories):** Erweitert SAT um reichhaltigere Hintergrundtheorien wie ganze Zahlen (Integer-Arithmetik) und Vergleichsoperationen (`=`, `!=`, Disjunktionen über erlaubte Zahlenmengen) [3, 5]. Der von De Moura und Bjørner entwickelte Solver **Z3** verbindet hierzu einen modernen DPLL($T$)-Suchkern mit spezialisierten Theorielösern [3]. Dadurch lässt sich jeder Pin im Programm direkt als ganzzahlige Variable $v_i \in \mathbb{Z}$ modellieren.
- **MaxSMT (Maximum SMT / Optimization Modulo Theories):** Im Fehlerfall reicht ein bloßes „Nicht erfüllbar“ nicht aus — man möchte unter allen konfliktfreien Alternativen eine möglichst minimale Korrektur berechnen. In der klassischen SMT-Nutzung erforderte das Finden optimaler Lösungen früher umständliche äußere Suchschleifen durch den Anwendungsentwickler. Mit dem $\nu Z$-Subsystem (Bjørner, Phan und Fleckenstein [4]) integriert Z3 diese Optimierungsfähigkeit über `z3.Optimize` direkt nativ in den Solver. Dabei werden Bedingungen in zwei Klassen eingeteilt [4]:
  - **Hard Constraints** (harte Bedingungen) stellen physikalische Gesetze dar und dürfen niemals verletzt werden (z. B.: „Pin $v_i$ darf kein reservierter Flash-Pin sein“).
  - **Soft Constraints** (weiche Bedingungen) besitzen ein numerisches Gewicht. Z3 maximiert anhand einer inkrementellen MaxRes-/OptSMT-Strategie [4] die gewichtete Summe aller erfüllten weichen Wünsche unter strikter Wahrung sämtlicher harter Gesetze. So bleiben bereits gültige Pins des Nutzers bevorzugt erhalten, während nur die fehlerhaften Pins auf sichere Alternativen verschoben werden.

---

## 3. Systemüberblick und Ablauf im Build-Prozess

Bevor die einzelnen Dateien im Detail betrachtet werden, verdeutlicht der folgende Überblick das Zusammenspiel aller Bausteine während eines regulären Entwicklungsschritts in PlatformIO:

```text
  [platformio.ini & Projektdateien (src/, include/)]
          │
          │  Klick auf "Build" -> Pre-Build Hook startet vor dem Compiler
          ▼
  pio_hook.py
    ├─ Prüft Python-Abhängigkeiten (z3-solver, tree-sitter, tree-sitter-cpp)
    ├─ Ermittelt Target-Board aus platformio.ini und den $PROJECT_SRC_DIR-Pfad
    └─ Startet: python -m mcu_validator.cli <PROJECT_SRC_DIR> <board_id>
          │
          ▼
  mcu_validator/cli.py
    ├─ 1. load_board_data(board_id)        ──► boards/<mcu>.json laden
    ├─ 2. parse_cpp_file(path, board_data) ──► AST über include/ & src/ auswerten
    └─ 3. validate_with_z3(req, res, data) ──► Konfliktprüfung + Z3 Optimize
          │
          ├── Ergebnis SAT   (Exit-Code 0) ──► Compiler übersetzt Firmware regulär
          └── Ergebnis UNSAT (Exit-Code 1) ──► Build bricht sofort ab & gibt
                                               LLM-Modulo-Reparatur-Prompt aus
```

Für die Nutzerin oder den Nutzer einer PlatformIO-Umgebung geschieht dieser gesamte Vorgang unsichtbar im Hintergrund: Nach dem einmaligen Eintragen der Bibliothek in `platformio.ini` verhält sich der Validator wie eine eingebaute Sicherheitsstufe direkt vor dem C++-Compiler. Gleichzeitig bleibt `mcu_validator.cli` unabhängig von PlatformIO als eigenständiges Kommandozeilenwerkzeug nutzbar — etwa für automatisierte Tests oder KI-gestützte Entwicklungs-Pipelines.

---

## 4. Detaillierte Architektur und Begründung der Entwurfsentscheidungen

Das Repository trennt Verantwortlichkeiten streng auf wenige, klar abgegrenzte Module:

| Komponente | Aufgabe im Gesamtsystem |
| :--- | :--- |
| `boards/*.json` | Deklarative Hardware-Spezifikationen der unterstützten Mikrocontroller |
| `mcu_validator/parser.py` | Multi-File-Quelltextauflösung und C++-AST-Analyse mit `tree-sitter-cpp` |
| `mcu_validator/solver.py` | Regelprüfung und Z3-MaxSMT-Optimierung für Reparaturvorschläge |
| `mcu_validator/cli.py` | Orchestrierung, Formatierung des Berichts und Rückgabe des Exit-Codes |
| `mcu_validator/__init__.py` | Schlanke Paket-Schnittstelle ohne verfrühten CLI-Import |
| `pio_hook.py` & `library.json` | Nahtlose PlatformIO-Integration, Paketexport und Build-Steuerung |

In den folgenden Unterkapiteln wird für jeden Baustein erklärt, wie er intern arbeitet und weshalb genau dieser technische Weg gewählt wurde.

---

### 4.1 Deklarative Hardware-Profile

Eine zentrale Leitlinie des Projekts lautet: **Keine einzige GPIO-Nummer, Flash-Grenze oder Chipspezifik darf im Python-Quelltext fest einprogrammiert sein.** Würde man Regeln wie „GPIO 12–17 sind beim ESP32-C3 verboten“ direkt in Python-`if`-Abfragen gießen, müsste bei jedem neuen Mikrocontroller Code umgeschrieben werden und die Gefahr widersprüchlicher Sonderfälle würde rasch wachsen.

Stattdessen liest [`load_board_data(board_id)`](mcu_validator/solver.py) aus dem Verzeichnis `boards/` dynamisch jene JSON-Datei ein, deren Dateistamm (in Kleinbuchstaben) als Teilzeichenkette im normierten Board-Namen vorkommt. So führt eine PlatformIO-Angabe `board = esp32-c3-devkitm-1` automatisch zu `boards/esp32-c3.json` und `board = esp32-s3-devkitc-1` zu `boards/esp32-s3.json`.

Jede Board-Datei trägt oben die Metadaten `mcu` und `description` und gliedert das eigentliche Hardware-Wissen in fünf einheitliche Regelabschnitte:

1. **`pins`:** Bildet jede physisch existierende GPIO-Nummer (als Zeichenkette) auf ihre Eigenschaften ab: eine Liste erlaubter Funktionen (`capabilities` wie `gpio`, `adc1`, `adc2`, `pwm`, `i2c`, `spi`, `uart`, `usb`, `jtag`), das Flag `strapping` (Bool), das Flag `reserved` (Bool für fest belegte Flash-/PSRAM-Pins) sowie eine optionale englische Kurznotiz (`note`). Nicht existierende Pins werden schlicht weggelassen.
2. **`capability_aliases`:** Verknüpft allgemeine Fähigkeiten aus dem Code mit konkreten Hardware-Bänken. Über `"adc": ["adc1", "adc2"]` genügt es, dass der Parser bei `analogRead(...)` generisch die Fähigkeit `"adc"` anfordert; erst das JSON-Profil entscheidet, welche konkreten ADC-Einheiten existieren.
3. **`shared_capabilities`:** Definiert Bus-Fähigkeiten (aktuell `["i2c", "spi"]`), die von mehreren logischen Signalen gleichzeitig auf denselben Pins geteilt werden dürfen.
4. **`resource_triggers`:** Ordnet abstrakte Peripherie-Ressourcen konkreten Funktionsmustern im C++-Code zu — beispielsweise `"wifi": ["WiFi.begin", "WiFi.softAP"]` oder `"usb_serial": ["Serial.begin"]`. Auch hier muss der Parser nichts fest über WLAN wissen; die Trigger lassen sich pro MCU im JSON anpassen.
5. **`conflict_rules`:** Beschreibt kontextabhängige Verbote in der Form `when_resource_active` kombiniert mit `forbidden_capability` oder einer Liste `forbidden_pins`. Auf beiden Espressif-Chips [7, 8] blockiert aktives `"wifi"` beispielsweise die Fähigkeit `"adc2"`, während aktives `"usb_serial"` die native `"usb"`-Fähigkeit und deren konkrete Pins (`18, 19` beim ESP32-C3 bzw. `19, 20` beim ESP32-S3) sperrt.

Diese Trennung beweist ihre Tragfähigkeit unmittelbar im direkten Chip-Vergleich: Ein identischer Sketch mit GPIO `12` für eine LED und GPIO `5` für `analogRead` neben aktivem WLAN ist auf dem **ESP32-C3** fehlerhaft (GPIO `12` ist interner Flash, GPIO `5` liegt auf `ADC2` [7]), auf dem **ESP32-S3** jedoch völlig zulässig (GPIO `12` ist ein normaler Ausgang und GPIO `5` gehört dort zu `ADC1` [8]). Durch das Beilegen eines universellen Prompt-Templates in `README.md` können Anwender neue Board-Profile anhand beliebiger Datenblätter generieren lassen.

---

### 4.2 Quelltextanalyse mit Tree-Sitter

#### Entscheidung für `tree-sitter-cpp` anstelle von Regex oder `libclang`
Nachdem ein früher Entwicklungsstand mit Regex-Mustern auf dem gesamten Quelltext durch Kommentare, Zeichenketten und Schleifenvariablen an seine Grenzen stieß, standen zwei echte Parser-Alternativen zur Auswahl: das LLVM-Compiler-Frontend `libclang` oder der Parser-Generator **Tree-Sitter** (`tree-sitter` mit `tree-sitter-cpp`).

Gegen `libclang` sprachen praktische Hürden im Embedded-Alltag: Ein vollständiges Compiler-Frontend verlangt Zugriff auf alle Target-Systemheader (`Arduino.h`, `WiFi.h`, chip-spezifische ESP-IDF-Pfade) sowie auf die exakten Präprozessor-Makros der jeweiligen Toolchain. Ohne vorher installierte Cross-Compiler-Pakete bricht die Analyse ab. Zudem scheitert ein strenger C++-Compiler häufig gerade an unvollständigen Entwürfen, wie sie ein LLM in Zwischenschritten liefert.

**`tree-sitter-cpp`** [6] löst beide Probleme elegant: Die Bibliothek baut auf einer inkrementellen, GLR-basierten Parser-Architektur auf, wird als leichtgewichtiges Python-Paket installiert, parst C/C++-Code eigenständig ohne externe Header-Dateien und erzeugt selbst bei kleineren Syntaxfehlern einen robusten Syntaxbaum [6].

#### Auflösung mehrerer Dateien und Schutz vor stillen Überschreibungen
Reale PlatformIO-Projekte bestehen selten nur aus einer einzigen Datei `main.cpp`; typischerweise liegen Pin-Definitionen zentral in `include/pins.h`, während die Peripherie-Initialisierung über mehrere `.cpp`-Module unter `src/` verteilt ist. Eine rein dateiweise Prüfung würde solche projektübergreifenden Konflikte übersehen (etwa wenn `include/pins.h` `SOIL_SENSOR = 5` definiert, `src/sensors.cpp` `analogRead(SOIL_SENSOR)` ausführt und `src/main.cpp` `WiFi.begin(...)` startet).

Deshalb löst die Hilfsfunktion `_resolve_source_files(target)` in [`mcu_validator/parser.py`](mcu_validator/parser.py) flexibel sowohl einzelne Dateien als auch ganze Verzeichnisbäume auf: Wird `src/` übergeben und existiert parallel dazu ein Geschwisterordner `include/`, bezieht der Parser automatisch beide Ordner ein. Unterstützt werden `.h`, `.hpp`, `.c`, `.cpp` und `.ino`; Unterordner namens `tests` oder `.pio` werden anhand des relativen Pfads (`relative_to`) ausgeblendet, damit Test-Szenarien innerhalb des Projekts beim rekursiven Durchlauf durch echte Build-Ordner sauber ignoriert bleiben und dennoch gezielt als Testziele übergeben werden können. Header-Dateien werden deterministisch vor den Implementierungsdateien sortiert.

Beim Zusammenführen der Pin-Definitionen über Dateigrenzen hinweg greift `_record_pin(...)`: Wird derselbe Bezeichner mehrfach mit identischer Pin-Nummer gefunden (etwa bei wiederholten Makros), wird er sauber dedupliziert. Wird derselbe Bezeichner jedoch in zwei Dateien mit *unterschiedlichen* Pin-Nummern definiert, legt der Parser die abweichende Definition unter dem eindeutigen Schlüssel `<Name> (<Dateiname>)` ab, sodass ein versteckter Widerspruch niemals stillschweigend überschrieben wird.

#### Extraktion über AST-Knoten
Innerhalb von `parse_cpp_file(cpp_path, board_data)` durchläuft `_walk_ast(tree.root_node)` jeden geparsten Syntaxbaum und wertet gezielt drei Knotenarten aus:

1. **Präprozessor-Makros (`preproc_def`):** Liest Namen (`name`) und Wert (`value`) aus `#define PIN 8`-Anweisungen.
2. **Variablendeklarationen (`declaration` → `init_declarator`):** Prüft explizit `node.parent.type != "for_statement"` sowie den Datentyp (`int` oder `uint8_t`) und übernimmt nur ganzzahlige Literale (`number_literal`). Zähler in `for`-Schleifen oder Variablen wie `unsigned long counter = 0;` werden strukturell ausgefiltert.
3. **Funktions- und Methodenaufrufe (`call_expression`):** Sammelt den normalisierten Funktionsnamen (`function`) zusammen mit sämtlichen Bezeichner-Argumenten (`identifier`) im `arguments`-Teilbaum.

Kommentare (`comment`) und String-Literale (`string_literal`) werden auf dieser strukturellen Ebene überhaupt nicht als Definitionen oder Aufrufe besucht. Anschließend ordnet der Parser die gefundenen Pin-Namen anhand der mit ihnen aufgerufenen Funktionen den benötigten Fähigkeiten zu (`analogRead` → `adc`, `analogWrite`/`ledcAttach`/`ledcAttachPin` → `pwm`, `Wire*.begin`/`setPins` → `i2c`, `SPI*.begin` → `spi`, `Serial*.begin` → `uart`, ansonsten standardmäßig `gpio`) und gleicht sämtliche AST-Funktionsaufrufe gegen `resource_triggers` aus dem Board-JSON ab.

#### Bewusste Rolle der verbliebenen `re`-Aufrufe
Bei der Lektüre von `parser.py` fällt auf, dass das Python-Modul `re` weiterhin importiert wird. Dabei handelt es sich ausdrücklich **nicht** um ein Regex-Scanning auf dem Quelltext — die gesamte Sprachstruktur stammt vom `tree-sitter-cpp`-AST. Reguläre Ausdrücke erfüllen hier lediglich vier eng abgegrenzte Normalisierungsaufgaben auf bereits vom AST isolierten Einzel-Strings:

1. **Inline-Kommentare in `preproc_arg`:** Die C++-Grammatik von Tree-Sitter liefert den Werteteil einer `#define`-Zeile als Rohtoken (`preproc_arg`), was einen am selben Zeilenende angehängten Kommentar (`#define LED_PIN 8 // Board-LED`) einschließen kann. Ein lokales `re.sub(r"//.*|/\*.*?\*/", ...)` entfernt diesen Kommentar vor der Ziffernprüfung.
2. **Whitespace im Funktionsnamen:** `re.sub(r"\s+", "", ...)` normalisiert eventuelle Leerzeichen innerhalb eines bereits isolierten Funktionsknotens (z. B. `WiFi . begin` zu `WiFi.begin`).
3. **Nummerierte Bus-Instanzen:** Auf dem extrahierten Funktionsnamen matchen kompakte Muster wie `^Wire\d*\.(?:begin|setPins)$`, `^SPI\d*\.begin$` und `^Serial\d+\.begin$` einheitlich sowohl Standardobjekte (`Wire`) als auch nummerierte Instanzen (`Wire1`, `SPI2`, `Serial1`).
4. **Namens-Fallback für I2C-Pins:** Sofern im AST ein `Wire`-Aufruf existiert, erkennt `(?:^|_)(?:SDA|SCL)(?:_|$)` Pin-Konstanten wie `OLED_SDA` oder `I2C_SCL` als `i2c`-Leitungen, selbst wenn `Wire.begin()` ohne explizite Pin-Argumente aufgerufen wurde.

---

### 4.3 Formale Prüfung und Reparaturberechnung mit Z3

Die Funktion [`validate_with_z3(requests, active_resources, board_data)`](mcu_validator/solver.py) arbeitet bewusst zweistufig:

#### Stufe 1: Deterministische Konfliktberichterstattung
Zunächst prüft der Solver direkt gegen das eingelesene Board-Wörterbuch, ob jeder angeforderte Pin $p_i^0$ gültig ist. Dabei entstehen präzise, für Menschen und Sprachmodelle sofort lesbare Fehlertexte für fünf Situationen:
- Der Pin existiert auf dem Ziel-Board gar nicht.
- Der Pin ist bereits durch ein anderes Signal belegt (Ausnahme: Beide Signale tragen dieselbe in `shared_capabilities` gelistete Bus-Fähigkeit, z. B. beide `i2c`).
- Der Pin ist mit `reserved: true` markiert.
- Der Pin unterstützt die angeforderte Fähigkeit (aufgelöst über `capability_aliases`) nicht.
- Der Pin oder seine Fähigkeit kollidiert über `conflict_rules` mit einer der aktiven Ressourcen (`active_resources`).

Tritt kein einziger Verstoß auf, endet die Funktion sofort mit `SAT`.

#### Stufe 2: MaxSMT-Reparatur mit `z3.Optimize` und paarweiser Bus-Kopplung
Sobald mindestens ein Konflikt vorliegt, formuliert der Solver ein Optimierungsproblem in **Z3 (`Optimize`)** auf Basis des von Bjørner et al. entwickelten $\nu Z$-Ansatzes [3, 4]. Für jedes Signal $r_i \in \{r_1, \dots, r_n\}$ wird eine Integer-Variable $v_i$ angelegt. Gleichzeitig bestimmt der Solver anhand der geladenen Board-Daten und aktiven Ressourcen die Menge der prinzipiell zulässigen Kandidaten-Pins $P_i$ (nicht reserviert, nicht in `forbidden_pins`, fähig zur benötigten Capability und frei von `forbidden_caps`).

**Harte Constraints:**
Jeder Variablen wird zunächst ihre gültige Pin-Menge vorgeschrieben (existiert kein einziger gültiger Kandidat auf dem Chip, wird zur Erhaltung der Lösbarkeit ersatzweise `-1` gesetzt):

$$\forall i \in \{1, \dots, n\}: \quad \bigvee_{p \in P_i} (v_i = p)$$

Anschließend folgt die Entflechtung beziehungsweise Kopplung der Signale. Ein einfaches globales `z3.Distinct(...)` über alle Variablen wäre hier fachlich falsch, weil es auch gewollte I2C- und SPI-Busverbindungen (beispielsweise ein OLED-Display und ein Umweltsensor auf demselben I2C-Bus) auseinanderreißen würde. Deshalb prüft `solver.py` jedes Signalpaar $(r_i, r_j)$ mit $i < j$ paarweise:

$$\forall 1 \le i < j \le n: \quad \begin{cases} v_i = v_j, & \text{falls } c_i = c_j \land c_i \in \text{shared\_capabilities} \land p_i^0 = p_j^0 \\ v_i \ne v_j, & \text{sonst} \end{cases}$$

Teilen sich also zwei Signale im Eingabe-Code denselben zulässigen Bus auf demselben Pin, bleiben sie auch nach einer eventuellen Verschiebung untrennbar gekoppelt; alle anderen Signale werden zwingend auf unterschiedliche Pins gelegt.

**Weiche Constraints (MaxSMT-Gewichtung):**
Um eine möglichst behutsame Reparatur statt einer willkürlichen Neuwürfelung zu erreichen, ergänzt der Solver zwei gewichtete Optimierungsziele:

$$\max \sum_{i=1}^{n} \left( 100 \cdot \mathbb{I}[v_i = p_i^0] + \sum_{p \in P_i \cap \text{Strapping}} 10 \cdot \mathbb{I}[v_i \ne p] \right)$$

Das deutliche Gewichtsverhältnis $100 \gg 10$ bewirkt eine klare Präferenzordnung: Jeder bereits konfliktfreie Pin des Originalcodes bleibt unverändert stehen — selbst dann, wenn er auf einem Strapping-Pin liegt. Nur wenn ein Pin tatsächlich neu zugewiesen werden muss, vermeidet Z3 Boot-Strapping-Pins und wählt nach Möglichkeit einen unkritischen Standard-GPIO.

---

### 4.4 Berichtsgenerierung und Kommandozeilensteuerung

[`mcu_validator/cli.py`](mcu_validator/cli.py) bildet die Brücke zwischen Dateisystem, Parser, Solver und externem Aufrufer. Über `validate_file(cpp_path, board_id)` wird zuerst die Board-JSON geladen und sowohl an `parse_cpp_file` als auch an `validate_with_z3` weitergereicht.

Im Erfolgsfall gibt `format_report(...)` lediglich eine kompakte Übersicht (`Checked File`, `Active Modules`, `RESULT: SAT`) aus und beendet den Prozess mit Exit-Code `0`. Im Fehlerfall (`UNSAT`, Exit-Code `1`) erstellt sie den direkt kopierbaren LLM-Modulo-Block (`--- COPY THIS PROMPT BACK TO YOUR AI (LLM-MODULO) ---`), der sowohl die gefundenen Konflikte als auch für jeden einzelnen Pin die konkrete Z3-Anweisung (`Keep GPIO ...` oder `Change GPIO X -> GPIO Y`) enthält.

---

### 4.5 Integration als PlatformIO-Bibliothek

Frühe Prototypen verlangten noch, Python-Skripte manuell in jedes neue Mikrocontroller-Projekt zu kopieren. Um stattdessen eine saubere Wiederverwendung als Bibliothek zu ermöglichen, nutzt das Paket zwei PlatformIO-Mechanismen:

1. **Paketmanifest ([`library.json`](library.json)):**
   - Über `"build": { "extraScript": "pio_hook.py", "srcFilter": ["-<*>"] }` wird das Hook-Skript bereitgestellt und zugleich verhindert, dass PlatformIO beim Einbinden über `lib_deps` versehentlich das im Repository enthaltene Demo-Programm (`src/main.cpp` mit ESP32-spezifischem `#include <WiFi.h>`) in fremde Projekte (etwa für ESP32-S3, STM32 oder RP2040) mitkompiliert.
   - Das Feld `"export": { "include": [...] }` stellt sicher, dass bei der Paketierung für die PlatformIO Registry ausschließlich die Laufzeitdateien (`boards/*.json`, `mcu_validator/*.py`, `pio_hook.py`, `library.json`, `README.md`, `LICENSE`) ausgeliefert werden und Entwicklungsordner wie `tests/` oder `src/` außen vor bleiben.
2. **Pre-Build-Hook ([`pio_hook.py`](pio_hook.py)):**
   - Ein Environment-Flag (`_MCU_VALIDATOR_RAN`) sorgt dafür, dass die Prüfung pro Build genau einmal abläuft.
   - Unter Windows wählt der Hook bevorzugt den System-Python-Launcher (`shutil.which("py") or sys.executable`), da PlatformIOs eigene eingebettete `penv`-Umgebung bei IDE-Updates mitunter zurückgesetzt wird. Fehlen `z3`, `tree_sitter` oder `tree_sitter_cpp`, installiert sie der Hook einmalig automatisch nach.
   - Anschließend ruft der Hook `python -m mcu_validator.cli` geschlossen auf dem gesamten `$PROJECT_SRC_DIR` und dem aus `platformio.ini` ausgelesenen Board-Namen auf. Kehrt die CLI mit einem Fehlercode ungleich `0` zurück, bricht `env.Exit(1)` den Build ab, bevor der Compiler gestartet wird.
3. **Vermeidung doppelter Modul-Initialisierung (`mcu_validator/__init__.py`):**
   - [`mcu_validator/__init__.py`](mcu_validator/__init__.py) exportiert bewusst nur die Bibliotheksfunktionen `parse_cpp_file`, `load_board_data` und `validate_with_z3` und verzichtet auf einen Vorab-Import von `.cli`. Andernfalls führt der Aufruf `python -m mcu_validator.cli` unter Python zu einem `RuntimeWarning` wegen doppelter Ladung des Moduls über `runpy`.

---

## 5. Evaluierung anhand von Testszenarien und Praxisbetrieb

Die Funktionsfähigkeit des Gesamtsystems wurde sowohl über eine automatisierte Testsuite als auch in einem realen Projekt-Workflow außerhalb des Entwicklungsordners überprüft.

### 5.1 Automatisierte Szenario-Testsuite

Der Test-Runner `tests/run_tests.py` startet `python -m mcu_validator.cli` isoliert gegen neun definierte Szenarien und prüft den Rückgabestatus (`SAT` vs. `UNSAT`). Alle neun Testfälle werden fehlerfrei bestanden (`9/9 tests passed!`), und eine GitHub-Actions-Pipeline (`.github/workflows/ci.yml`) führt diese Suite automatisiert bei jedem Push auf Ubuntu unter Python 3.11 aus:

| Szenario | Ziel-Board | Erwartung | Abgedeckter Nachweis |
| :--- | :--- | :--- | :--- |
| `src/main.cpp` | `esp32-c3` | `SAT` | Vollständiger Hardware-Sketch mit Status-LED (GPIO `8`), ADC1-Sensor (GPIO `1`), Relais (GPIO `4`), Wi-Fi-Access-Point und USB-Serial-Heartbeat. |
| `00_flash_and_wifi_conflict.cpp` | `esp32-c3` | `UNSAT` | Erkennt den gleichzeitigen Verstoß gegen SPI-Flash (GPIO `12`) und `ADC2` bei aktivem WLAN (GPIO `5`). |
| `00_flash_and_wifi_conflict.cpp` | `esp32-s3` | `SAT` | Belegt die rein datengetriebene Architektur: Exakt derselbe Quelltext gilt auf dem ESP32-S3 als zulässig, weil dort GPIO `12` regulär nutzbar und GPIO `5` Teil von `ADC1` ist. |
| `01_valid_sketch.cpp` | `esp32-c3` | `SAT` | Positivkontrolle für eine konfliktfreie Standardkonfiguration. |
| `02_usb_serial_conflict.cpp` | `esp32-c3` | `UNSAT` | Erkennt die Blockierung der nativen USB-Pins `18` und `19` bei aktivem `Serial.begin(...)`. |
| `03_duplicate_and_invalid_pin.cpp` | `esp32-c3` | `UNSAT` | Meldet Doppelbelegung auf GPIO `7`, nicht existierenden GPIO `32` sowie fehlende ADC-Fähigkeit auf GPIO `6`. |
| `04_shared_i2c_bus.cpp` | `esp32-c3` | `UNSAT` | Akzeptiert die gemeinsame Nutzung des I2C-Busses (GPIO `6` und `7`) für zwei Geräte (OLED und BME280), isoliert aber eine zusätzlich auf GPIO `6` kollidierende `STATUS_LED` und verschiebt gezielt nur diese. |
| `05_ast_ignores_strings_and_comments.cpp` | `esp32-c3` | `SAT` | Beweist die strukturelle Überlegenheit des Tree-Sitter-AST gegenüber Regex: `WiFi.begin(...)` innerhalb eines Kommentars und eines String-Literals löst keinen Fehlalarm aus. |
| `06_multi_file_project/src` | `esp32-c3` | `UNSAT` | Prüft die projektweite Analyse über drei Dateien hinweg: Pin-Definitionen in `include/pins.h`, `WiFi.begin` in `src/main.cpp` und `analogRead` in `src/sensors.cpp`. |

### 5.2 Praxisbetrieb über die PlatformIO Registry

Um die Ende-zu-Ende-Erfahrung für Anwenderinnen und Anwender realitätsnah nachzustellen, wurde das Paket über `pio pkg publish` unter `dmatheja/mcu-pin-solver` (`0.1.0`) in der öffentlichen PlatformIO Registry veröffentlicht und in einem vollständig neuen, separaten PlatformIO-Projekt für `esp32-c3-devkitm-1` eingebunden — ausschließlich über `lib_deps = dmatheja/mcu-pin-solver@^0.1.0` und `extra_scripts`.

In einem zweistufigen Durchlauf zeigte sich das angestrebte Verhalten unmittelbar:
1. Mit bewusst fehlerhaften Pin-Definitionen in einer separaten Header-Datei (`include/pins.h` mit `LED_PIN 12` und `SENSOR_PIN 5`) neben `WiFi.begin` und `Serial.begin` in `src/main.cpp` erkannte der Pre-Build-Hook die aktiven Module `['wifi', 'usb_serial']`, brach den Compilerlauf ab und berechnete mit `LED_PIN 10` und `SENSOR_PIN 0` eine kollisionsfreie Alternative abseits von Strapping- und USB-Pins.
2. Nach Übernahme der beiden Z3-Vorschläge in `include/pins.h` passierte der Validator mit `RESULT: SAT`, die reguläre ESP32-C3-Firmware wurde vollständig übersetzt und dank `srcFilter` in `library.json` blieb der demo-eigene Code der Bibliothek sauber aus dem Projekt-Build ausgeschlossen.

---

## 6. Kritische Würdigung, Grenzen und Ausblick

### 6.1 Erreichte Qualität und bekannte Grenzen des aktuellen Stands

Durch das Zusammenspiel aus `tree-sitter-cpp`-AST, JSON-Regelwerken, paarweiser Z3-MaxSMT-Optimierung und sauberer PlatformIO-Paketierung erfüllt **mcu-pin-solver** alle gesetzten Ziele. Dennoch weist der bewusst schlank gehaltene Stand klare technische Grenzen auf, die bei zukünftigen Erweiterungen bedacht werden sollten:

- **Aktuelle Hardware-Abdeckung:** Verifiziert wurden bislang ausschließlich **ESP32-C3** und **ESP32-S3**. Andere Chip-Familien lassen sich zwar unmittelbar durch neue JSON-Dateien nachrüsten, erfordern aber sorgfältige Recherche anhand der jeweiligen Referenzhandbücher.
- **Statische Pin-Konstanten vs. dynamische Berechnungen:** Der AST-Parser extrahiert explizite Ganzzahl-Literale in `#define`-Makros sowie `int`- und `uint8_t`-Deklarationen. Pins, die in Arrays, `struct`-Tabellen, `enum`-Blöcken oder komplexeren Präprozessor-Ausdrücken (`#define LED_PIN (BASE + 2)`) beziehungsweise bedingter Kompilierung (`#ifdef ...`) definiert werden, wertet die aktuelle Version noch nicht aus.
- **Klassenkonstruktoren und komplexe Peripherie-Limits:** Manche Bibliotheken (wie OLED-Display-Treiber oder benutzerdefinierte `HardwareSerial`-Objekte) erhalten ihre Pins bereits im C++-Konstruktor statt in einem `.begin(...)`-Aufruf. Zudem prüft das JSON-Schema bislang statische Pin-Fähigkeiten und Ressourcen-Konflikte, jedoch noch keine zählbaren Controller-Limits (wie maximal verfügbare PWM-/LEDC-Kanäle) oder rein als Eingang nutzbare Pins (`input-only`).

### 6.2 Ideen für weiterführende Ausbaustufen

Aufbauend auf der etablierten Architektur bieten sich mehrere natürliche Erweiterungspfade an — unterstützt durch die Entwickler- und KI-Übergabedokumentation in `AGENTS.md`:

1. **Vollgeschlossene Auto-Repair-Schleife:** Anstatt den generierten Reparatur-Prompt manuell in ein Chatfenster zu kopieren, könnte eine CLI-Option oder VS-Code-Erweiterung direkt per API mit einem Sprachmodell kommunizieren, den Patch automatisch einspielen und erneut durch Z3 schicken, bis `SAT` erreicht ist.
2. **Erweiterung des C++-AST-Modells und der JSON-Regeln:** Ergänzung von Konstruktor-Erkennung, Pin-Arrays und `constexpr`-Auswertung in `parser.py` sowie elektrischer Richtungsregeln (`input_only`, erlaubter Boot-Pegel an Strapping-Pins) in `solver.py`.
3. **Wachsende Board-Datenbank und automatisierte Registry-Releases:** Aufnahme real getesteter Profile für weitverbreitete Einstiegsplattformen wie RP2040, STM32 und klassische Arduino-AVRs sowie Automatisierung neuer `pio pkg publish`-Veröffentlichungen per GitHub Actions beim Erstellen eines Versions-Tags.

---

## 7. Literaturverzeichnis

- **[1]** Kambhampati, S., Valmeekam, K., Guan, L., Verma, M., Stechly, K., Bhambri, S., Saldyt, L., & Murthy, A. (2024). *LLMs Can't Plan, But Can Help Planning in LLM-Modulo Frameworks.* In *Proceedings of the 41st International Conference on Machine Learning (ICML 2024)*, Proceedings of Machine Learning Research (PMLR), Bd. 235, S. 22895–22907 (Preprint: arXiv:2402.01817).
- **[2]** Garcez, A. d'Avila, & Lamb, L. C. (2023). *Neurosymbolic AI: The 3rd Wave.* *Artificial Intelligence Review*, 56(11), S. 12387–12406, Springer.
- **[3]** De Moura, L., & Bjørner, N. (2008). *Z3: An Efficient SMT Solver.* In *Tools and Algorithms for the Construction and Analysis of Systems (TACAS 2008)*, Lecture Notes in Computer Science (LNCS), Bd. 4963, S. 337–340, Springer. DOI: 10.1007/978-3-540-78800-3_24.
- **[4]** Bjørner, N., Phan, A.-D., & Fleckenstein, L. (2015). *$\nu Z$ - An Optimizing SMT Solver.* In *Tools and Algorithms for the Construction and Analysis of Systems (TACAS 2015)*, Lecture Notes in Computer Science (LNCS), Bd. 9035, S. 194–199, Springer. DOI: 10.1007/978-3-662-46681-0_14.
- **[5]** Barrett, C., Sebastiani, R., Seshia, S. A., & Tinelli, C. (2021). *Satisfiability Modulo Theories.* In A. Biere, M. Heule, H. van Maaren, & T. Walsh (Hrsg.), *Handbook of Satisfiability* (2. Aufl.), Frontiers in Artificial Intelligence and Applications, Bd. 336, IOS Press.
- **[6]** Brunsfeld, M. (2018). *Tree-sitter: An incremental parsing system for programming tools.* Offizielle System- und Grammatikdokumentation, https://tree-sitter.github.io/tree-sitter/.
- **[7]** Espressif Systems (2024). *ESP32-C3 Series Datasheet* & *ESP32-C3 Technical Reference Manual*. Espressif Systems, Shanghai.
- **[8]** Espressif Systems (2024). *ESP32-S3 Series Datasheet* & *ESP32-S3 Technical Reference Manual*. Espressif Systems, Shanghai.
