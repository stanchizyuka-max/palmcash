# Palm Cash Internal Communication System

## Overview

Palm Cash has a comprehensive internal communication system that enables system administrators, managers, and loan officers to communicate efficiently. The system includes **direct messaging**, **threaded conversations**, and **automated notifications**.

---

## Communication Architecture

### 1. **Direct Messaging System**
One-to-one communication between staff members with full message history.

**Features:**
- Send messages to any staff member (Admin, Manager, Loan Officer)
- Link messages to specific loans for context
- Mark messages as read/unread
- Reply to messages
- View sent and received messages separately

**Access:** Only staff members (Admin, Manager, Loan Officer) can use direct messaging

**URL Routes:**
```
/messages/inbox/          - View received messages
/messages/sent/           - View sent messages
/messages/compose/        - Compose new message
/messages/<id>/           - View message details
/messages/<id>/reply/     - Reply to message
```

---

### 2. **Threaded Conversations**
Group conversations with multiple participants for collaborative discussions.

**Features:**
- Create threads with multiple participants
- Link threads to specific loans
- All participants can see full conversation history
- Track who has read each message
- Real-time participant notifications

**Access:** Only staff members can participate in threads

**URL Routes:**
```
/messages/threads/        - View all threads
/messages/threads/<id>/   - View thread details and add messages
```

---

### 3. **Notification System**
Automated notifications for important system events.

**Features:**
- In-app notifications
- Email notifications
- SMS notifications (configurable)
- Notification templates for different event types
- Read/unread tracking
- Scheduled delivery

**Notification Types:**
- Loan Approved
- Loan Rejected
- Payment Due
- Payment Overdue
- Payment Received
- Payment Rejected
- Loan Disbursed
- Document Required
- Document Uploaded
- Document Approved
- Document Rejected

**URL Routes:**
```
/notifications/           - View all notifications
/notifications/<id>/      - View notification details
/notifications/<id>/read/ - Mark as read
/notifications/mark-all-read/ - Mark all as read
/notifications/templates/ - Manage templates (Admin only)
```

---

## Communication Hierarchy

### System Administrator → Manager
**Use Case:** System-wide announcements, policy updates, system maintenance notices

**How to Send:**
1. Go to `/messages/compose/`
2. Select Manager as recipient
3. Write subject and message
4. Send

**Automatic Notifications:**
- Manager receives in-app notification
- Email notification sent to manager's email
- Notification appears in dashboard

---

### Manager → Loan Officers
**Use Case:** Loan approvals, performance feedback, client assignments, policy reminders

**How to Send:**
1. Go to `/messages/compose/`
2. Select Loan Officer as recipient
3. Optionally link to a specific loan for context
4. Send

**Automatic Notifications:**
- Loan Officer receives in-app notification
- Email notification sent
- Notification appea

missionsk user perec. Ch
4templatescation  notifi3. Reviewtor
ministram Adteontact Sys Ce
2. this guid. Checkcation:
1 communinalterues with in iss
For# Support

#ts

---
ple recipienng to multisagik mes- [ ] Bulresponses
on mmes for colatge tempessa [ ] Mges
-messae hive/delet
- [ ] ArcencryptionMessage - [ ] ration
nteg ieo call] Voice/vidojis
- [ em reactions/age
- [ ] Messmestampsith tipts wcei] Read reng
- [ heduli] Message scnts
- [ tachme] Message at- [ lity
onarch functiMessage sea
- [ ] ents
emure Enhancut## F
---

fresh page
amp
3. Remestticreation ck message 
2. Cheticipantr is a par. Verify usesages
1eswing mshoead not ### Thr

 error logs
3. Reviewationil configur2. Check ema is active
on templatetificati noerify1. Vg
ins not sendionicatotif
### Nsettings
n catioeck notifitive
3. Chacs and is stxipient e recierifyicer)
2. V or Loan Offger,Admin, Manaust be e (mser roleck u. Ching
1not appearsages 
### Mesg
shootinleoub
## Trad

---
as reMark all l-read/` - alions/mark-icat /notif `POST
-rk as read/read/` - Macations/<id> /notifin
- `POSTtiotificano/` - View ations/<id>fic- `GET /notins
ationotific` - List ns/tio /notifica
- `GETions# Notificat

##to threaddd message ` - As/<id>/ges/thread/messa- `POST read
w th- Vieeads/<id>/` ages/thr /messGETreads
- `- List thhreads/` /messages/tds
- `GET 

### Threareply` - Send eply/id>/r/<ssagesme /- `POSTReply form
` - /reply/ssages/<id> /mesage
- `GETesew md>/` - Vimessages/<i `GET /message
-` - Send /compose/ssagesST /meform
- `POompose ose/` - Ces/comp/messag
- `GET gessent messant/` - List /seET /messagessages
- `Geived messt recLi- inbox/` T /messages/
- `GEgesMessaints

### Endpo## API ---

tional)

 Payment, opreignKey toyment (Fo
- paonal) optiey to Loan,nKig- loan (Fored)
TimeFiel (Date read_atField)
-me_at (DateTiveredliField)
- deTimet (Date)
- sent_aTimeFieldDateuled_at (
- schedled, read)failivered, g, sent, dedinen pCharField:
- status (n_app) i email, sms,d:(CharFielannel  ch
-Field)age (Textld)
- messrFieChaubject (- snTemplate)
ficatiootiKey to NreignFomplate ()
- teey to User(ForeignKcipient 
- reon Model:**ficati**Notield)

(DateTimeFieated_at r)
- cr to UseeldManyFianyToad_by (Md)
- reTextFielr)
- body (Key to UseForeignr (d)
- sendeMessageThrea to gnKey(Forei thread 
-Model:**ssage **ThreadMe

teTimeField)_at (Dadated upield)
-meFd_at (DateTi
- create to User)nKeyy (Foreigted_b
- creaptional), oey to LoanoreignK)
- loan (Fserld to UnyToManyFieMas (panttici par
-CharField)ubject (del:**
- sThread MoMessage

**eTimeField)d_at (Dat)
- createeTimeFieldad_at (DatField)
- reead (Booleans_ronal)
- ian, optiey to LognK(Foreild)
- loan ody (TextFie- bCharField)
 subject ()
- UserignKey tot (Foreipienser)
- recto UeignKey (For
- sender odel:**
**Message Me Models
bas## Dataails

#cal Detechni# T

---

#ofessionaln prommunicatio. Keep cussions
4sc dirative caselaboeads for colUse threded
3.  necation whenor clarifiAsk f
2. tlyssages prompespond to me1. Rfficers
Loan O
### For y
larlions reguk notificat
4. Checscussions diteams for  threadtext
3. Useon loans for cssages to meLinkicers
2.  Off Loanack toly feedbrovide times
1. PManagerr ### Fo

 conciseand clear mplatestetion notifica
4. Keep specific caseng sscussi diloans whenges to Link messars
3. tteal maenticonfide/ensitiv for sesirect messag Use dncements
2.de annouystem-wifor ss se threadors
1. UstratFor Adminices

### t Practi-

## Bes-- link

ions**l notificat**View alon
- pti** oall as read
- **Mark wn preview)(dropdotions** ficatint noe)
- **Rece badg** (redad countUnreshows:
- **bar igation  top navn thell ification beThe notiell

ation B Notific-

##
--es
ssagal me internend/receiveannot s Cocuments)
- payments, dn status,n (loans** sectio*Notificatiod
- *hboarower Das## Borret

#ations widgnotificecent ssage
- Re meoscompto uick link ator
- Qicssages** indad Men
- **Unre* sectioview*ents for Reending Docum **P
-shboard Officer Da
### Loanidget
ions w notificatecent
- Re messageosmpk link to co
- Quicatordics** inread Message
- **Un** countuments*Pending Docd
- *hboarer Dasag
### Manation
rd Integrhboa# Das--

#
-
```
ferencefor reavailable history sation onver6. Full cguidance
eply with ger can rion
5. Manaotificatr receives n4. Managen
ecific loaLinks to sp"
3. #456n Loan d oeedeidance nGu Subject: "anager
2.to Mds message ener sn Offic. Loa`
1
``ceidanequesting Gu Officer Rle 3: Loan

### Examp``
`readrify in than cladmin c
6. Ain threadtions ques ask taff canations
5. Seive notifictaff rec"
4. All slymmediateeffective ints emeKYC requir"New ment: ouncets annnts
3. Poss participas an Officerand Loaers s all Manag
2. Addge threadessan creates m. Admi
```
1 Changeng Policyouncinnrator Administ Ae 2: SystemplExam### 

rmation
```h confiy witcan replcer an Offiinbox
4. Loars in essage appe
   - Mcationtifi no Emailon
   -atiotific  - In-app nreceives:
 oan Officer  #123
3. L: Loan Link."
   -rsementh disbuceed wit Please proed.pprovhas been a Doe or John loan fThe  - Body: ""
 ed123 Approv"Loan #ject:  - Sub
  cer:an OffiLoage to  sends messanager
2. Mapplicationoan eviews lnager rMa`
1. n
``g a Loa Approvine 1: Manager Examplmples

###orkflow Exa## W

---
.)
etcyments, us, paan stattions (lootificaated ntomeive auec- ✅ Can rg
nal messaginess inter❌ Cannot accwer
- 
### Borro
inistrators Admnagers and from Maesessag miveceions
- ✅ Reotificat nownw 
- ✅ Viegueswith colleae threads  ✅ Creatanagers
-ers and Man Officher Losages to otd mes- ✅ Senfficer
## Loan Oors

#tratisminfrom Ades sagesceive ms
- ✅ Renotificationiew own 
- ✅ Vith staffe threads wreat ✅ Crs
- Manage others andLoan Officer to ges Send messa- ✅Manager
ents

### ouncemem-wide ann ✅ Send systes
-plation tematific Manage notates
- ✅cation templnotifi✅ View all - 
affth any stds wireate threa- ✅ Co anyone
sages td mes
- ✅ Senministratorystem Ads

### Sission & Perm User Roles
##---
once

 all at  orividually read indark as
- Munts unread coowshshboard m
- Da read theo haswhck s traaged messreastatus
- Thread unread/ges show ual messa*
- Individcking*us Traead Stat*R * 4.##us

#ctive statctive/Inasage
- Amese platApp)
- TemSMS, In-mail, el (Eann
- Chfigured: can be conn typeicatioifEach noterences**
tion Pref**Notificat

### 3. r participanpeatus stad rack reace
- Ts in one pl All messageticipants
-ple parulti- Add msubject
ad with eate thre
- Crple:peo multiple ns involvingussiooing discong*
For hreads*age T2. **Mess

### loans.cific bout speunication a track commsy toaking it eaan #123, m with Loages the messy associatells automaticaThi
```
_id=123/?loanosees/compssag/metion:
```
 organizabetterloans for to specific e linked  bges can*
Messa Context*1. **Loan# s

##y Feature

## Kest

---hread lis tember'ach staff ms in epear apadns
- Threicatioifeive notrecs ntparticipa- All ations:**
atic Notific

**Automnouncementan Post 
4.tsticipanarth all pead wihreate new t`
3. Crs/ead/thr `/messages tombers
2. Gome all staff ** withsage Threada **Mes1. Create o Send:**
How t

**hangeses, policy cing updatrain tnts,meounce* System ann Case:*se**U Staff
rator → Allem Administ Syst##
#
---
nd

4. Sentextcon for loaink to nally lOptioer
3.  Loan Officlect anothere/`
2. Seges/compos `/messa*
1. Go tond:*
**How to Seformation
 client inharedals, sases, referrlient ction on c** CollaboraUse Case:er
**fic→ Loan Ofan Officer ## Lo
---

#
oarddashbn officer  irs