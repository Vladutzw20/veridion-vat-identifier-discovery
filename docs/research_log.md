# Log VAT discovery

> Jurnalul de lucru al proiectului. Ce vine de la asistentul AI (Claude) e marcat explicit: idei, cod, presupuneri neverificate și greșeli găsite pe parcurs.

---

## Step 1 – Setup și prima privire la Companies House

### Mediu de lucru și de ce l-am ales
- **Python 3.12 + mediu virtual (`.venv`):** dependențele proiectului stau izolate de restul sistemului, iar proiectul se poate reproduce pe alt calculator dintr-un `requirements.txt`.
- **VS Code + notebook-uri Jupyter:** proiectul e în mare parte explorare. Notebook-ul păstrează codul, rezultatul și observația unul lângă altul, deci trail-ul cerut de enunț rămâne vizibil, pas cu pas.
- **DuckDB pentru fișierul Companies House:** fișierul are ~5,7 milioane de rânduri. DuckDB rulează SQL direct pe CSV, fără să-l încarce întreg în memorie: citirea completă a durat 5,9 s. A avut și opțiunile de care am avut nevoie pentru rândul stricat (`ignore_errors`, `store_rejects`), ca să văd exact ce rând e respins în loc să pierd date în tăcere.
- **pandas pentru eșantioane și rezultate:** tabelele mici (zeci sau sute de rânduri) le prelucrez și le salvez ca CSV, ca fiecare pas să lase un fișier verificabil.
- **Numerele (TVA, nr. CH) ținute mereu ca text** (`dtype=str`): altfel se pierd zerourile din față și potrivirile cu Companies House ies greșit.
- **`requests` cu reîncercări:** serverele folosite (indexul Common Crawl, Find a Tender) dau des erori temporare (504, 429). Codul reîncearcă și separă „eroare de server” de „nu există”, ca o eroare să nu fie numărată drept rezultat.
- **Common Crawl citit „chirurgical”:** prin index iau doar înregistrarea paginii de care am nevoie (cerere `Range`), nu fișierul întreg de sute de MB; pentru eșantionul aleatoriu folosesc fișierele WET (doar text). `warcio` citește formatul arhivei, iar `pypdf` extrage text din PDF-uri (la Laine, TVA-ul era doar într-un PDF).
- **Seed fix (42) la orice alegere aleatorie:** eșantioanele se pot reproduce exact.
- **Verificarea HMRC de mână, pe pagina web:** API-ul de producție cere o organizație înregistrată (vezi mai jos), deci am construit și testat verificarea automată în Sandbox, iar numerele reale le verific manual.
- **Cheile API în `.env`, exclus din git:** credențialele nu ajung în repo.

### Fișierul Companies House
- Fișier: `BasicCompanyDataAsOneFile-2026-09-01.csv`, 5.689.370 de linii (rezultatul `wc -l`).
- Cu `SELECT * ... LIMIT 5` am văzut primele 5 rânduri ale tabelului.
- **Observație:** tabelul nu are nicio coloană de TVA (VAT).

### Ipoteza mea: numărul de TVA ar putea fi legat de company number
- Motiv: nu există coloană de TVA în tabel și m-am gândit că poate are legătură cu company number.
- În rândurile din `head`, company number are 8 cifre (ex. 08209948, 16092999).
- Enunțul Veridion indică numere de TVA UK de 9 cifre.
- Concluzie provizorie: formatele diferă, deci ipoteza pare puțin probabilă.
- Închis în Step 2: pagina HMRC „Check a UK VAT number” confirmă că TVA-ul UK are 9 cifre (vezi mai jos).

### Context legal 1: facturile
- Sursă oficială (GOV.UK): secțiunea „4.1 Details to include on a VAT invoice”, https://www.gov.uk/guidance/record-keeping-for-vat-notice-70021#vat-invoices
- Ce spune: orice factură de TVA trebuie să arate numele, adresa și numărul de TVA al furnizorului.
- Concluzie: numărul de TVA apare obligatoriu pe facturi.
- Dar facturile sunt documente private între furnizor și client. Legea obligă numărul de TVA să apară pe ele, dar nu sunt accesibile pe web-ul deschis, deci nu sunt o sursă directă. Excepții de verificat: facturi care ajung publice (de ex. în înregistrări ale sectorului public, cum menționează enunțul).

### Context legal 2: site-ul firmei
- La început am pornit de la surse secundare (ghiduri, bloguri), care nu sunt dovadă.
- Sursa primară: legislation.gov.uk, Electronic Commerce (EC Directive) Regulations 2002, Regulation 6, lit. (g): un furnizor de servicii care desfășoară o activitate supusă TVA trebuie să furnizeze numărul de TVA.
- Limite: se adresează „service providers” (servicii online), nu e clar pentru orice firmă cu site de prezentare; se aplică doar firmelor înregistrate la TVA.
- Opinia mea după ce am citit Regulation 6: nu sunt convins că un site de prezentare simplu e obligat să afișeze TVA-ul. Nu am verificat definiția din lege („information society services”). Tratez obligația legală ca incertă și o măsor empiric.

### Rând stricat în Companies House
- DuckDB oprește citirea la linia 4.502.220: 55 de coloane așteptate, 56 găsite (aceeași eroare la două interogări diferite).
- Cu `grep -n` am găsit rândul la linia 4.502.221: SENTINALL LIMITED, număr 08652773.
- Cauză observată: rândul are 5 coduri SIC, iar antetul are doar 4 coloane SIC (SicText_1..4), deci valorile se mută cu o poziție.
- Diferența de 1 între numărul liniei din DuckDB și cel din grep: nu am verificat motivul.

**Rezultat final:**
- Citire completă cu `ignore_errors` și `store_rejects`: 5.689.366 de rânduri citite, în 5,9 secunde.
- `COUNT(DISTINCT line)` pe `reject_errors`: 1 rând respins (linia 4.502.220, TOO MANY COLUMNS).
- Verificare cifre: 5.689.366 + 1 = 5.689.367, față de 5.689.369 (wc -l minus antet). Diferență de 2, motiv neverificat.
- Decizie: pentru eșantion folosesc `ignore_errors = true`; pierd cel mult acest rând din 5,69 milioane.

Primele rânduri dintr-un eșantion aleatoriu de 20 de firme (folosit mai jos):

| companyname | companynumber | regaddressposttown | companystatus | accountsaccountcategory |
|---|---|---|---|---|
| 51 UPPERTON GARDENS (EASTBOURNE) LIMITED | 09115556 | EASTBOURNE | Active | DORMANT |
| 151 AND 153 MARLBOROUGH ROAD LIMITED | 07893004 | LONDON | Active | MICRO ENTITY |
| 70 WEBBS ROAD FREEHOLD LIMITED | 13436038 | LONDON | Active | DORMANT |
| 127STAMFORD LIMITED | 14702421 | MANCHESTER | Active | TOTAL EXEMPTION FULL |
| 19 LANSDOWNE STREET (HOVE) LIMITED | 05658192 | HOVE | Active | DORMANT |
| 49 SIMPSON STREET FREEHOLD LIMITED | 06195867 | LONDON | Active | MICRO ENTITY |
| 3SPR MANAGEMENT SERVICES LTD | 09537288 | BIRMINGHAM | Active | MICRO ENTITY |
| 17 LIONGATE GARDENS LIMITED | 02328272 | SURREY | Active | MICRO ENTITY |
| 44 GRAFTON ROAD LTD | 16027082 | WORTHING | Active | DORMANT |
| 20 CABOT SQUARE II UNIT TRUST SLP | SL005921 | 20 CASTLE TERRACE | Active | NO ACCOUNTS FILED |
| 4 JAYS CONSULTING AND DEVELOPMENTS LTD | 15868094 | WARRINGTON | Active | TOTAL EXEMPTION FULL |
| 3D LEADERSHIP LTD | 09520166 | WILDEN | Active | MICRO ENTITY |
| 360 BLADES AND TOWER TRAINING LIMITED | SC820901 | AYR | Active | MICRO ENTITY |
| 76CASTLE CANDY LTD | SC850767 | EDINBURGH | Active | NO ACCOUNTS FILED |
| 4S UK CONSULTING LIMITED | 11167533 | READING | Active | TOTAL EXEMPTION FULL |
| 6 DEERDYKES PLACE LTD | 12754671 | LONDON | Active | SMALL |
| 58 GREENCROFT OWNERS LIMITED | 06004638 | BARNET | Active | MICRO ENTITY |
| 55PMMANCO LIMITED | 11251444 | OXFORD | Active | DORMANT |
| 1ST SENTRY GROUP LTD | 16529394 | LONDON | Active | NO ACCOUNTS FILED |
| 68 PLUS LIMITED | 15466423 | LONDON | Active | DORMANT |

### Cale abandonată: căutare site firmă (Google) + căutare „VAT” pe site
- Ce am încercat: căutare manuală pe Google pentru 4 firme din eșantionul de 20; cod cu requests + regex (`\bVAT\b`) pe pagini descărcate.
- Ce a ieșit: pe pagina Companies House a firmei 09115556: status 200, 35.747 caractere, 0 potriviri „VAT”. Pe pagina de contact a 4S UK Consulting: niciun număr TVA vizibil.
- De ce opresc: (1) nu scalează la milioane de firme; (2) cel mai greu a fost găsirea TVA-ului pe site, nu a site-ului; o pagină descărcată nu acoperă paginile unde apare de obicei, deci ar trebui parcurs și restul site-ului; (3) „nu găsesc” nu se poate separa de „firma nu are TVA”.
- Neverificat la momentul respectiv: rata reală la care apare TVA pe site-uri (măsurată ulterior, vezi Common Crawl).

---

## Step 2 – HMRC (verificatorul web și API-ul Sandbox)

### Pagina web de verificare
Am găsit verificatorul HMRC pentru oameni („Check a UK VAT number”). Merge fără cont, dar doar de mână, număr cu număr. Pe pagină scrie că un număr de TVA UK are 9 cifre, uneori cu „GB” în față. Asta închide o întrebare de ieri: company number are 8 caractere, TVA-ul 9, deci nu pot fi același lucru.

### Cont și aplicație
Mi-am făcut cont pe HMRC Developer Hub și am creat aplicația veridion-vat-PoC în Sandbox (mediul de test, cu date false). Am abonat-o la „Check a UK VAT number 2.0” și la „Hello World 1.0”. Cheia (client ID + secret) e în `.env`, iar `.env` și `.venv/` sunt în `.gitignore`, ca să nu ajungă pe GitHub.

### Tokenul
Am cerut un token OAuth de la Sandbox și am primit status 200. E valabil 14400 de secunde, adică 4 ore.

### Primul număr
Am verificat 553557881 și am primit 200. Răspunsul are numele firmei, numărul, adresa (line1, postcode, countryCode) și data verificării (`processingDate`). Nu are company number, deci legătura cu Companies House nu se poate face direct, doar prin nume și cod poștal.

### Toată lista de test
Am descărcat lista cu numere de test: 40 de numere, de 9 și 12 cifre, unele cu 0 în față. Toate 40 au primit 200. Am verificat cu cod că numărul returnat e identic cu cel trimis la toate 40, inclusiv la cele de 12 cifre și la cele cu zerouri în față. Numerele trebuie ținute ca text, altfel se pierd zerourile. Numele firmelor de test sunt inventate și au forme amestecate (Ltd, Inc., Plc sau nimic).

### Numere greșite
- 123456789 (format corect, dar nu există) → 404, NOT_FOUND, „targetVrn does not match a registered company”.
- 12345 (format greșit) → 400, INVALID_REQUEST, „Vrn parameters should be 9 or 12 digits”.

Deci API-ul deosebește „nu există” de „format greșit”.

### Sursa numerelor de test
Fișierul `vrn.csv` din depozitul GitHub al HMRC (https://github.com/hmrc/vat-registered-companies-api/blob/main/public/api/conf/2.0/test-data/vrn.csv). L-a găsit asistentul AI (Claude) printr-o căutare web: linkul apărea în README-ul bibliotecii valvat (https://github.com/yolk/valvat/blob/master/README.md). Nu l-am găsit în documentația oficială HMRC, dar Sandbox-ul a recunoscut toate numerele, deci lista e bună pentru test.

### Concluzia mea
Status 200 spune doar că numărul există, nu că e al firmei pe care o caut. Pentru fiecare număr găsit trebuie să compar numele și adresa primite de la HMRC cu datele firmei din Companies House.

### Neverificate (presupuneri ale asistentului)
- Numerele de 12 cifre ar fi numărul de bază plus 3 cifre pentru o ramură a firmei.
- Adresa de TVA poate fi diferită de sediul din Companies House (confirmat ulterior empiric, vezi Endole).
- HMRC are o limită de cereri pe secundă (n-o știu; am pus 0,5 s pauză din prudență).
- Termenii API-ului spun că e doar pentru „due diligence” între comercianți. E posibil ca folosirea lui pentru un dataset comercial să nu intre aici.

### Mecanismul de validare (gândit înainte de date reale)
Un număr găsit trebuie să treacă trei verificări:
1. HMRC îl recunoaște (200, nu 404/400);
2. numele de la HMRC se potrivește cu numele din Companies House;
3. codul poștal de la HMRC e același cu cel din Companies House.

**Compararea numelor.** Același nume poate fi scris diferit („J Smith Building Services Ltd” / „J. Smith Building Svcs Limited”): punctuație, cuvinte prescurtate, forma juridică scrisă altfel. Idei:
- scot punctuația și împart în cuvinte;
- „scot vocalele” NU merge (Services → Srvcs, Svcs → Svcs, nu se potrivesc);
- prescurtarea = literele ei apar în cuvântul lung, în aceeași ordine (subșir); merge pe Svcs/Services și Ltd/Limited;
- cuvintele generice (Ltd, Limited, Services, Building) nu identifică firma; contează partea distinctivă (J Smith), deci cuvintele generice cântăresc mai puțin.

Neverificat: unde dă regula cu subșirul potriviri false (de ex. la prescurtări de 2–3 litere).

**Când numele se potrivește, dar codul poștal nu:** inițial am decis să nu accept numărul, pentru că un număr greșit costă mai mult decât unul lipsă. Variantă: o a treia categorie, „incert”. Întrebarea „cazurile «nume da, cod poștal nu» sunt de obicei corecte sau greșite?” am testat-o pe date reale (Endole, Common Crawl): sunt de obicei corecte.

Categorii pentru fiecare număr verificat: confirmat, incert, respins_alta_firma, respins_inexistent (404), respins_format (400), fara_candidat.

### Termenii HMRC pentru producție
Am citit termenii de utilizare pentru producție. Cer dovada că organizația e înregistrată oficial (Companies House, UTR, VAT, PAYE), plus privacy policy și termeni pentru software. Ca student fără firmă nu pot răspunde cinstit, deci nu cer credențiale de producție.
- **Decizie:** numerele reale din eșantioane le verific pe pagina web HMRC, de mână. Codul Sandbox rămâne ca dovadă că verificarea automată e construită și testată.
- Pentru Part 3: accesul automat cere un proces de conformitate (7 secțiuni), iar API-ul e declarat doar pentru due diligence → risc pentru un produs comercial.

### Cum separ „firma nu are TVA” de „n-am găsit eu”
Nu pot pentru fiecare firmă, dar pot pe grupuri.
- Indicii din Companies House: categoria conturilor (DORMANT / MICRO / FULL...) și codul SIC (domeniul de activitate).
- La firmele mari, care aproape sigur au TVA, un „fără candidat” = am ratat eu → acolo măsor rata de ratare a căutării.
- De aici: eșantion stratificat pe categoria conturilor.

### Stratificarea: grupări după conturi și SIC

**1. Categoria conturilor (`accountsaccountcategory`).** Interogare DuckDB pe tot fișierul: 16 categorii, total 5.689.366 (se închide cu numărul de rânduri). Primele 4 (MICRO ENTITY 1,86M; NO ACCOUNTS FILED 1,46M; TOTAL EXEMPTION FULL 1,34M; DORMANT 0,63M) ≈ 93% din firme. Gruparea în 4 grupuri a propus-o asistentul, la cererea mea; semnificațiile categoriilor sunt din memoria lui și nu le-am verificat pe gov.uk.

| grup | categorii | șansa de TVA | firme |
|---|---|---|---|
| 1. probabil fără TVA | DORMANT, FILING EXEMPTION SUBSIDIARY | foarte mică | 632.873 |
| 2. necunoscut | NO ACCOUNTS FILED, ACCOUNTS TYPE NOT AVAILABLE, INITIAL, PARTIAL EXEMPTION | habar n-am | 1.460.883 |
| 3. firme mici | MICRO ENTITY, TOTAL EXEMPTION FULL, UNAUDITED ABRIDGED, SMALL, TOTAL EXEMPTION SMALL, AUDITED ABRIDGED | amestec | 3.439.978 |
| 4. firme mari | FULL, MEDIUM, GROUP, AUDIT EXEMPTION SUBSIDIARY | mare | 155.632 |

Observații:
- Unele categorii au doar câteva firme (INITIAL: 3).
- NO ACCOUNTS FILED e uriaș (~1,46M). Ipoteza asistentului: firme noi, care n-au ajuns la primele conturi. De verificat cu data înființării.
- Capcane (presupuneri ale asistentului): filialele pot fi într-un „VAT group”, cu numărul de TVA al altei firme din grup (confirmat ulterior empiric: Taylor Maxwell, Carter Jonas); categoria nu e o măsură exactă a mărimii.

**2. SIC (`siccodesictext_1`).** Am folosit doar primul cod SIC (simplificare; o firmă poate avea până la 4). 1.164 de valori diferite, deci trebuie grupate. Pe baza celor mai frecvente 25 de coduri:

| grup | coduri | șansa de TVA | firme |
|---|---|---|---|
| A. fără activitate | 99999 Dormant Company, 98000 Residents property management | foarte mică | 231.451 |
| B. imobiliare + holding | 68209 închiriere, 68100 cumpărare/vânzare, 64209 holding | incertă | 659.588 |
| C. necunoscut | None Supplied | habar n-am | 231.523 |
| D. activitate comercială | restul (inclusiv 68320 administrare contra cost) | depinde de mărime | 4.566.804 |

Pe ce mă bazez:
- 99999 apare în date chiar cu descrierea „Dormant Company”.
- VAT Notice 742 (HMRC, gov.uk), secțiunile 3.1 și 7.1: închirierea și vânzarea de imobile sunt în mod normal scutite de TVA, iar înregistrarea e obligatorie doar pentru livrări taxabile. Deci multe firme imobiliare pot fi fără TVA.
- Tot acolo: proprietarul poate „opta să taxeze”, iar hotelurile, cazarea de vacanță, parcările și clădirile comerciale noi sunt taxabile. Codul SIC nu separă aceste cazuri, de aceea grupul B e „incert”, nu „fără TVA”.
- Secțiunea 12.1: taxele de întreținere pentru locuințe sunt scutite → susține grupul A (98000).
- Secțiunea 12.4: administrarea contra cost e taxabilă → 68320 l-am lăsat în D.
- 64209 (holding) în B e presupunerea asistentului. Neverificat.

### Întrebări deschise (rămase)
- Enunțul spune ~4,2M firme active, dar fișierul are 5,69M rânduri. Se explică prin `companystatus` / `companycategory` (fișierul conține și CIO-uri, LP-uri, Overseas Entities)? Neverificat.
- De ce 1.164 de valori SIC, mai multe decât codurile existente?

---

## Step 3 – Primul caz real și adresele comune

### Firma 1: CAYMANBRACK CAPITAL GROUP PLC (08945805)
- Candidatul de TVA găsit în Step 2 (căutare Google „CaymanBrack” „VAT”) era pe pagina **altei firme**: Endole Open, https://open.endole.co.uk/insight/company/09325294-blockchain-gb-limited
  - firma de pe pagină: Blockchain (GB) Limited, 09325294; VAT Number GB205886786;
  - tot pe pagină: Size Medium, SIC 62012, „Part of Blockchain Group” (4 firme), proprietar internațional.
- Pentru CaymanBrack: candidatul GB205886786 → **respins_alta_firma**. CaymanBrack rămâne fără TVA găsit.

### Verificare HMRC: 205886786
- **Valid UK VAT number**; nume_hmrc: BLOCKCHAIN (GB) LIMITED; adresa_hmrc: Third Floor, 86-90 Paul Street, Hackney, London, **EC2A 4NE**.
- Fără număr de referință pe pagină.
- În subsolul paginii: conținut sub Open Government Licence v3.0, „except where otherwise stated”. De verificat dacă acoperă și rezultatele verificărilor (relevant pentru Part 3).

### Comparație cu Companies House
- 09325294: BLOCKCHAIN (GB) LIMITED, regaddresspostcode **SK4 2LP**, categoria conturi GROUP (grup 4), SIC 62012.
- Nume HMRC = nume CH ✓; cod poștal HMRC (EC2A 4NE) ≠ CH (SK4 2LP) ✗ → **incert**.

### Observație: SK4 2LP e o adresă comună
- SK4 2LP este și codul poștal al CaymanBrack; asta explică probabil legătura dintre cele două firme în căutare.
- În fișierul CH, **219 firme** au regaddresspostcode = SK4 2LP, cu activități foarte diferite.

### Adrese de sediu social comune (DuckDB, grupare după cod poștal + primul rând al adresei)

| prag (firme/adresă) | adrese | firme la ele | % din total |
|---|---|---|---|
| ≥ 2 | 525.503 | 3.449.935 | 61,6% |
| ≥ 10 | 34.860 | 2.115.327 | 37,8% |
| ≥ 100 | 4.033 | 1.283.031 | 22,9% |

- Total cu cod poștal: 5.598.126 (din 5.689.366 rânduri).
- Top adrese: 71-75 Shelton Street, WC2H 9JQ (86.448 firme); 128 City Road, EC1V 2NX (42.746); 167-169 Great Portland Street, W1W 5PF (23.525).
- **Adresa HMRC a Blockchain (EC2A 4NE, 86-90 Paul Street) e și ea în top:** „3RD FLOOR, 86-90” (13.559) + „86-90 PAUL STREET” (9.091). Deci și adresa de la HMRC poate fi o adresă de serviciu.
- Același loc apare scris în mai multe feluri (86-90 Paul Street; 124 / 124-128 City Road; 20 / 20-22 Wenlock Road), deci cifrele sunt subestimate.

### Concluzii pentru validare
- Codul poștal e un **indiciu**, nu o dovadă. Greutatea lui depinde de câte firme stau la acea adresă.
- O nepotrivire de cod poștal nu înseamnă automat altă firmă, pentru că HMRC și CH pot ține adrese de tipuri diferite.
- Idee: o coloană cu numărul de firme de la adresa CH.

### Rânduri fără cod poștal (~91.000)
- Cele mai multe sunt entități britanice fără țară la sediu: Charitable Incorporated Organisation (40.416), Registered Society (10.811), Scottish CIO (7.923), Limited Partnership (6.037).
- Restul includ Overseas Entity din Insulele Virgine Britanice (4.035), Hong Kong, Seychelles, Panama, plus „Other company type” din SUA și Irlanda.
- Fișierul CH conține deci și entități care nu sunt firme comerciale obișnuite.

### Presupuneri ale asistentului AI (neverificate)
- Adresele cu multe firme sunt probabil ale contabililor sau ale furnizorilor de „registered office address”.
- HMRC poate avea adresa principală de activitate, iar CH sediul social (confirmat ulterior empiric: Laine, Stratford, Instep).
- Organizațiile caritabile și „Registered Society” au adresa ținută în principal la alt regulator, de aceea lipsește din CH.
- Un cod poștal UK acoperă de obicei mai multe clădiri.

---

## Step 4 – Endole pe 30 de firme

Detalii complete: `docs/notes/endole_30.md`. Date: `data/hmrc_checks/urma_endole_30.csv`, `data/hmrc_checks/explorare_grupuri_endole.csv`.

- Eșantion: 30 de firme aleatorii din grupul 4 (`set_explorare_endole.csv`).
- Endole afișează TVA la 13/30 (43%, IC 95% Wilson: 27–61%). Toate cele 13 sunt valide la HMRC, pe numele exact al firmei: 0 fals-pozitive.
- Potrivire de cod poștal: 9/13. Restul de 4 au cauze normale: HMRC rămâne în urmă după o mutare, sau HMRC ține adresa de activitate, iar CH sediul social.
- „Lipsă” pe Endole ≠ fără TVA: 8 din 17 aproape sigur au TVA (evaluare după mărime și activitate, neverificată la HMRC).
- Căutarea în grupul firmei: 0 TVA proprii la 6 firme, +40% timp. Nu o mai folosesc ca pas standard.
- Timp: ~2,8 min per firmă (estimat pe intervale), ~6,5 min per TVA valid găsit.
- **Decizie:** agregatorii nu sunt direcția principală. Acoperirea e limitată, iar Terms 2.5 interzic automatizarea.
- De corectat la un eșantion final: excluderea SIC 74990 (AES Barry, non-trading, a scăpat filtrului).

### Filtrul de import/export după SIC (pentru pista EORI)
- Diviziunile 01–03, 05–09, 10–33, 46, 47, 49–52 (bunuri, producție, comerț, transport): **19,0%** din toate firmele (1.080.113 din 5.689.367); 19,2% pe FULL/GROUP/MEDIUM (121.473). Pe eșantionul Endole: 5/30.
- E o limită de sus: diviziunea 47 (retail) include multe magazine mici; 49 include taxiuri.
- De refăcut cu AUDIT EXEMPTION SUBSIDIARY inclus, ca să fie exact grupul 4 (asistentul a omis categoria din cod).

### Suma de control a TVA UK (mod 97)
- Funcția mea, testată pe cele 13 numere confirmate: 13/13 True; `123456789` → False.
- Un număr aleator de 9 cifre trece cu probabilitate ~2/97 ≈ 2% → ~20,6 milioane de combinații valide din 10⁹. Argument pentru debate: brute force pe HMRC e o idee proastă.

---

## Step 5 – Common Crawl, Pasul 1 („pornind de la firmă”)

Detalii complete: `docs/notes/cc_step1.md`. Codul (v1 → v3) e în `notebooks/04_cc_step1_from_company.ipynb`.

**De unde a venit ideea.** Common Crawl nu e numit în enunț. L-a propus asistentul AI (Claude), ca interpretare a indiciului „bulk web corpora: crawling site by site may be the wrong shape”. Decizia de a-l testa a fost a mea.

**Întrebarea:** dacă știu site-ul firmei, găsesc TVA-ul în arhiva Common Crawl, fără să vizitez site-ul?

**Eșantion:** 12 firme, adică cele 13 cu TVA confirmat din Endole, minus Mohari (fără site). Domeniile sunt luate din Endole. E un test al metodei, nu al acoperirii, pentru că știam dinainte răspunsul corect.

**Codul** l-am scris cu ajutorul asistentului AI. Bug-urile din v1 și v2 erau în codul generat; le-am găsit pentru că rezultatele nu se potriveau cu ce vedeam pe site-uri.

| Versiune | TVA găsit | Ce era greșit / ce am reparat |
|---|---|---|
| v1 | 1/12 | Erorile 504 ale serverului de index erau tratate ca „domeniu absent”; `domeniu/*` nu prindea `www.`; conținutul nu era decodat corect |
| v2 | 1/12 | Reparat cu `matchType=domain`, `warcio` și separarea erorilor de absențe (BP3: 0 → 228 de pagini). Rămânea o problemă: PDF-urile erau ignorate |
| v3 | 2/12 | Citire PDF (`pypdf`) + prioritizare pe niveluri. Laine e găsit la pagina 0; în v2, 73 de PDF-uri cu „policy” în nume ocupau primele 30 de locuri |

**Rezultate (v3 + reîncercare, `CC-MAIN-2026-39`):**
- 10/12 domenii în crawl (lipsesc Haulfryn și Stratford); ABQ are doar 2 pagini, ESL doar 1.
- TVA găsit: 2/12 (Laine: PDF Terms, pct. 1.4; Rope & Sling: pagina Contact). 0 fals-pozitive pe 172 de pagini.
- Numărul CH apare lângă TVA în 2/2 cazuri.
- Verificare de mână pe site-urile live: 5 din 7 nu publică TVA-ul (Red, Encirc, BP3, Jera Nex, Wahed), inclusiv firme cu £170M–567M cifră de afaceri.
- PDF-ul Laine e în `2026-39`, dar nu și în `2026-34`, `2026-30`, `2026-25`.
- Timp: ~50 s per firmă, dominat de erorile 504 ale indexului.

**Concluzia mea:** când TVA-ul e pe site și pagina e în crawl, metoda îl găsește. Limita principală o pun firmele, care nu își publică numărul, nu unealta. A doua limită e acoperirea variabilă de la un crawl la altul.

**Decizie:** trec la Pasul 2, „pornind de la număr”. Vreau să văd dacă numerele firmelor care nu-și publică TVA-ul apar pe alte site-uri.

### Neverificate
- Jera Nex: captura cu Terms poate fi de pe alt site.
- Greenspruce, ABQ, ESL, Haulfryn, Stratford nu au fost verificate de mână.
- La scară, indexul columnar sau procesarea pe AWS ar evita erorile 504 (propunere a asistentului, de verificat pentru Part 3).

---

## Step 6 – Common Crawl, Pasul 2 („pornind de la număr”)

**Întrebarea:** dacă extrag orice număr de TVA UK din pagini web oarecare, cât de des e corect și pot afla a cui firmă e?

**Codul** l-am scris cu ajutorul asistentului AI (Claude). Notebook: `notebooks/05_cc_step2_from_number_wet.ipynb`.

### Date
- Crawl `CC-MAIN-2026-39`: 100.000 de fișiere WET. Am ales aleatoriu 3 (seed 42), adică 0,003% din crawl. Lista: `data/samples/cc_pas2_fisiere_alese.csv`.
- ~65 MB per fișier, ~21.000 de pagini per fișier; total 64.082 de pagini, dintre care 1.302 pe domenii `.uk`.
- Timp per fișier: ~22 s descărcare (de pe laptop) + ~16 s procesare. Tot crawl-ul: ~6,5 TB comprimat; ~44 de zile serial de pe laptop.

### Metoda
1. Regex: „VAT” urmat în max. 40 de caractere (fără cifre) de 9 cifre, cu sau fără „GB”, spații sau cratime (`vat_kw`). Separat: „GB” + 9 cifre fără „VAT” (`gb_fara_vat`).
2. Filtru checksum mod 97 (aceeași formulă ca funcția mea din Step 4).
3. Din textul din jur (±200 de caractere): numărul CH, dacă apare.
4. Legarea numărului CH de fișierul Companies House (DuckDB).
5. Verificarea la HMRC (pagina web, de mână) a primelor 31 de numere, într-o ordine aleatorie (seed 42).
6. Atribuirea: numele de la HMRC, normalizat (LIMITED → LTD, & → AND, fără „THE”, fără punctuație și spații), căutat în CH; confirmare prin codul poștal și prin numărul CH din context.

### Rezultate: extragere
- 165 de potriviri; 121 trec checksum-ul (`vat_kw`: 116/155; `gb_fara_vat`: 5/10, deci mai zgomotos).
- **108 numere unice**, pe 106 site-uri.
- 74/108 au un număr CH în context; 72 dintre ele există în fișierul CH.
- Cele 2 negăsite: SC005336 (biology.ed.ac.uk, număr de organizație caritabilă scoțiană, University of Edinburgh) și 00454825 (retailrevealed.com, pagină de expozanți).
- Pagini cu cuvântul „VAT”: ~225 per fișier (~1,1%); majoritatea nu conțin un număr.
- Mărimea firmelor (cele 72 găsite în CH): grup 4 = 24 (33%), grup 3 = 45, grup 2 = 3. În tot CH, grupul 4 e doar 2,7% → firmele mari sunt de ~12 ori supra-reprezentate. Atenție: părtinire posibilă, pentru că sunt doar firmele care scriu numărul CH pe pagină.

### Rezultate: verificarea la HMRC (31 de numere)
- **Invalide la HMRC: 1/31 (3,2%; IC 95% ~0,6–16%).** Charlotte Tilbury (144073630, pagina `/au/`). Regex-ul a citit corect („VAT number: GB 144 0736 30”); numărul apare în subsolul global al site-ului, inclusiv lângă Charlotte Tilbury Beauty Inc. (Delaware). HMRC nu-l recunoaște → număr publicat de firmă, invalid (probabil vechi). **Nu e o eroare a extragerii:** rata de eroare a regex-ului e 0/31; singurul invalid vine din sursă.
- Valide cu număr CH în context: 21. Numele HMRC = numele CH la 19/21 (12 cu același cod poștal, 7 cu cod poștal diferit).
- Valide fără număr CH: 9. Toate găsite în CH după numele de la HMRC, câte o singură firmă, cu același cod poștal.
- **Comparația celor două metode de atribuire:** numărul CH din context și căutarea după numele HMRC dau aceeași firmă la 19/21. La 2/21 diferă, iar numele HMRC duce la altă firmă, care există:
  - taylormaxwell.co.uk: context 00476749 TAYLOR, MAXWELL & CO → HMRC 05726000 TAYLOR MAXWELL GROUP LTD (holding sau VAT group?);
  - veeve.com: context 07666067 UNIQUE VENTURES → HMRC 08968561 UNDER THE DOORMAT LTD.
- **Total: 30/30 de numere valide atribuite unei singure firme din CH.**

### Concluziile mele
1. **Precizia e foarte mare:** 30 din 31 de numere extrase sunt valide, iar toate cele valide pot fi atribuite.
2. **Cheia de atribuire e numele de la HMRC, nu numărul CH din pagină.** Numărul din pagină poate fi al altei firme din grup (2/21). Îl folosesc ca verificare; când nu concordă, notez „grup / posibil VAT group”.
3. **Codul poștal e un semnal slab la adresele de serviciu** (W1W 5PF, EC2A 4NE, WC2H 9JQ apar și aici).
4. **Filtrul pe `.uk` sau pe engleză ar rata numere reale:** Cochrane (pagină în rusă, `.org`), Whisky Marketplace (`.sg`).
5. **Acoperirea nu e măsurată aici.** Pasul 2 măsoară precizia. Măsurarea acoperirii o fac separat (vezi testul pe eșantionul Find a Tender).
6. Mărcile diferă des de numele juridic (buysheds → ILIKESTORES, warmco → NOMOCO, holidaysplease → HAYS TRAVEL). Atribuirea după numele site-ului n-ar funcționa.
7. Nu toate numerele aparțin unor firme: unele sunt ale unor organizații care nu sunt în Companies House (universități, organizații caritabile).

### Transcrierea HMRC
Am copiat textul paginilor HMRC în chat, iar asistentul AI l-a transcris în `data/hmrc_checks/hmrc_transcriere.csv`. Ora e aproximativă (ora mesajului, convertită în BST).

### Fișiere
`data/results/cc_pas2_candidati.csv`, `cc_pas2_statistici.csv`, `cc_pas2_verificare_hmrc.csv` (include și potrivirea cu CH), `hmrc_transcriere.csv`, `cc_pas2_rezultat_hmrc.csv`.

### Neverificate / de făcut
- [x] Checksum: funcția din Pasul 2 are aceeași formulă ca funcția mea testată pe 13 numere confirmate (13/13).
- [x] Charlotte Tilbury: număr publicat de firmă, invalid la HMRC (vezi mai sus).
- [x] SC005336 = număr de organizație caritabilă scoțiană (University of Edinburgh).
- [x] Potrivirea cu CH salvată în `cc_pas2_verificare_hmrc.csv`.
- [ ] Regula de unicitate a numelor în CH (gov.uk).
- [ ] Veeve ↔ Under The Doormat (fost nume?).
- [ ] accreditedengineers.com: director sau site propriu al Newbury Investments?
- [ ] Sondaj pe transcrierea HMRC (4 numere).

### Greșeli ale asistentului AI, găsite pe parcurs
- Indicatorul `pagini_cu_cuvant_vat` căuta subșirul „vat” (prindea „private”, „elevator”): ~4.900 → ~225 per fișier după corectură. Potrivirile nu au fost afectate.
- Estimarea mărimii unui fișier WET (100–200 MB) era greșită: în realitate ~65 MB.
- Numărarea în timpul verificării (29/30 în loc de 30/31), corectată în fișier.
- Regex-ul pentru numărul CH prinde și numere de organizații caritabile („registered … number”).
- Funcția de checksum a fost rescrisă din memorie în loc să fie refolosită funcția mea; formula s-a dovedit identică.
- Primul test de checksum propus raporta „True” pe o listă goală (fals-liniștitor); al doilea test propus era circular (pe numere deja filtrate de checksum).
- A inversat etichetele a două numere: corect, Laine = 211105734 și Rope & Sling = 811037280.

---

## Step 7 – Registre publice de cheltuieli

**Întrebarea:** registrele publice de plăți către furnizori (indiciul „public records / public spending” din enunț) conțin numărul de TVA al furnizorului? Dacă da, ar acoperi exact firmele care nu își publică TVA-ul pe site (golul lăsat de Common Crawl).

**Rolul asistentului AI (Claude):** a căutat ghidurile oficiale și paginile autorităților, a citit prin fetch web structura fișierului Dorset și ghidul HM Treasury, și a scris codul de verificare. Descărcarea fișierelor, rularea codului și concluziile sunt ale mele.

### 1. Autoritățile locale (plăți > £500)

**Regula oficială:** Local Government Transparency Code 2015 obligă autoritățile locale din Anglia să publice, pentru fiecare plată > £500: data, departamentul, beneficiarul, scopul, suma, TVA-ul nerecuperabil și categoria comerciantului.
- „VAT” înseamnă aici **o sumă de bani** (TVA-ul nerecuperabil), nu numărul de TVA al furnizorului.
- Codul **nu cere** numărul de TVA. Pentru contractele > £5.000 cere un „registration number” doar dacă furnizorul e IMM sau organizație de voluntariat (interpretarea mea: nr. CH sau de caritate, de verificat în textul oficial).

**Verificare empirică:** 2 autorități, aceeași lună (iunie 2026), fișiere în `data/registre/`.

| | Dorset Council | Kirklees Council |
|---|---|---|
| Fișier | `dorset_2026_06.csv` | `kirklees_2026_06.xlsx` |
| Rânduri | 11.113 | 5.669 |
| Coloane | Directorate, Description, Invoice Number, Vendor, Date, Amount | Payment Date, Transaction Number, Amount Excluding VAT, Vendor Number, Vendor Name, **Company Number**, …, Purpose of Spend (14 coloane) |
| Coloană de TVA furnizor | **nu** | **nu** |
| Număr CH | nu | da, la **396 din 1.219 furnizori (32%)**; format inconsecvent (fără zerouri în față, un caz cu 5 cifre) |
| Rânduri redactate | **5.776 (52%)** | **953 (17%)** |
| Numere de 9 cifre care trec checksum-ul | 0 | 6, niciunul TVA (vezi mai jos) |

**Cele 6 „numere valide” de la Kirklees:**
- 4 sunt artefacte ale codului: cifre din două celule vecine, lipite la unirea textului.
- 2 sunt numere de referință din textul liber „Purpose of Spend”: „MDT (200115687)” și „PN 260005808”. Au trecut checksum-ul întâmplător (~2% din numerele de 9 cifre trec).
- **Rezultat: 0 TVA-uri în 16.782 de rânduri.**

**Alte observații:**
- Conținutul diferă mult între autorități: Dorset publică minimul, Kirklees publică în plus nr. CH (peste ce cere codul).
- Numele furnizorilor sunt uneori tăiate („…WELLBEING LIMIT”) sau sunt mărci („RAYFORD LTD T/A RADIO CABS”). Legarea de CH după nume ar fi aproximativă.
- Acces: la prima încercare, dorsetcouncil.gov.uk refuza accesul din România („This page is unavailable”, pagina lor de eroare), deși fetch-ul asistentului (din afara UK) mergea. La o încercare ulterioară a mers. Implicație pentru Part 3: o colectare automată poate fi blocată în funcție de țara de origine.

### 2. Guvernul central (plăți > £25.000)

**Documentul:** HM Treasury, „Guidance for publishing spend over £25,000”, fișier gov.uk 662332 (https://assets.publishing.service.gov.uk/government/uploads/system/uploads/attachment_data/file/662332/guidance_for_publishing_spend.pdf). Fără dată sau versiune în document; versiunea citită e din 2013 sau mai nouă (nota de subsol 1, p. 3, citează o arhivă web din 04.01.2013). Prima versiune: v1.0, 30 iulie 2010. Inițiativa pornește de la scrisoarea prim-ministrului din 31 mai 2010 (pct. 1.1).

**Regula:** se aplică tuturor organismelor guvernului central (departamente, agenții, NDPB-uri, organisme NHS etc.).
- Câmpuri obligatorii: departament, entitate, dată, tip și zonă de cheltuială, **furnizor (doar numele, fără adresă)**, număr tranzacție, sumă, descriere.
- Câmpuri opționale: cod poștal furnizor, tip furnizor (Large / SME / VCS / Public Sector), nr. contract, cod proiect, tip cheltuială.
- **Câmpul 15, „VAT Registration Number” al furnizorului: colectat, dar „Not to be published until requested by the Treasury”.** Scopul declarat: agregarea plăților pe furnizor chiar când numele e scris diferit.
- Confirmat de mine în PDF: p. 8 (secț. 2.13: se colectează, dar „for the time being” nu se publică) și p. 14 (tabelul 3.1, rândul 15).

**Concluzie:** statul **are** TVA-ul furnizorilor pentru plățile mari, dar **alege să nu-l publice**. Dead end prin decizie de politică, nu prin lipsa datelor.

### Concluziile mele
1. **Registrele publice de cheltuieli sunt un dead end pentru TVA:** nici regula, nici practica (0 în 16.782 de rânduri) nu-l oferă.
2. Cel mai aproape de o sursă a fost **ghidul guvernului central**, care colectează TVA-ul furnizorilor, dar nu-l publică. Nu poate fi baza unui produs, pentru că publicarea depinde de o decizie a Trezoreriei.
3. Unele autorități (Kirklees) oferă un **identificator adiacent (nr. CH)** pentru o parte din furnizori: o listă de firme active în comerț cu sectorul public, dar fără TVA.
4. **Checksum-ul singur dă fals-pozitive** pe numere de referință. Confirmă regula din Pasul 2: numărul trebuie să apară lângă cuvântul „VAT”.

### Greșeli ale asistentului AI
- Primul regex nu avea `(?<!\d)`: ar fi prins ultimele 9 cifre din numerele de factură de 10 cifre. Corectat înainte de rularea finală.
- Codul a lipit celulele vecine, ceea ce a creat 4 „numere” false.
- Căutarea coloanei de furnizor a prins `Vendor Number` în loc de `Vendor Name` → „0 redactate” și „1.530 furnizori” greșite la Kirklees. Corect: 953 redactate, 1.219 furnizori.
- Primul link Dorset (iulie 2026) și cel din 2024 nu funcționau.

### De verificat de mine
- [ ] Textul oficial al Local Government Transparency Code 2015 (gov.uk): ce înseamnă exact „registration number”.
- [x] PDF-ul HM Treasury, secțiunea 3.1, rândul 15: verificat de mine (p. 8 și p. 14).
- [ ] Opțional: un fișier > £25.000 al unui departament, pentru confirmare empirică.

### Fișiere și surse
- `data/registre/dorset_2026_06.csv`, `data/registre/kirklees_2026_06.xlsx`
- Local Government Transparency Code 2015 (gov.uk)
- Dorset Council, Payments to suppliers over £500: https://www.dorsetcouncil.gov.uk/w/payments-to-suppliers-over-500
- Kirklees Council, Expenditure data: https://www.kirklees.gov.uk/beta/information-and-data/expenditure-data.aspx

---

## Step 8 – Achiziții publice, Find a Tender (API OCDS)

**Întrebarea:** contractele publice atribuite (Find a Tender) conțin numărul de TVA al furnizorului? Ultima sursă din pista „public records” din enunț.

**Rolul asistentului AI (Claude):** a găsit API-ul și standardul OCDS prin căutare web și a scris codul. Documentația API-ului am citit-o eu de pe site (pagina „Data and API documentation”), iar codul l-am rulat eu.

### Sursa
- Find a Tender (find-tender.service.gov.uk): anunțurile de achiziții publice din UK, inclusiv contractele atribuite.
- **API public, gratuit, format OCDS 1.1.5 (JSON).** Licență: **Open Government Licence v3**, inclusă în fiecare răspuns → date reutilizabile legal.
- Parametri: `limit` (max 100), `cursor`, `updatedFrom`, `updatedTo`, `stages` (planning/tender/award). Paginare prin `links.next`.
- Limită de cereri: răspunsuri 429/503 cu header `Retry-After`.
- Pagina principală mai arată o sursă nouă, apărută cu Procurement Act 2023: **„Payments transparency register”** (plăți legate de contracte publice). Neverificată.

### Test 1: identificatorii furnizorilor (500 de contracte atribuite, sept. 2026)
- 1.480 de apariții de furnizori. Identificator principal: **GB-COH 49%**, lipsă 48%, GB-NHS 2%, GB-CHC <1%.
- `additionalIdentifiers`: **0**. **TVA (GB-VAT): 0.**
- Exemplul cu `GB-VAT` din documentația OCDS (standard.open-contracting.org) e **doar ilustrativ**; nu apare în datele reale UK.
- Numărul CH apare uneori fără zerourile din față (`GB-COH-2644862`) → aceeași normalizare ca la Kirklees.
- Un furnizor mai are: nume juridic, adresă cu cod poștal, `details.url` (site), `scale` (large/sme).

### Test 2: cât de des sunt completate câmpurile (1.371 de furnizori unici)
- Cu nr. CH: 51% | cu site: 38% | cu ambele: 32% (436) | cu cod poștal: 82%.
- Mărime: 30% large, 70% SME.

### Test 3: eșantion pentru Common Crawl (ideea: Find a Tender → site → CC Pasul 1)
**Scopul:** un eșantion nepărtinitor de firme active, cu site, pentru a măsura acoperirea Common Crawl. Eșantionul din CC Pasul 1 era părtinitor (12 firme alese pentru că aveau TVA pe Endole).

**Încercarea 1** (30 de furnizori aleși direct din cei 436, seed 42): **26 din 30 din sectorul de îngrijire**.
- Cauza: **26 din 500 de contracte (5%)** sunt acorduri-cadru cu până la **76 de furnizori**; ele adună **61% din aparițiile de furnizori**. CPV 85 (sănătate și asistență socială) = 53%. Contractul tipic are 1 furnizor (mediana).
- Problemă suplimentară: serviciile de îngrijire sunt în mare parte scutite de TVA [din memoria asistentului, de verificat VAT Notice 701/2] → un „negăsit” n-ar mai însemna „metoda a ratat”.
- Multe domenii erau de grup sau de franciză (homeinstead.co.uk, shaw.co.uk, jobs.careconcerngroup.com).
- **Eșantion abandonat.** Fișierul a fost suprascris; rezultatul e documentat doar prin output-ul din notebook.

**Încercarea 2** (un furnizor per contract, fără CPV 85, 1.000 de contracte): **doar 10 contracte eligibile** (`data/samples/fat_esantion_30.csv`).
- **În 3 din 10, `details.url` nu e site-ul furnizorului:** True Compliance Ltd → camden.gov.uk; MPS UK Group → liv-coll.ac.uk; un consiliu local (Stockton) apare chiar ca „furnizor”.

**Încercarea 3** (ian.–sept. 2026, 6.000 de contracte atribuite; un furnizor per contract; fără CPV 85 și fără site-uri .gov/.ac/.nhs; seed 42): CPV 85 = 2.174 de contracte (36%). Din 3.826 rămase, doar 48 (1,3%) au furnizor cu nr. CH + site. Eșantion de 30: 14 diviziuni CPV, 17 large / 13 SME (`data/samples/fat_esantion_30_v3.csv`).
- Limita API: 429 cu Retry-After 120 s la fiecare ~10 pagini; 60 de pagini în ~6,5 min.
- **Verificare nr. CH (Find a Tender → CH):** 30/30 există și sunt aceeași firmă; 24 identice după normalizare, 6 diferă prin forma juridică lipsă, abrevieri („CO”/„COMPANY”, „U.K.”) sau o greșeală de tastare în FaT („Vilolet-Shift”). Cazul 03341304 („Stockton Council” în încercarea 2) = MRI Software Limited → eroare de introducere la publicator. **Lecție:** normalizarea de nume trebuie să ignore forma juridică și abrevierile (6/30 fals-negative cu regula actuală).
- Eșantion: 19/30 în grupul 4 (FULL 13, GROUP 5, AES 1).
- **Verificarea domeniilor** (făcută de asistentul AI prin fetch web, doar pe prima pagină; de confirmat de mine prin sondaj): 21 da, 2 grup (PAM → altă entitate juridică; Aebi Schmidt → site global), 2 nu (Univ. of Bristol → nccuk.com; Kind & Co → londonconstructionprogramme.co.uk), 5 neverificabile (2 blochează roboții, 3 inaccesibile uneltei). TVA vizibil pe prima pagină: 2/26 (Ford Retail, Instep).

### Concluziile mele
1. **Find a Tender nu conține TVA-ul furnizorului (0 în 1.480 de apariții).** Dead end pentru TVA.
2. **Identificator adiacent bun:** numărul CH la ~50% din furnizori, corect în 30/30 de cazuri verificate, sub licență deschisă.
3. **Câmpul „site” e nesigur** (completat rar și inconsecvent, uneori cu site-ul cumpărătorului). Find a Tender nu rezolvă fiabil problema „firmă → domeniu” din CC Pasul 1.
4. **Eșantionarea pe furnizori e părtinită de acordurile-cadru.** Orice eșantion din date de achiziții trebuie făcut la nivel de contract, nu de furnizor.
5. **Decizia mea:** am extins perioada (încercarea 3) și am construit un eșantion la nivel de contract, verificat pe CH și pe site; l-am folosit pentru testul Common Crawl de mai jos.

### Greșeli și presupuneri ale asistentului AI
- A prezentat inițial exemplul `GB-VAT` din documentația OCDS ca pe o posibilitate reală; datele au arătat că nu apare.
- Parametrii API-ului au fost scriși întâi din memorie; confirmați apoi din documentația oficială.
- Prima schemă de eșantionare (pe furnizori) nu a ținut cont de acordurile-cadru mari.
- „GB-PPON = identificator introdus de Procurement Act 2023” e din memoria asistentului, neverificat.

### Fișiere și surse
- `data/registre/find_a_tender_scheme.json`, `data/registre/fat_award_2026_01_09.jsonl` (6.000 de contracte, nu intră în repo), `data/samples/fat_esantion_30.csv`, `data/samples/fat_esantion_30_v3.csv`, `data/results/fat_esantion_30_v3_verificat_ch.csv`
- Find a Tender, Data and API documentation (pagina OCDS release package API, citită de mine)
- OCDS, Organization identifiers: https://standard.open-contracting.org/latest/en/guidance/map/organization_identifiers

---

## Step 9 – Common Crawl pe eșantionul Find a Tender (măsurarea acoperirii)

**Întrebarea:** pe un eșantion de firme active, cu site verificat, ales **fără** legătură cu vreo sursă de TVA, în câte cazuri găsește Common Crawl TVA-ul firmei?

**Codul:** `notebooks/08_cc_on_fat_sample.ipynb`, scris de asistentul AI pe baza descrierii v3 din Pasul 1 (codul v3 original e în `notebooks/04_cc_step1_from_company.ipynb`, găsit ulterior). Crawl `CC-MAIN-2026-39`, max. 30 de pagini/domeniu, HTML + PDF, prioritizare Terms/Contact/Legal. Spre deosebire de Pasul 1, TVA-ul corect nu era cunoscut dinainte: codul colectează orice număr valid, iar verificarea se face la HMRC.

### Rezultate
- 26 de firme (21 domenii „da” + 5 „neverificat”); 1 cu eroare de server persistentă (MRI Software) → **25 cu rezultat**.
- **Test de control:** Ford Retail și Instep (TVA vizibil pe prima pagină) găsite corect, la prima pagină citită.
- **Domenii în crawl: 19/25 (76%).** Absente: Inspectas, Violet-Shift, Thinks, Places for People Leisure, Crawford & Co, TW Engineering.
- **TVA găsit: 4/25 firme; 5 numere, toate valide la HMRC (5/5).**
- Atribuire (nume HMRC):
  - 3 pe numele exact al firmei: Ford Retail (833053650), Instep (736669489; HMRC scrie „INSTEP (UK) LIMITED”, cod poștal diferit: Warrington vs Londra), TLT LLP (752995876);
  - 1 pe numele altei entități din grup: Carter Jonas LLP → „CARTER JONAS SERVICE COMPANY” (256845862, aceeași adresă);
  - 1 al altei entități de pe aceeași pagină: TLT (NI) LLP (129500920, Belfast), corect neatribuit.
- **Acoperire: 12% (3/25) pe numele exact; 16% (4/25) incluzând cazul de grup.** Consistent cu Pasul 1 (2/12).
- Toate TVA-urile găsite erau pe pagini juridice (Terms, Legal notices). Numărul CH apare lângă TVA doar la 2/4 → atribuirea trebuie făcută prin numele HMRC.

### Cazul Carter Jonas
În CH, 6 firme la W1G 0BG: CARTER JONAS LLP (OC304417, GROUP), CARTER JONAS SERVICE COMPANY (00786457, FULL, activă), CARTER JONAS ENTERPRISES LIMITED, CARTER JONAS ACQUISITIONS LTD, CARTER JONAS LIMITED (dormant), THE CARTER JONAS GROUP LIMITED (dormant). TVA-ul 256845862 e pe numele Service Company la HMRC, deși site-ul îl atribuie LLP-ului → probabil VAT group, cu Service Company ca membru reprezentant (ipoteză, neverificabilă din date publice). Al doilea caz după Taylor Maxwell (Pasul 2).

### Observații
- Ipoteza asistentului „site-urile care blochează roboții lipsesc din crawl” s-a confirmat doar parțial: Places for People Leisure e absent, dar Bytes e prezent cu 103 pagini.
- Limită: max. 30 de pagini/domeniu; la site-uri mari (Holt 1.197, TLT 679, Burges Salmon 637) s-a citit o mică parte.
- Formularul HMRC a respins un număr corect copiat din pagina web (caracter invizibil); tastat de mână a mers.
- Timp: ~20 min pentru 26 de firme (~46 s/firmă), dominat de erorile 504 ale indexului.

### Concluzia mea
Common Crawl e **foarte precis** (5/5 numere valide), dar acoperă **~1 din 8 firme** (12–16%). Pierderile vin din două locuri: 24% din domenii lipsesc complet din crawl, iar din cele prezente ~79% nu au TVA în primele 30 de pagini citite. Atribuirea e partea grea: 2 din 5 numere găsite pe site-ul firmei nu erau ale ei.

### Fișiere
`data/results/cc_fat_rezultat_firme.csv`, `data/results/cc_fat_candidati.csv`, `data/hmrc_checks/hmrc_transcriere_fat.csv` (5 numere, transcrise de asistentul AI)

---

## Step 10 – EORI

**Întrebarea:** poate EORI (identificatorul vamal) să ofere TVA-ul firmelor care nu și-l publică direct?

**Ipoteza** (din memoria asistentului AI, de confirmat oficial): pentru firmele înregistrate în scopuri de TVA, EORI UK = GB + TVA (9 cifre) + 000. Orice EORI găsit public ar da TVA-ul.

**Eligibilitate:** ~19% din firme au un SIC de comerț cu bunuri (limită de sus a celor care ar putea avea EORI; de refăcut pe grupul 4 exact).

**Test empiric** (aceleași 3 fișiere WET din Pasul 2, 64.082 de pagini, cod scris de asistentul AI):
- Pagini cu cuvântul „EORI”: 8 (față de ~676 cu „VAT”).
- Numere EORI găsite: 1 (față de 108 TVA-uri unice).
- Singurul caz: GB717899083000 (thedjshop.co.uk): sufix 000 ✓, primele 9 cifre trec checksum-ul TVA ✓ și sunt identice cu TVA-ul găsit pe aceeași pagină în Pasul 2 ✓.

**Concluzia mea:** formatul GB + TVA + 000 e consistent cu datele (n = 1; de confirmat oficial). Dar EORI apare public de ~100 de ori mai rar decât TVA-ul și doar lângă el, deci nu aduce numere noi. Dead end pentru acoperire.

**Greșeli ale asistentului:** prima variantă a codului căuta subșirul „eori” (prindea „theories”: 641 de pagini în loc de 8) și excludea literele între „EORI” și număr (nu prindea „EORI No: GB…”). Corectate înainte de rezultatul final.

**De făcut:** confirmarea formatului EORI pe gov.uk („Get an EORI number”).

Fișier: `data/results/eori_pas2_wet.csv`

---

## Rezumat: surse încercate

| Sursă | Precizie | Acoperire | Utilizabilă într-un produs? | De ce |
|---|---|---|---|---|
| Companies House | – | 0% (nu are TVA) | da, ca bază de legătură | nr. CH, nume, adresă, categoria conturilor |
| Google + site, de mână | – | nemăsurată | nu | nu scalează |
| HMRC (web / API) | sursa de adevăr | – | API-ul de producție cere firmă înregistrată | validare: nume + cod poștal, fără nr. CH |
| Endole (agregator) | 13/13 | 43% (grup 4) | nu | Terms interzic automatizarea |
| Common Crawl, de la firmă | 5/5 + 2/2 | 12–16% (eșantion nepărtinitor) | da | majoritatea firmelor nu publică TVA-ul; 24% din domenii lipsesc din crawl |
| Common Crawl, de la număr | 30/31 valide, 30/30 atribuite | nemăsurată pe populație | da | precis; atribuire prin numele HMRC |
| Cheltuieli publice locale | – | 0% | nu | legea nu cere TVA-ul |
| Cheltuieli guvern central | – | 0% | nu | TVA colectat, dar nepublicat |
| Find a Tender | – | 0% | nu (pentru TVA) | util pentru nr. CH (OGL v3) |
| EORI | – | ~0% | nu | apare de ~100× mai rar decât TVA-ul, doar lângă el |
