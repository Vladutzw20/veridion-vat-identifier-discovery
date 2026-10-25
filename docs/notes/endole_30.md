# Rezumat 4: Endole ca sursă de TVA, eșantion de 30 de firme

**Etapă:** Step 4 – Endole
**Fișiere:** `data/hmrc_checks/urma_endole_30.csv` (cele 30 de firme), `data/hmrc_checks/explorare_grupuri_endole.csv` (firmele din grup, în afara eșantionului)

## 1. Întrebarea

Pentru câte firme din eșantion afișează Endole un număr de TVA, câte dintre acestea sunt valide la HMRC și aparțin chiar firmei respective, și cât timp costă verificarea?

## 2. Metoda

Pentru fiecare firmă din `set_explorare_endole.csv`:

1. Am deschis pagina Endole a firmei (link construit din număr + slug) și am notat câmpul „VAT Number”: numărul sau `lipsa` (câmpul nu apare).
2. Dacă era un număr, l-am verificat pe „Check a UK VAT number” (HMRC) și am notat numele, codul poștal și ora (BST).
3. La 6 firme fără TVA am căutat și în secțiunea „Mutual Companies” (firme din același grup).
4. Clasificare:
   - **confirmat**: valid la HMRC, nume identic, cod poștal identic cu CH
   - **incert**: valid, nume identic, cod poștal diferit
   - **respins_alta_firma**: numărul găsit aparține altei firme (aici, o firmă soră)
   - **fără candidat**: Endole nu afișează TVA

Timpii sunt **estimați pe intervale, nu cronometrați exact**: 2 minute pentru o firmă obișnuită și 6 minute când am căutat și în grup (limita de sus, deci estimare prudentă). Cronometrul real al sesiunii a fost ~55 de minute, sub cele 84 estimate.

## 3. Rezultate

### 3.1 Vizibilitatea TVA pe Endole

| Indicator | Firme | % din 30 | IC 95% (Wilson) |
|---|---|---|---|
| Endole afișează TVA propriu | 13 | 43,3% | 27,4–60,8% |
| … valid la HMRC | 13 | 43,3% | (13 din 13 valide) |
| … confirmat (nume + cod poștal) | 9 | 30,0% | 16,7–47,9% |
| … incert (doar nume) | 4 | 13,3% | |
| Fără TVA pe Endole | 17 | 56,7% | |

Cu 30 de firme, intervalele sunt largi. Rezultatul corect de raportat este „aproximativ 30–60% din firme au TVA pe Endole”, nu „exact 43%”.

### 3.2 Corectitudinea datelor (verificarea la HMRC)

- **13 din 13 numere afișate de Endole sunt valide la HMRC (100%)**, iar toate sunt pe numele exact al firmei.
- 9 din 13 (69,2%) se potrivesc și la cod poștal; 4 din 13 (30,8%) diferă doar la cod poștal.
- Comparativ cu explorarea din Step 3 (1 TVA afișat din 12, invalid), calitatea în acest eșantion e mult mai bună. Eșantionul de 30 și cel de 12 au fost alese diferit, deci nu se pot compara direct.

Observații de metodă:
- La Red Construction, HMRC scrie numele cu o greșeală („PROJE CTS”). O comparație automată pe text exact ar fi respins-o. Potrivirea de nume trebuie să ignore spațiile și să tolereze mici diferențe („LTD”/„LIMITED”).
- La ABQ, HMRC scrie adresa fără numărul 27. Codul poștal e mai sigur decât adresa completă.
- Link-urile Endole funcționează și pentru numere cu prefix `NI` și pentru nume cu `&`.

### 3.3 Ce înseamnă „lipsa” pe Endole

„Lipsa” **nu înseamnă că firma n-are TVA**. Evaluarea celor 17 cazuri (pe baza mărimii, activității și grupului; nu e verificată la HMRC):

| Evaluare | Firme | Exemple |
|---|---|---|
| Aproape sigur au TVA | 8 | KLA (£358,8M), Wenzels, Stage C, Hodder & Stoughton, A1, Bedford, HID, EDP |
| Neclar (firme-vehicul, locuințe sociale, probabil VAT group) | 6 | Blueprint (Strangers), Lennox, Tritax, MCAP 2, Newarch, Impax |
| Posibil fără TVA (activități scutite) | 2 | Pleo (creditare), Dignus (sănătate) |
| Probabil fără TVA (fără activitate) | 1 | AES Barry (SIC 74990, scăpare de filtru) |

Deci Endole ratează cel puțin 8 firme care aproape sigur au TVA. **Acoperirea este limitată de sursă, nu de lipsa TVA-ului.**

### 3.4 Vizibilitatea pe mărimea firmei (după Endole)

| Mărime | Cu TVA / total |
|---|---|
| Micro | 3 / 9 |
| Small | 4 / 5 |
| Medium | 0 / 4 |
| Large | 5 / 10 |
| Necunoscut | 1 / 2 |

Grupurile sunt prea mici pentru o concluzie. Ipoteza de la jumătatea sesiunii („Endole acoperă mai rar firmele mari”) **nu s-a confirmat**: la final Large are 5 din 10.

### 3.5 Căutarea în grup

| | Valoare |
|---|---|
| Firme din eșantion la care am căutat în grup | 6 (Blueprint Strangers, Bedford, MCAP 2, Dignus, Impax, AES Barry) |
| TVA **propriu** găsit astfel pentru firma din eșantion | **0 din 6** |
| Numere găsite la firme surori | 1 caz util pentru eșantion (MCAP 2 → numărul surorii, clasificat `respins_alta_firma`) |
| Timp suplimentar | 24 min (6 × 4 min) |

În afara eșantionului (`explorare_grupuri_endole.csv`):
- **Grupul Blueprint:** 3 din 6 firme verificate au TVA pe Endole, toate valide la HMRC și pe numele propriu. Fiecare firmă-vehicul are **propriul** număr, deci nu e un VAT group.
- **McAp Global Finance Ltd:** TVA valid, nume și cod poștal identice.
- **Grupurile Bedford, Dignus, Impax, AES:** niciun TVA vizibil.

**Concluzie:** căutarea în grup crește timpul cu 40% (de la 60 la 84 min) și nu a adus niciun TVA pentru firmele din eșantion. Un număr al unei firme surori nu poate fi atribuit firmei căutate fără o dovadă de VAT group. Pentru eșantionul final, căutarea în grup **nu merită** ca pas standard.

### 3.6 Timp

| Indicator | Valoare |
|---|---|
| Timp total estimat | 84 min (24 × 2 + 6 × 6) |
| Medie pe firmă | 2,8 min |
| Timp per TVA valid găsit | 6,5 min |
| Timp per TVA confirmat | 9,3 min |
| Fără căutare în grup (estimare) | 60 min, adică 4,6 min per TVA găsit |

## 4. Teoria despre adresă: când se potrivește HMRC cu Companies House?

**Ipoteza de pornire:** codul poștal de la HMRC coincide cu cel din CH/Endole doar dacă firma nu și-a schimbat adresa de ceva timp.

**Ce arată datele (13 firme cu TVA):**

| Situația adresei în CH | Confirmat | Incert |
|---|---|---|
| Stabilă (fără mutare reală de ≥3 ani) | 6 (Haulfryn, Wahed, Red, Encirc, Jera Nex, Elizabeth School) | 2 (Laine, Stratford) |
| Schimbată | 3 (Mohari, BP3, ABQ) | 2 (Greenspruce, Rope & Sling) |

**Interpretare:**
- Ipoteza are o parte adevărată: adresele stabile se potrivesc mai des (6 din 8, față de 3 din 5).
- Dar în forma „**doar dacă**” e **falsă** în ambele sensuri:
  - **Firmă stabilă, totuși nepotrivire:** Laine are aceeași adresă de 36 de ani, dar HMRC arată școala din Epsom. Stratford arată sediul grupului din Leicester. Cauza nu e timpul, ci faptul că HMRC păstrează **adresa de activitate**, iar CH **sediul social**.
  - **Firmă mutată, totuși potrivire:** BP3 s-a mutat acum 5 luni, Mohari și ABQ acum 1–3 ani, și HMRC are deja adresa nouă. Firma și-a actualizat datele și la HMRC.

**Formularea corectă:** nepotrivirea de cod poștal are cel puțin **două cauze** distincte, ambele observate:
1. **HMRC rămâne în urmă după o mutare.** Exemple: Greenspruce (mutată acum 8 zile; HMRC are a treia adresă), Rope & Sling (HMRC are o adresă care nu e nici actuală, nici anterioară), Blueprint Billboards (HMRC = adresa CH anterioară), Blueprint Seven (HMRC = o adresă și mai veche). În același grup, Blueprint Television are adresa actualizată, deci actualizarea depinde de firmă, nu de grup.
2. **Adresă de activitate față de sediu social:** Laine, Stratford.

**Consecință pentru clasificare:** o nepotrivire de cod poștal, când numărul e valid și numele identic, **nu indică o altă firmă**. Toate cele 4 cazuri „incerte” au explicații normale. Propunere: 
- **potrivire puternică:** valid + nume + cod poștal
- **potrivire pe nume:** valid + nume, cod poștal diferit (acceptabil, cu cauza notată)
- **respins:** nume diferit

Ipoteza merită testată pe un eșantion mai mare, cu data ultimei schimbări de adresă ca variabilă numerică.

## 5. Limitări

- 30 de firme: intervale de încredere largi, iar defalcările pe mărime și adresă au 2–10 firme pe categorie.
- Timpii sunt pe intervale, nu cronometrați exact.
- Evaluarea „aproape sigur are TVA” se bazează pe mărime și activitate, nu pe verificare la HMRC.
- Pentru Wenzels, site-ul propriu nu a fost verificat.
- AES Barry (non-trading) n-ar fi trebuit să fie în eșantion; de exclus SIC 74990 la eșantionul final.
- Endole livrează datele „as is” (Terms 8.1) și interzice automatizarea (Terms 2.5), deci rezultatele sunt valabile doar pentru verificare manuală.

## 6. Concluzie

Endole găsește TVA pentru **aproximativ 43%** din firme (IC 95%: 27–61%), iar **fiecare număr afișat s-a dovedit valid și al firmei corecte**. Este deci o sursă **precisă, dar cu acoperire limitată**: ratează cel puțin 8 din 30 de firme care aproape sigur au TVA. Costul e de ~2 minute pe firmă fără căutarea în grup, care nu a adus niciun rezultat util. Pentru firmele fără TVA pe Endole e nevoie de o a doua sursă (de exemplu site-ul propriu al firmei).
