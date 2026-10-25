# Rezumat 5: Common Crawl, Pasul 1 („pornind de la firmă”)

**Etapă:** Step 5 – Common Crawl, Pasul 1
**Crawl folosit:** `CC-MAIN-2026-39`
**Fișiere:** `data/results/cc_pas1_domenii_v1.csv`, `data/results/cc_pas1_v3_laine.csv`, `data/results/cc_pas1_v3_toate.csv`, `data/results/cc_pas1_v3_retry.csv`

## 1. Întrebarea

Dacă știu site-ul unei firme, găsesc numărul ei de TVA în arhiva Common Crawl, fără să vizitez eu site-ul?

## 2. Eșantionul și de ce a fost ales

- **12 firme** din eșantionul aleatoriu de 30 din grupul 4 (Rezumat 4): cele 13 cu TVA confirmat de HMRC, minus Mohari, care nu are site.
- Site-ul fiecărei firme a fost luat din Endole.
- **Scop: test al metodei, nu măsurarea acoperirii.** Știam dinainte numărul corect pentru fiecare firmă, deci puteam verifica exact dacă metoda îl găsește. Firmele au fost selectate tocmai pentru că aveau TVA pe Endole, deci eșantionul **nu e reprezentativ** pentru acoperirea pe toată populația.

## 3. Metoda

Pentru fiecare firmă:
1. Interogare la indexul Common Crawl pentru domeniu (`matchType=domain`, include `www.` și alte subdomenii).
2. Păstrarea paginilor HTML și PDF cu status 200; ordonare după probabilitatea de a conține TVA: Terms/Conditions/Contact/Legal → Privacy/Cookie → Policy → restul, la egalitate PDF-urile înaintea HTML-ului.
3. Descărcarea doar a înregistrării paginii din arhivă (cerere `Range`), maximum 30 de pagini per domeniu; decodare cu `warcio`, extragerea textului din PDF cu `pypdf`.
4. Regex: cuvântul „VAT” urmat (în max. 40 de caractere) de 9 cifre, cu sau fără „GB” și spații.
5. Filtru cu suma de control (mod 97), testat pe cele 13 numere confirmate de HMRC: 13/13 acceptate; un număr inventat (`123456789`) a fost respins.
6. Comparare cu numărul confirmat de HMRC; verificarea prezenței numărului Companies House în contextul din jurul TVA-ului.

**Verificare de mână (ground truth):** pentru firmele la care Common Crawl nu a găsit numărul, am căutat „VAT” pe site-ul live (subsol, Contact, Terms, Privacy, Policies).

## 4. Evoluția codului (trail)

| Versiune | TVA găsit | Problemă descoperită și reparată |
|---|---|---|
| v1 | 1/12 | Erorile serverului (504) erau tratate ca „domeniu absent”; interogarea `domeniu/*` nu prindea `www.`; conținutul paginii nu era decodat corect |
| v2 | 1/12 | Reparat: `matchType=domain`, `warcio`, erori separate de absențe. **BP3: 0 → 228 de pagini.** Rămânea: PDF-urile erau ignorate |
| v3 | **2/12** | Reparat: citire PDF + prioritizare pe niveluri. **Laine: găsit la pagina nr. 0** (PDF Terms & Conditions); în v2 citise 21 de pagini fără rezultat. Cauza: 73 de PDF-uri cu „policy” în nume ocupau primele 30 de locuri |

## 5. Rezultate (v3 + reîncercare, 0 erori de server rămase)

| Indicator | Valoare |
|---|---|
| Domenii prezente în crawl | **10/12** (Haulfryn și Stratford lipsesc) |
| Domenii cu prea puține pagini (1–2) | 2/12 (ABQ: 2, ESL: 1) |
| **TVA corect găsit** | **2/12 (16,7%)**: Laine (PDF), Rope & Sling (Contact) |
| Numere greșite găsite (fals-pozitive) | **0** (niciun alt număr valid după checksum pe cele 172 de pagini citite) |
| Poziția paginii cu TVA în lista ordonată | 0 la ambele (prima pagină citită) |
| Numărul Companies House lângă TVA | **2/2** |
| Timp | ~10 min pentru 12 firme (~50 s/firmă), dominat de erorile 504 ale serverului de index |

Diagnostic pe firme:

| Firmă | Pagini în index | Rezultat CC | TVA pe site-ul live (verificat de mână) | Concluzie |
|---|---|---|---|---|
| Laine Theatre Arts | 94 (73 PDF) | ✅ găsit (PDF) | ✅ da, PDF Terms & Conditions, pct. 1.4 | Metoda funcționează |
| Rope & Sling | 174 (6 PDF) | ✅ găsit (Contact) | ✅ da, pagina Contact | Metoda funcționează |
| Red Construction | 92 | fără „VAT” | ❌ nu | Firma nu publică |
| Encirc | 113 | fără „VAT” | ❌ nu (doar mențiuni generale în termeni) | Firma nu publică |
| BP3 Global | 229 (1 PDF) | fără „VAT” | ❌ nu | Firma nu publică |
| Jera Nex | 17 (citite toate) | fără „VAT” | ❌ nu (doar mențiuni generale în Terms) | Firma nu publică |
| Wahed Invest | 858 | „VAT” fără număr | ❌ nu (site global; „VAT” se referă la UAE) | Firma nu publică; site multinațional |
| Greenspruce GP | 865 (invesco.com) | fără „VAT” | neverificat | Site de grup, nu al firmei |
| ABQ Investment | 2 | fără „VAT” | neverificat | Acoperire CC insuficientă |
| Elizabeth School | 1 | fără „VAT” | neverificat | Acoperire CC insuficientă |
| Haulfryn Group | 0 | lipsă | neverificat | Domeniu absent din crawl |
| Stratford Retail | 0 | lipsă | neverificat | Domeniu absent din crawl |

## 6. Ce rezultă

1. **Când numărul e publicat pe site și pagina e în crawl, metoda îl găsește: 2/2, la prima pagină citită, fără fals-pozitive.** Pe cele 7 site-uri verificate de mână, Common Crawl nu a ratat niciun număr publicat.
2. **Limita principală nu e unealta, ci firmele: 5 din 7 site-uri verificate nu-și publică numărul de TVA**, inclusiv firme mari (Encirc: £567M cifră de afaceri; Red: £170M). Endole a avut aceste numere din altă sursă decât site-ul firmei.
3. **A doua limită e acoperirea Common Crawl:** 2/12 domenii lipsesc din crawl, iar alte 2 au doar 1–2 pagini. PDF-ul cu TVA-ul Laine apare în `CC-MAIN-2026-39`, dar **nu și în cele 3 crawl-uri anterioare** (`2026-34`, `2026-30`, `2026-25`), deși e urcat în iunie 2026. La scară trebuie combinate mai multe crawl-uri.
4. **Documentele contează:** la Laine, numărul era **doar într-un PDF**. O căutare doar în HTML l-ar fi ratat (exact ce s-a întâmplat în v1 și v2).
5. **Atribuirea:** în ambele cazuri găsite, numărul Companies House apare chiar lângă TVA („Company Reg No: 04084819 Company VAT No: 811037280”; „registered number 1180133 and VAT Reg. No. 211105734”). Dacă tiparul se confirmă pe mai multe cazuri, el permite atribuirea sigură a unui TVA găsit pe orice pagină.
6. **Probleme de atribuire observate:** site-uri de grup (Greenspruce → invesco.com), site-uri multinaționale (Wahed: „VAT” pentru UAE), mărci diferite de numele firmei (observate în Rezumat 4).
7. **Cuvântul „VAT” singur nu e un semnal:** apare des în termeni („prices exclusive of VAT”) fără niciun număr. Regex-ul trebuie să ceară cuvântul urmat de număr.

## 7. Limitări

- **Eșantion mic și părtinitor:** 12 firme, toate cu TVA cunoscut din Endole. Rezultatul testează metoda, nu acoperirea pe populație.
- **Domeniile au fost luate din Endole.** La scară, găsirea domeniului pornind de la firmă e o problemă separată, nerezolvată aici.
- **Un singur crawl** (`CC-MAIN-2026-39`) în rularea principală.
- **Maximum 30 de pagini per domeniu.** La Wahed (858) și Invesco (865) s-a citit doar o mică parte, deși ordonată după prioritate.
- **5 firme neverificate de mână** (Greenspruce, ABQ, ESL, Haulfryn, Stratford).
- **Serverul de index Common Crawl dă des erori 504/502**, ceea ce a cerut reîncercări. La scară, interogările pe index ar trebui înlocuite cu indexul în format columnar sau cu procesare direct pe AWS (de verificat pentru Part 3).

## 8. Pasul următor

**Pasul 2, „pornind de la număr”:** extragerea oricărui număr de TVA din pagini oarecare din Common Crawl (fișiere WET), atribuirea prin HMRC (nume, cod poștal) și prin numărul Companies House din context. Testează dacă numerele firmelor care **nu** își publică TVA-ul pe site apar pe alte site-uri.
